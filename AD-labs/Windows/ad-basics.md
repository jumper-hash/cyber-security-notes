#Lab-Objective
  ##Goal-of-the-lab
    Build a local Active Directory environment
    Understand how core Windows infrastructure components work together
    Focus on Active Directory fundamentals
    Focus on DNS role in AD
    Focus on Network configuration and troubleshooting
    Focus on Firewall rules and service communication

#Environment
  ##Infrastructure-details
    Hypervisor: Oracle VirtualBox
    Network type: Internal Network
    Network name: intnet1
    ##Virtual-Machines
    Windows Server (Domain Controller + DNS)
    Windows 11 (Domain-joined client)

#Network-Configuration
  ##Windows-Server-(Domain Controller)
    IP Address: `192.168.100.1/24`
    DNS Server: `192.168.100.1`
    Default Gateway: (not configured)
    Network Adapters: 1 (Internal Network only)
  ##Windows-11-Client
    IP Address: `192.168.100.20/24`
    DNS Server: `192.168.100.1`
    Default Gateway: (not configured)
    Network Adapters: 1 (Internal Network only)
  ##Important-note
    The client uses only the Domain Controller as DNS
    Public DNS servers (e.g. `8.8.8.8`) were intentionally avoided to ensure proper Active Directory functionality

#Active-Directory
  ##Setup-and-Management
    Installed Active Directory Domain Services (AD DS)
    Promoted the server to a Domain Controller
    Created a new domain (e.g. `lab.local`)
    Used Active Directory Users and Computers (ADUC) to browse default OUs
    Used ADUC to create custom Organizational Units
    Used ADUC to create and manage test user accounts

#DNS-Configuration
  ##Configuration-and-Verification
    DNS installed together with AD DS
    Verified Forward Lookup Zone for the domain
    Verified A and SRV records required by AD
    Enabled DNS debug logging to observe client DNS queries
  ##DNS-Testing
    `ping lab.local`
    `nslookup lab.local`
