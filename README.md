# Kan-i

Kan-i is a Python-based command-line tool designed to programmatically check your Kubernetes capabilities. It iterates through all available API resources and standard Kubernetes verbs to give you a comprehensive matrix of exactly what permissions you have. 

It acts as a robust alternative to `kubectl auth can-i --list`, which can sometimes fail or be restricted depending on your cluster's Role-Based Access Control (RBAC) settings. Kan-i tackles this by making individual `kubectl auth can-i <verb> <resource>` requests concurrently.

## Features

- **Comprehensive Permission Matrix**: Cycles through all accessible Kubernetes resources and standard verbs (get, list, watch, create, update, patch, delete, use, bind, escalate, etc.).
- **Namespace Scope**: Run checks within your current namespace, a specific namespace, or across all namespaces in the cluster.
- **Concurrent Execution**: Uses a thread pool to rapidly execute the necessary `kubectl` commands.
- **Token Authentication**: Supports passing a specific API bearer token for authentication.
- **Clear Output**: Formats results into an easy-to-read table.
- **Graceful Error Handling**: Provides clear error messages for cluster connectivity drops, authorization issues, or a missing kubeconfig.

## Prerequisites

- Python 3.x
- `kubectl` installed and configured in your `$PATH`
- A valid kubeconfig or an authentication token

## Usage

```bash
python3 kan_i.py [OPTIONS]
```

### Options

| Option | Short | Description |
| :--- | :--- | :--- |
| `--help` | `-h` | Show the help message and exit. |
| `--token TOKEN` | | Bearer token for authentication to the Kubernetes API server. By default, it uses your current kubeconfig context. |
| `--namespace NAMESPACE` | `-n` | The specific namespace scope to check permissions against. |
| `--all-namespaces` | `-A` | List permissions across all available namespaces in the cluster. |

### Examples

**Check permissions in the current namespace:**
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

## How It Works

1. **Cluster Access Check**: Validates your connection or token by retrieving the available API resources via `kubectl api-resources`.
2. **Context Discovery**: Determines your current authenticated user and the target namespace(s).
3. **Concurrent Processing**: Spins up multiple threads to query `kubectl auth can-i <verb> <resource>` for every permutation of verbs and resources.
4. **Result Aggregation**: Filters out the "no" responses and tabulates the allowed actions, sorting them alphabetically for readability.
