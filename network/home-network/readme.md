# My-Home network project

## Main objects:
- Create separated VLANs, to disable access from certain VLANs to the rest of the network.
- Create fully-functional network, that would make my everyday life easier and safer.
- Preserve connection between certain machines

## Network Graph
```
[ INTERNET ]
      │
      ▼
┌──────────────────────────────────────────────┐
│ TP-Link Archer MR200                         │
│ Network: 192.168.1.0/24                      │
│ • Provides Wi-Fi                             │
└────────────┬────────────────────────┬────────┘     
             │ (LAN Cable)            │ (LAN Cable)
             ▼ IP: 192.168.1.10       ▼ IP: 192.168.1.50
┌──────────────────────────┐    ┌─────────────────┐
│ MikroTik hAP lite        │    │ Pi-hole         │
│ Router / Gateway         │    │ (Raspberry Pi)  │
│ (192.168.88.1)           │    └─────────────────┘
└────────────┬─────────────┘
             │
             │ [ BRIDGE (Ports 1-4) ]
             ├───────────────────────┬───────────────────┐
             │                       │                   │
             ▼ Port 2                ▼ Port 3            ▼ Port 4 (VLAN 200)
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │  PC (Computer)   │    │  Proxmox VE      │    │    IP Camera     │
    │  192.168.88.x    │    │  (Host & VLANs)  │    │  (No routing)    │
    └──────────────────┘    └────────┬─────────┘    └──────────────────┘
                                     │
                  ┌──────────────────┼──────────────────┬──────────────────┐
                  │                  │                  │                  │
                  ▼                  ▼                  ▼                  ▼
               [VLAN 10]          [VLAN 20]          [VLAN 30]          [VLAN 40]
```
## Tp-Link router configuration
- DHCP scope: `192.168.1.100/24` - `192.168.1.200/24`
- DNS addresses: `192.168.1.50`, `1.1.1.2`
- Static routing to networks via `192.168.1.10` (MikroTik hAP lite)
  - `192.168.10.0/24` (VLAN10)
  - `192.168.20.0/24` (VLAN20)
  - `192.168.30.0/24` (VLAN30)
  - `192.168.40.0/24` (VLAN40)
  - `192.168.200.0/24` (VLAN200)
- DHCP reservations
  - Mirotik `192.168.1.10`
  - Raspberry Pi `192.168.1.50`
    
## Pi-hole (Raspberry Pi) configuration
- Static DNS addresses: `1.1.1.2`; `1.0.0.2`
- DNS aliases:
  - `pi.local` --> `192.168.1.50`
  - `proxmox.local` --> `192.168.88.150`
  - `omv.local` --> `192.168.10.250`

## MikroTik configuration:
- Allows movement from both 192.168.88.0/24 and 192.168.1.0/24 to every VLAN, creating access to the one-way isolated VLAN's
- Works as gateways for every VLAN, except VLAN200.
- DHCP scope:
  - `192.168.10.50/24` - `192.168.10.250/24` (VLAN10)
  - `192.168.20.50/24` - `192.168.20.250/24` (VLAN20)
  - `192.168.30.50/24` - `192.168.30.250/24` (VLAN30)
  - `192.168.40.50/24` - `192.168.40.250/24` (VLAN40)
  - `192.168.200.50/24` - `192.168.200.250/24` (VLAN200)
- Created address lists:
  - `home`: `192.168.1.0/24`, `192.168.88.0/24`
  - `proxmox`: `192.168.10.0/24`, `192.168.20.0/24`, `192.168.30.0/24`, `192.168.40.0/24`
    
- Firewall rules:
  -  allow forwarding as `estabilished` and `related` from `proxmox` to `home`
  -  allow forwarding anywhere except `home` for the entire `proxmox` addresses list
  -  allow forwarding as `estabilished` and `related` from VLAN200 to anywhere
