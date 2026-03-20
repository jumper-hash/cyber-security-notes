# HackTheBox-Facts-Full-Chain-Penetration-Testing
  ## External-Reconnaissance-and-Web-Entry
    Network Mapping: Nmap scan of `10.129.244.96` leading to `facts.htb` identification
    Endpoint Discovery: Manual and automated fuzzing revealing `/admin/login`
    Platform Analysis: Identification of Camaleon CMS 2.9.0 as the core engine
    
  ## ExploitationandDataExfiltration
    CVE-2025–2304: Exploiting Privilege Escalation within CMS to gain administrative access
    Cloud Leakage: Identification and extraction of AWS S3 Access Keys and Bucket names
    CVE-2024-46987: Leveraging Path Traversal to read `/etc/passwd` and sensitive system files
    
  ## Credential-Cracking-and-SSH-Access
    SSH Key Recovery: Extraction of an encrypted private key for user 'trivia'
    John The Ripper: Brute-force attack on SSH passphrase (Cracked: dragonballz)
    Lateral Movement: Interactive SSH session and retrieval of `user.txt`

# Privilege-Escalation-and-Root-Access
  ## Linux-System-Enumeration
    Sudo Analytics: Identifying `sudo -l` misconfiguration allowing execution of `/usr/bin/facter`
    Technical Troubleshooting: Analyzing Facter's ability to load external ruby/custom facts
    
  ## Root-Acquisition-(Facter Exploit)
    Custom Fact Injection: Creating a malicious ruby exploit in `/tmp` for privilege escalation
    Command: `sudo /usr/bin/facter --custom-dir /tmp/ shell`
    Validation: Shell elevation confirmed via `whoami` (root)
    Final Objective: Full system compromise and retrieval of `/root/root.txt`
