# HackTheBox WingData Full Chain Penetration Testing
## Exploitation and Shell Stabilizing
	RCE Execution: Launching `cve.py` with a Netcat reverse shell payload directed to port 443.
	Interactive Shell: Upgrading the terminal using Python's pty module:
	`python3 -c 'import pty; pty.spawn("/bin/bash")'`
	Environment Setup: Configuring export TERM=xterm to enable full terminal interactivity and clear screen commands.
	
## Data Exfiltration and Credential Cracking
	System Enumeration: Analysis of the `/opt/wftpserver/Data` directory to locate configuration and user files.
	Sensitive Data Leakage: Extraction of the hashed password for user 'wacky' from wacky.xml and the plaintext salt 'WingFTP' from users.xml.
	Hashcat Orchestration: Performing a dictionary attack on the combined hash and salt string.
	Credential Recovery: Successful recovery of the plaintext password: `!#7Blushing^*Bride5`
	SSH Access: Establishing an interactive SSH session as user 'wacky' and retrieving user.txt.

# Privilege Escalation and Root Access
## Linux System Enumeration
	Sudo Analytics: Identifying a `sudo -l` misconfiguration allowing execution of `restore_backup_clients.py` as root.
	Platform Analysis: Identifying vulnerability to CVE-2025-4517 within the Python tarfile module.
	Technical Troubleshooting: Analyzing the filter="data" parameter which successfully blocked standard path traversal attempts (../../).
	
## Root Acquisition (CVE-2025-4517)
	Symlink and Hardlink Bypass: Crafting a malicious .tar archive using a deep directory structure and hardlinks to bypass extraction filters.
	Command Execution: Triggering the backup restoration script to overwrite `/etc/sudoers` via the symlink "portal".
	Validation: Confirming privilege elevation via` sudo -l` showing NOPASSWD: ALL.
	Final Objective: Achieving full system compromise and retrieving the final flag from `/root/root.txt`.