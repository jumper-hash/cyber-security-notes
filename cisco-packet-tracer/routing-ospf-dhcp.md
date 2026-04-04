# Cisco Network Infrastructure & Secure Routing Implementation
  ## Layer 2 Switching & VLAN Architecture
    VLAN Segmentation: Defined VLAN 10, 20, and 30 for logical isolation of broadcast domains.
    Port Configuration: Assigned physical interfaces (7/1, 8/1, 9/1) to Access mode and established 802.1Q Trunking on uplink Port 0/1.
    Router-on-a-Stick: Sub-divided Gig0/0/0 into logical units (.10, .20, .30) with dot1Q encapsulation to enable Inter-VLAN routing.
  ## Hardware Scaling & Modular Expansion
    Diagnosis: Resolved 'Invalid input' constraints by identifying L2 hardware limitations vs L3 routing requirements.
    Modular Solution: Deployed 'PT-Empty' chassis with 1CFE expansion modules to facilitate multi-interface L3 connectivity.
    Physical Topology: Linked 3-router backbone using Cross-Over cabling for direct DTE-DTE communication.
  ## Dynamic Routing (OSPF Implementation)
    Area Strategy: Established Multi-Area OSPF hierarchy (Backbone Area 0 and Area 1).
    Adjacency Verification: Confirmed 'FULL' neighbor states using 'show ip ospf neighbor'.
    Route Analysis: Validated OSPF 'O' (Intra) and 'O IA' (Inter-Area) route injection into the routing table.
  ## Network Automation & Addressing (DHCP)
    Service Deployment: Configured 'ip dhcp pool' for automated distribution of IP, Mask, and Gateway parameters.
    Conflict Prevention: Implemented 'ip dhcp excluded-address' to protect infrastructure and gateway IPs.
    Verification: Confirmed successful DORA process and end-to-end connectivity across subnets.
  # Security & Traffic Management (ACL)
    Access Policy: Implemented Standard ACL 101 to enforce traffic isolation (Deny VLAN 30 to VLAN 10).
    Traffic Flow: Applied 'permit any any' to override implicit deny and maintain global network access.
    Interface Binding: Deployed ACL on sub-interface IN direction for proactive packet filtering.
  ## CLI Operations & Maintenance
    System Persistence: Committed Running-Config to NVRAM via 'write memory'.
    Process Control: Utilized 'Ctrl+Shift+6' for command interruption and 'show' commands for real-time state verification.
