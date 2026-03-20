#DNS-Infrastructure-and-Active-Directory-Resolution
  ##DNS-Role-and-Zone-Configuration
    Authority: AD Integrated Forward Lookup Zone (`lab.local`)
    SRV Records: Automated registration of LDAP, Kerberos, and GC services
    Forwarders: Upstream resolution enabled via `8.8.8.8` and `1.1.1.1`
    Root Hints: Fallback mechanism for top-level domain (TLD) traversal
  ##Client-Side-DNS-Configuration
    Resolver: /etc/resolv.conf points to Windows Server IP (`192.168.100.1`)
    Search Domain: Configured `lab.local` for short-name resolution
    Optimization: Disabled mDNS (avahi) to prioritize unicast DNS queries

#Operational-Verification-(DNS)
  ##Query-Testing
    dig -t SRV `_ldap._tcp.lab.local`: Verified DC service location records
    nslookup `google.com`: Confirmed successful recursion through Forwarders
  ##Log-Auditing
    DNS Manager (Windows): Monitored "Cached Lookups" for external domain resolution
    Journalctl -u sssd: Inspected LDAP search queries during user authentication

#Technical-Nuances-and-"Under-the-Hood" Observations
  ##The-IPv6/AAAA Latency Trap
    Symptom: 5-10 second delay during initial 'apt update' or 'ping' commands.
    Nuance: Linux clients often attempt AAAA (IPv6) lookups before A (IPv4). Since the lab environment lacked IPv6 routing, the resolver waited for a timeout.
    Mitigation: Configured /etc/gai.conf to prioritize IPv4 (precedence `::ffff:0:0/96 100`), eliminating resolution lag.
  ##RRAS-Interface-Role-Polarity
    Symptom: Packets reach the Windows Server but are dropped before egress.
    Nuance: In RRAS NAT, the 'Public' interface MUST have "Enable NAT" checked, while 'Private' interfaces MUST NOT.
    Observation: Swapping roles causes the server to attempt NAT on the internal network, breaking the routing table for the entire subnet.
  ##Kerberos-Case-Sensitivity-(The "REALM" Rule)
    Symptom: 'realm join' fails with "KDC not found" despite successful pings.
    Nuance: Kerberos is strictly case-sensitive. While DNS is case-insensitive (lab.local), the Kerberos Realm MUST be uppercase (`LAB.LOCAL`).
    Verification: Verified /etc/krb5.conf (realms) section for correct casing to ensure ticket-granting service (TGS) compatibility.
  ##SSSD-Cache-Desynchronization
    Symptom: 'id' command returns "no such user" immediately after a successful join.
    Nuance: The System Security Services Daemon (SSSD) may not instantly populate its local cache from the AD LDAP tree.
    Diagnostic: Required 'sss_cache -E' to force an immediate invalidation of the local database and trigger a fresh lookup to the DC.
