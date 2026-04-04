# Cisco Network Core & Infrastructure Implementation
  ## Layer 2 Switching & VLAN Segmentation
    VLAN Definition: Created VLAN 10, 20, and 30 for logical network isolation.
    Access Ports: Assigned physical interfaces (7/1, 8/1, 9/1) to respective broadcast domains.
    Trunking: Configured interface 0/1 as 802.1Q Trunk to carry multi-VLAN traffic to the router.
  ## Layer 3 Routing (Router-on-a-Stick)
    Sub-interfaces: Divided Gig0/0/0 into logical units (.10, .20, .30).
    Encapsulation: Enabled 'encapsulation dot1Q' per VLAN for inter-VLAN routing.
    Gateway IPs: Configured virtual interfaces as default gateways (e.g., 192.168.10.1).
  ## DHCP Automation & Addressing
    Pools: Configured 'ip dhcp pool' for automatic subnet addressing (IP, Mask, GW).
    Exclusions: Applied 'ip dhcp excluded-address' to prevent IP conflicts with gateways.
    Verification: Confirmed dynamic IP allocation and connectivity across VLANs.

# Security & Traffic Management (ACL)
  ## Access Control Lists (Standard ACL)
    Policy: Implemented ACL 101 to deny VLAN 30 traffic from reaching VLAN 10 subnet.
    Explicit Permit: Added 'permit any any' to maintain internet/local access for other services.
    Interface Binding: Applied 'ip access-group 101 in' on the sub-interface level.
  ## Operations & CLI Maintenance
    Verification: Used 'show ip int brief' and 'show vlan brief' for real-time status checks.
    Persistence: Executed 'write memory' to save Running-Config to NVRAM.
    Process Control: Used Ctrl+Shift+6 to terminate hung Cisco IOS processes.
