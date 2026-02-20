# Kan-I

This idea for this project came about when I was trying to demonstrate a privilege escalation vulnerability in an EKS cluster. When trying to run `kubectl auth can-i --list` it was always return no permissions with the message: The error message: `Warning: the list may be incomplete: webhook authorizer does not support user rule resolution.`. Yet when running specific `kubectl auth can-i <verb> <resource>` it would correctly repsond yes/no, so I threw this together to get a full list when `kubectl` won't do it for me. 


## Prerequisites

Kan-I uses Python 3 and assumes you have `kubectl` setup and working on your machine with a valid kubeconfig file. By default, it will use the authentiation and namespace from the current-context in your kubeconfig file, but you can pass a bearer token, set a namespace, or check all namespaces to set these yourself.

## Usage

```bash
python3 kan_i.py [OPTIONS]
```

### Options

| Option | Short | Description |
| :--- | :--- | :--- |
| `--help` | `-h` | Show the help message and exit. |
| `--token TOKEN` | | Bearer token for authentication to the API server |
| `--namespace NAMESPACE` | `-n` | List permissions for a specific namespace |
| `--all-namespaces` | `-A` | List permissions across all namespaces |

### Examples

**Check permissions using the current context:**
```bash
python3 kan_i.py
```

**Check permissions in a specific namespace:**
```bash
python3 kan_i.py -n kube-system
```

**Check permissions across all namespaces:**
```bash
python3 kan_i.py -A
```

**Check permissions using a specific bearer token:**
```bash
python3 kan_i.py --token <your-service-account-token>
```

