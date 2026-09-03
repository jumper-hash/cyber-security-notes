# Cisco High-Availability L3 Enterprise Network Implementation
```
                               +-------------------+
                               |      Router      |
                               +---------+---------+
                                 /               \
                       Gig0/0   /                 \   Gig0/1
                    10.0.1.1/30/                   \10.0.2.1/30
                              /                     \
                             v                       v
                   +------------------+     +------------------+
                   |  CORE01 (SW1)    |<===>|  CORE02 (SW2)    |
                   | 3560 L3 (Active) | L2  | 3560 L3 (Standby)|
                   +--------+---------+Trunk+--------+---------+
                      /     |     \            /     |     \
                     /      |      \          /      |      \
                    /       |       \        /       |       \
                   v        v        v      v        v        v

                   
                +--------------+  +--------------+  +--------------+
                |   OFFICE1    |  |   OFFICE2    |  |  SERVERS_SW  |
                | 2960 L2 Sw.  |  | 2960 L2 Sw.  |  | 2960 L2 Sw.  |
                +-------+------+  +-------+------+  +-------+------+
                        |                 |                 |
         +------+------+   +------+------+   +------+------+------+
         |             |   |             |   |             |      |
         v             v   v             v   v             v      v
      [PCs A]       [PCs B]             [HTTP]        [DC]  [DHCP]
      VLAN 10       VLAN 20             VLAN 50      VLAN 40
```



## Topology and Core Architecture
- Core Redundancy: Deployed L3 switches (SW1 and SW2) executing HSRP across all SVIs (VLAN 10, 20, 40, 50).
- Priority Control: SW1 configured as Active gateway (Priority 110) with preemption, SW2 as Standby (Priority 100).
- L3 Uplinks: Established point-to-point routed links (`no switchport`) using `/30` subnets to edge Router0 (`10.0.1.0/30` and `10.0.2.0/30`).

## Routing Strategy and Edge Configuration
- Static Routing: SW1 and SW2 route default outbound traffic (`0.0.0.0/0`) towards Router0 interfaces.
- Floating Static Route: Router0 configured with primary route to SW1 (`10.0.1.2`) and backup route to SW2 (`10.0.2.2`) with AD 20.
- Return Path Redundancy: Prevents blackholing return traffic if SW1 fails.

```text
! Router0 Static Routes Configuration
ip route 192.168.0.0 255.255.0.0 10.0.1.2
ip route 192.168.0.0 255.255.0.0 10.0.2.2 20

```

## Network Services and Automation

* Centralized Infrastructure: Deployed dedicated DHCP server at `192.168.40.10` in VLAN 40.
* DHCP Relay: Configured `ip helper-address 192.168.40.10` on all SVIs across SW1 and SW2.
* Scope Allocation: Server hands out unique network parameters and virtual HSRP gateway IPs (`192.168.X.1`) per requesting VLAN.

## Security and Traffic Management (Extended ACLs)

* Micro-segmentation: Applied inbound Extended ACLs on user SVI interfaces (`interface vlan 10`, `interface vlan 20`).
* Policy Rules:
* Full access to central server farm (VLAN 40).
* Web-only access (TCP 80/443) to DMZ (VLAN 50).
* Explicit block on inter-VLAN traffic between user subnets (`192.168.0.0/16`).
* Global internet access via trailing `permit ip any any`.



```text
! Inbound Extended ACL on Core SVI
ip access-list extended ACL_VLAN10
 permit ip 192.168.10.0 0.0.0.255 192.168.40.0 0.0.0.255
 permit tcp 192.168.10.0 0.0.0.255 192.168.50.0 0.0.0.255 eq 80
 permit tcp 192.168.10.0 0.0.0.255 192.168.50.0 0.0.0.255 eq 443
 deny ip 192.168.10.0 0.0.0.255 192.168.0.0 0.0.255.255
 permit ip any any

interface Vlan10
 ip access-group ACL_VLAN10 in

```

## Verification and Resilience Testing

* Gateway Verification: Executed `show standby brief` on SW1/SW2 to confirm Active/Standby states and virtual IP binding.
* Link Failure Simulation: Disabled `Fa0/10` on SW1 during active ping sessions.
* HSRP failover transferred gateway ownership to SW2 within 1-2 dropped ICMP packets.
* Router0 automatically activated secondary route via SW2 (`10.0.2.2`), restoring return path traffic.


* ACL Policy Validation:
* `ping` between VLAN 10 and VLAN 20 returned `Destination Host Unreachable`.
* `ping` from VLAN 10 to VLAN 40 server succeeded.
* `HTTP` request from VLAN 10 to DMZ server succeeded, while `ICMP` ping to DMZ was dropped.
