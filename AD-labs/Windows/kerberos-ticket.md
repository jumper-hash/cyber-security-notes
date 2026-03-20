# Kerberos-ticket-lifecycle-(klist analysis)
  Executed:  klist
  ## Observed:
    TGT (Primary ticket)
    Multiple Service Tickets (CIFS, HOST, LDAP depending on usage)
  ## Compared:
    Standard user vs local admin ticket count
    Admin session had additional service tickets (delegation / service related)

# Ticket-purge-behavior
  Executed:  klist purge
  ## Observed:
    TGT and service tickets removed
    After short delay, system automatically requested new TGT
  ## Conclusion:
    Windows automatically retrieves new TGT when needed
    Ticket lifecycle is dynamic and usage-driven
  ## Important-security-insight:
    If attacker steals TGT -> possible Pass-the-Ticket attack
    Ticket presence = active authentication context

# Kerberos-auditing-events
  ## Identified-relevant-Event-IDs:
  4768 → TGT requested
  4769 → Service ticket requested
  ## Correlated:
    -Account Name
    -Service Name
    -Client Address
  ## Understood:
    Service ticket requests reveal which services user accessed
    Useful for detecting lateral movement or unusual service usage

# Security-mindset-gained
  ## Understood-difference-between:
    Authentication protocol selection
    Logon type context
    Privilege vs group membership
    TGT vs Service Ticket
  ## Observed-how:
    DNS usage affects authentication protocol
    Token generation affects privileges
    Kerberos tickets are service-specific
    Logs can reconstruct authentication timeline
