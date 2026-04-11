# HackTheBox Garfield Full Chain Penetration Testing

## External Reconnaissance and Service Identification

- **Network Mapping:** Nmap scan of `10.129.26.230` leading to the identification of Active Directory services and SMB.
    
- **SMB Enumeration:** Used `smbmap` with credentials `j.arbuckle : Th1sD4mnC4t!@1978` to discover shared files.
    
- **Data Discovery:** Identified `printerDetect.bat` within a web-shared directory with read permissions, indicating its use in automated system processes or logon scripts.
    

## Active Directory Enumeration

- **User Enumeration (RPC):** Utilized `rpcclient` to map domain users, identifying two high-value targets: `l.wilson` (Standard User) and `l.wilson_adm` (Administrative Account).
    
- **Group Membership:** Verified that both accounts are members of the `Remote Management Users` group, confirming WinRM as a viable lateral movement vector.
    
- **ACL Analysis:** Employed `bloodyAD` to audit Object Security, revealing that `j.arbuckle` possesses write permissions over the `l.wilson` user object.
    

## Exploitation: Logon Script Injection

- **Persistence via ADSI:** Leveraged write permissions to modify the `scriptPath` attribute of the `l.wilson` account, pointing it to a malicious version of `printerDetect.bat`.
    
- **Payload Construction:** `@echo off powershell -nop -w hidden -enc {Base64_Encoded_Reverse_Shell}`
    
- **Execution:** Uploaded the modified `.bat` file via SMB. The payload executed upon the next login of `l.wilson`, granting an interactive shell as `garfield\l.wilson`.
    

## Lateral Movement and Privilege Escalation

- **Credential Escalation (Force Change Password):** Analyzed ACLs of the `l.wilson_adm` object using PowerShell ADSI, identifying the `User-Force-Change-Password` (Extended Right).
    
- **Exploitation:** `$u=[ADSI]"LDAP://CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb"; $u.Invoke("SetPassword", @("Kwakwa5!"));`
    
- **System Access:** Authenticated via WinRM using the newly set credentials for `l.wilson_adm`.
    

## Domain Analysis and Data Exfiltration

- **User Flag Recovery:** Accessed the administrative session and retrieved the contents of `user.txt`.
