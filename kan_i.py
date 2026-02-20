#!/usr/bin/env python3

import argparse
import subprocess
import sys
import concurrent.futures

VERBS = [
    "get", "list", "watch", "create", "update", "patch", "delete",
    "deletecollection", "use", "bind", "escalate", "impersonate"
]

def run_command(cmd):
    """Run a shell command and return its stdout, stderr, and return code."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def base_kubectl_cmd(token=None):
    """Return the base kubectl command, optionally with a token."""
    cmd = ["kubectl"]
    if token:
        cmd.extend(["--token", token])
    return cmd

def check_cluster_access(token):
    """Check if we can access the cluster and get API resources."""
    cmd = base_kubectl_cmd(token) + ["api-resources", "--cached=false", "-o", "name"]
    stdout, stderr, rc = run_command(cmd)
    
    if rc != 0:
        error_msg = stderr if stderr else "Unknown error connecting to cluster."
        if "error: You must be logged in to the server" in error_msg:
            print("Error: Unauthorized. Please check your credentials or token.")
        elif "connection refused" in error_msg.lower() or "no route to host" in error_msg.lower():
            print(f"Error: Cannot connect to server. Details: {error_msg}")
        elif "does not exist" in error_msg.lower() and "kubeconfig" in error_msg.lower():
            print(f"Error: No config file found. Details: {error_msg}")
        else:
            print(f"Error: Cluster access failed.\nDetails: {error_msg}")
        sys.exit(1)
        
    resources = stdout.split('\n')
    return [r for r in resources if r]

def get_current_user(token):
    """Get the current authenticated user."""
    cmd = base_kubectl_cmd(token) + ["auth", "whoami"]
    stdout, _, rc = run_command(cmd)
    if rc == 0 and stdout:
        return stdout
    # Fallback if whoami fails
    return "current"

def get_current_namespace(token):
    """Get the current namespace from the context."""
    cmd = base_kubectl_cmd(token) + ["config", "view", "--minify", "-o", "jsonpath={..namespace}"]
    stdout, _, rc = run_command(cmd)
    if rc == 0 and stdout:
        return stdout
    return "default"

def get_all_namespaces(token):
    """Get a list of all namespaces in the cluster."""
    cmd = base_kubectl_cmd(token) + ["get", "namespaces", "-o", "jsonpath={.items[*].metadata.name}"]
    stdout, stderr, rc = run_command(cmd)
    if rc != 0:
        print(f"Error fetching namespaces: {stderr}")
        sys.exit(1)
    if stdout:
        return stdout.split()
    return []

def check_permission(verb, resource, namespace, token):
    """Check a specific permission and return (resource, verb, result_boolean)."""
    cmd = base_kubectl_cmd(token) + ["auth", "can-i", verb, resource]
    if namespace:
        cmd.extend(["-n", namespace])
    
    stdout, _, _ = run_command(cmd)
    allowed = stdout.lower() == "yes"
    return resource, verb, allowed

def main():
    parser = argparse.ArgumentParser(
        description="Check user's permissions by cycling through verbs and resources."
    )
    parser.add_argument("--token", help="bearer token for authentication to the API server")
    parser.add_argument("-n", "--namespace", help="list permissions for a specific namespace")
    parser.add_argument("-A", "--all-namespaces", action="store_true", help="list permissions across all namespaces")
    
    args = parser.parse_args()

    resources = check_cluster_access(args.token)
    
    user = get_current_user(args.token)

    namespaces_to_check = []
    is_multi_namespace = args.all_namespaces
    if is_multi_namespace:
        namespaces_to_check = get_all_namespaces(args.token)
        print(f"The {user} user has the following permissions across all namespaces:")
    else:
        if args.namespace:
            namespaces_to_check = [args.namespace]
        else:
            namespaces_to_check = [get_current_namespace(args.token)]
        print(f"The {user} user has the following permissions in the {namespaces_to_check[0]} namespace:")

    if is_multi_namespace:
        print(f"{'NAMESPACE':<20} {'RESOURCE':<40} {'VERBS'}")
    else:
        print(f"{'RESOURCE':<40} {'VERBS'}")

    next_check = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for ns in namespaces_to_check:
            ns_results = {res: [] for res in resources}
            
            for res in resources:
                for verb in VERBS:
                    check = executor.submit(check_permission, verb, res, ns, args.token)
                    next_check[check] = (ns, res, verb)
            
            for check in concurrent.futures.as_completed(next_check):
                ns, res, verb = next_check[check]
                _, _, is_allowed = check.result()
                if is_allowed:
                    ns_results[res].append(verb)
            
            for res in sorted(ns_results.keys()):
                allowed_verbs = sorted(ns_results[res])
                if allowed_verbs:
                    verbs_str = f"[{', '.join(allowed_verbs)}]"
                    if is_multi_namespace:
                        print(f"{ns:<20} {res:<40} {verbs_str}")
                    else:
                        print(f"{res:<40} {verbs_str}")
            
            next_check.clear()

if __name__ == "__main__":
    main()
