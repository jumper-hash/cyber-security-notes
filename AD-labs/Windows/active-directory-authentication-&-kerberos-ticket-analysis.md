# NTLM vs Kerberos authentication behavior
  ## Tested authentication to SMB share using:
    `\\192.168.100.1\share` (IP address)
    `\\dc.lab.local\share` (DNS name)
  ## Observed authentication differences in Security Event Log(4624):
    IP -> NTLMv2
    DNS -> Kerberos
    Verified in event details:
    Logon Type = 3 (Network logon)
    Authentication Package changed depending on connection method
  ## Key conclusion:
    Kerberos requires SPN and hostname resolution
    Using IP forces fallback to NTLM
    This behavior is important in NTLM relay and pass-the-hash attack scenarios

# Logon Type analysis Analyzed Event ID 4624
  ## Identified different logon types:
    2 -> Interactive (local logon)
    3 -> Network (SMB access)
    10 -> RemoteInteractive (RDP – theoretical analysis)
  ## Examined:
    Source Network Address
    Workstation Name
    Logon GUID
    authentication Package
  ## Understood how logon type helps detect lateral movement patterns

# User privileges analysis (`whoami /all`)
  ## Analyzed:
    User SID
    Group memberships
    Privilege list
  ## Observed:
    Standard user had only SeChangeNotifyPrivilege enabled
  ## Understood:
    Enabled privilege ≠ administrative rights
    Many privileges appear but are disabled by default
    SeChangeNotifyPrivilege allows directory traversal but not data access

# Local Administrator privilege comparison
  ## Added user to local Administrators group
    Re-ran:  whoami /all
  ## Compared:
    Additional group memberships
    Token differences
    Privilege changes
  ## Observed:
    Increased number of privileges
    Not all privileges automatically enabled
    Session refresh (logoff/logon) required for full token update
  ## Key concept:
    Security token is generated at logon
    Privilege changes require new authentication context
