# Domain Group Membership and Escalation
  ## Analyzed privilege escalation by adding a user to Domain Admins:
    Added standard domain user to privileged group
    Waited for replication and log generation
    Removed user to simulate "temporary" persistence
  ## Observed events in Security Log:
    4728: Member added to global security group
    4729: Member removed from global security group
    Correlated Subject (Admin) with Member (Target) and Logon ID
  ## Key conclusion:
    Temporary membership in privileged groups is a high-severity indicator of persistence
    Monitoring 4728/4729 is critical for detecting unauthorized administrative changes

# Password Change vs Reset Analysis
  ## Tested two different password modification scenarios:
    User-initiated password change (knowing old password)
    Administrator-forced password reset (reset via ADUC)
  ## Observed log differences:
	4723: Attempt to change password (User action)
    4724: Attempt to reset password (Admin action)
  ## Security Insight:
    Differentiating 4723 vs 4724 helps identify if an account was compromised via admin tools or user-level access
    Mass 4724 events often indicate a malicious takeover or lateral movement attempt

# SPN Manipulation and Kerberoasting Detection
  ## Analyzed SPN modification using setspn.exe:
    Executed: setspn -A fake/service lab\user
    Troubleshot audit gaps (empty fields in event 4738)
    Enabled Directory Service Changes via GPO and SACL on the user object
  ## Observed event correlation:
    4688: Process creation (setspn.exe) with full command line arguments
    4738: User account changed (basic notification)
    5136: Directory Service Object modification (detailed attribute tracking)
    Verified attribute: servicePrincipalName added with value "fake/service"
  ## Key conclusion:
    SPN injection is a prerequisite for Kerberoasting attacks
    Standard auditing (4738) is often insufficient; 5136 provides the necessary attribute-level telemetry

# Kerberos Ticket Lifecycle and Behavior
  ## Tested ticket management using klist:
    Enumerated active tickets (TGT and Service Tickets)
    Purged tickets using klist purge to observe re-authentication
  ## Observed logs on Domain Controller:
    4768: TGT (Ticket Granting Ticket) requested
    4769: Service Ticket requested (following SPN modification)
  ## Security Insight:
    Correlating an SPN change with a subsequent 4769 request for that specific SPN is a high-confidence indicator of Kerberoasting
    Ticket lifecycle monitoring reveals lateral movement patterns

# NTLM vs Kerberos Authentication Behavior
  ## Tested authentication to SMB share using:
    `\192.168.100.1\`share (IP address)
    `\dc.lab.local\share` (DNS name)
  ## Observed differences in Security Log (4624):
    IP -> NTLMv2
    DNS -> Kerberos
    Verified Logon Type = 3 (Network)
    Authentication Package field changed based on the connection method
  ## Key conclusion:
    Kerberos requires SPN and proper hostname resolution
    Using IP forces fallback to NTLM, which is susceptible to relay and pass-the-hash attacks

# Security Token and Privilege Analysis
  ## Analyzed user context using `whoami /all`:
    Inspected SID, Group SIDs, and Privileges
    Compared standard user token vs. Domain Admin token
  ## Observed token limitations:
    Standard user: minimal privileges (e.g., SeChangeNotifyPrivilege)
    Admin user: expanded privilege set and high-integrity SIDs
    Token update required full logoff/logon to apply group membership changes
  ## Key concept:
    Security tokens are immutable once generated during the logon session
    Privilege escalation requires session renewal to reflect new permissions

# Detection Mindset and Correlation
  ## Analyzed suspicious activity chain:
    -Step 1: 4728 (User added to Domain Admins)
    -Step 2: 4624 Type 3 (Network logon from unusual source)
    -Step 3: 4769 (Service ticket request for newly created SPN)
  ## Outcome:
    Recognized that incident detection relies on timeline reconstruction
    Shifted focus from single-event alerts to multi-stage attack correlation
