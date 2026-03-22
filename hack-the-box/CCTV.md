# HackTheBox CCTV Full Chain Penetration Testing
## External Reconnaissance and Web Entry
    Network Mapping: Nmap scan of `10.129.8.221` leading to cctv.htb identification
    Platform Analysis: Identification of ZoneMinder v1.37.63 via default administrative credentials (admin/admin)
    
## Exploitation and Data Exfiltration
    CVE-2024–51482: Exploiting a Multi-Stage Vulnerability within ZoneMinder for initial system interaction
    SQL Injection: Utilizing SQLmap for automated database exploitation and user/password hash extraction
    
## Credential Cracking and SSH Access
    John The Ripper: Brute-force attack on extracted hashes (Cracked: opensesame for user 'mark')
    SSH Access: Established interactive session as user 'mark' via remote authentication
    
## Internal Enumeration and Pivoting
    Port Forwarding: Identification of internal-only service (motionEye) on port 8765
    SSH Tunneling: Constructing a local port forward to bypass firewall and access internal web UI
    Credential Recovery: Manual extraction of administrative hash from `/etc/motioneye/motion.conf`

# Privilege Escalation and Root Access
## Privilege Escalation CVE 2025-60787 (motionEye)
    Command Injection: Exploiting the 'Image File Name' parameter within the motionEye dashboard
    Sudoers Manipulation: Injecting a malicious payload to modify system permissions
    Command: `$(echo "mark ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers).%Y-%m-%d`
    
## Root Acquisition and System Compromise
    Sudo Analytics: Leveraging NOPASSWD misconfiguration to execute commands with root privileges
    Validation: Confirmation of administrative access via sudo -l and whoami (root)
    Final Objectives: Full system takeover and retrieval of `/home/sa_mark/user.txt` and `/root/root.txt`
