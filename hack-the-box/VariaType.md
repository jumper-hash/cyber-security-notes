# HackTheBox VariaType Penetration Testing

## External Reconnaissance and Web Entry
    Network Mapping: Nmap scan of `10.129.13.110` leading to `variatype.htb` identification
    Endpoint Discovery: Manual and automated fuzzing revealing `panel.variatype.htb'
## Git Repository Exposure
	`curl -s http://portal.vatiratype.htb/.git/HEAD` revealed that the Git repository was publicly accessible.
	Dumping git revealed old commit changing openly written credentials for the gitbot user account.
	
