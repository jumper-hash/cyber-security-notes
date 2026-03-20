#Configuration-Changes
 ##Audit-Policy-Setup
	  Enabled success and failure auditing for logon events
	  Enabled auditing for object access within Group Policy
 ##User-Interface-Restrictions
	  Implemented restrictions for the Ctrl+Alt+Del options menu
	  Limited end-user access to critical system functions

#Applied-Settings
 ##GPO-Propagation
	  Configured the relevant GPOs
	  Ensured settings were propagated across the domain
 ##Ctrl+Alt+Del Options
	  Removed Task Manager: Enabled -> prevent users from killing system processes
	  Removed Change Password: Enabled -> enforce password management through official channels
	  Removed Logoff / Lock: Enabled based on specific workstation security requirements

#Log-Analysis
 ##Security-Event-Monitoring
	  Reviewed security logs for logon and logoff attempts
	  Analyzed Event ID 4624 -> Successful Logon
	  Analyzed Event ID 4625 -> Failed Logon
	  Monitored object access events
 ##Policy-Enforcement-Tracking
	  Monitored for unauthorized attempts to access restricted UI elements
	  Checked for attempts to bypass enforced group policies

#Hardening-Success
 ##Attack-Surface-Reduction
	  Confirmed GPO and registry-level changes successfully reduced the attack surface
	  Prevented users from interfering with system-level operations via Secure Attention Sequence (SAS)

#Findings
 ##Visibility-and-Safety
	  Confirmed auditing is working properly to ensure visibility into user and object access
	  Verified that specific system changes drastically increase the safety level on machines
