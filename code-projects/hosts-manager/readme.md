# hosts-manager

hosts-manager is a Python utility script designed to maintain the /etc/hosts file, specifically tailored for penetration testing environments like Hack The Box (HTB).

It automates the process of adding new target entries and editing existing ones, ensuring that the local DNS resolution is always up to date with the latest target IP and domain.

## Features

	-Automated IP Formatting: Automatically prefixes short IP inputs (e.g., 10.15) with the HTB standard 10.129.0.0/16 subnet.
	-Domain Auto-Completion: Automatically appends the .htb suffix to domain names if it is missing.
	-Smart Indexing: Locates the last active entry after a specific separator (`#=====`) to keep system entries and target entries organized.
	-Legacy Preservation: When adding a new entry, it automatically comments out the previous entry to maintain a history of targets.
	-Validation Engine: Uses the ipaddress library to ensure all inputs are syntactically correct before modifying system files.
	-Safe File Handling: Includes permission error handling to alert users when root privileges (sudo) are required for writing to /etc/hosts.
## How It Works

	The script operates by parsing the /etc/hosts file into a list of strings. It uses a custom indexing function (get_last_index) that scans for a defined separator and then finds the last non-empty line following it.
	Depending on the flags provided (-n for new or -e for edit), the script either performs an in-place string replacement or an insertion. After modifying the internal list, it calls a centralized save function to commit the changes back to the disk.
## Configuration

	-Path Customization: The default target is set to /etc/hosts. This can be modified by changing the path variable at the top of the script for testing purposes.
	-Separator Control: The script looks for #===== to delineate the target section. You can customize this string by editing the separator variable.
	-Default Subnet: The 10.129. prefix used for short IP inputs is hardcoded in the check_ip function and can be adjusted to match other lab environments.
