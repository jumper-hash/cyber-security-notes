# Linux-Router-Infrastructure-and-Network-Analysis
  ## Network-Services-and-Configuration
    Routing: IP Forwarding enabled via sysctl (`net.ipv4.ip_forward=1`)
    DHCP Server: `isc-dhcp-server` configured for subnet `192.168.10.0/24`
    DNS Server: `BIND9` active for local name resolution (`lab.local`)
    NAT: iptables POSTROUTING MASQUERADE on WAN interface (enp0s3)

# Wireshark-and-Traffic-Inspection
  ## DHCP-DORA-Sequence-(UDP 67/68)
    Discover: Client broadcast to identify available DHCP servers
    Offer: Server proposal of IP configuration (`192.168.10.120`)
    Request: Client formal request for the offered IP address
    Acknowledgment (ACK): Server confirmation and lease finalization
  ## DNSandNATFlowVerification
    DNS Queries: Standard A-record lookups captured on UDP port 53
    NAT Verification: Observed source IP translation from LAN to WAN IP
    Peer Address: Identification of remote socket endpoints during active sessions

# Operational-Commands-and-Diagnostics
  ## Network-Socket-Analysis
    `ss -tulnp`: Core command to identify listening ports and PIDs
    Ports verified: 22 (SSH), 53 (DNS), 67 (DHCP)
  ## System-Monitoring
    `systemctl status [service]`: Verification of daemon operational states
    `journalctl -u [service] -f`: Real-time log auditing for troubleshooting
  ## Packet-Capturing
    `tcpdump -i [interface]`: CLI-based packet sniffing for rapid verification
