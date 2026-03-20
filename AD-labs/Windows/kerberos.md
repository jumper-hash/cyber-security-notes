# Kerberos Authentication Analysis
  ## What is Kerberos
    Kerberos is a network authentication protocol designed to provide secure user authentication across open networks
    Uses tickets to allow nodes to prove their identity in a secure manner

# How Kerberos Works
  ## Ticket Issuance Process
    Issues a ticket-granting ticket (TGT) when a user logs in
    TGT is used to request service tickets for specific resources
    Ensures that passwords are never sent over the network
    Behavior can be observed during login sessions

# Importance in Active Directory
  ## Role and Security
    Default authentication protocol in Active Directory
    Allows users to securely log in and access resources
    Ensures credentials protection across the domain

# My Analysis
  ## Security Log Monitoring
    Monitored Kerberos ticket events in security logs
    Verified TGTs and service tickets were issued correctly
    Ensured each authentication step was logged as expected
  ## Key Event IDs
    Event ID 4768 -> TGT Request
    Event ID 4769 -> Service Ticket Request
  ## Client side Verification
    Used klist command on workstation to verify cached tickets
    Confirmed tickets were used for accessing network shares
    Verified tickets use encryption: AES256-CTS-HMAC-SHA1-96
