# dumper
dumper is a lightweight Python automation script designed for rapid Linux system enumeration. It executes a series of diagnostic commands, gathers system information, and provides options to either save the output locally or exfiltrate it to a remote listener.
## Features
- Customizable Command Sets: Easily categorize and modify commands directly within the script:
    - commands: Standard system information gathering.
    - finds: Focused reconnaissance using the find utility.
    - sudos: Privileged command execution.
    - Intelligent Reporting: Automatically performs `ls -l` on files discovered during search operations for immediate permission analysis.
- Flexible Output:
    - Local: Save results directly to a file using the `-d` flag.
    - Remote: Stream output to a remote listener (e.g., `nc`) using the `-i` (IP) and `-l` (port) flags.
- Sudo Support: Secure handling of sudo privileges with password input functionality.
  
## How It Works
`python3 dumper.py [-h] [-i IP] [-p PASSWORD] [-d DESTINATION] [-l PORT]`
