# Cisco Network Infrastructure & Redundant Routing Implementation

## Core Router Backbone & Fiber Connectivity
- Centralized Architecture: Deployed 4 interconnected core routers forming the backbone of the network.
- Point-to-Point Links: Configured dedicated /31 networks (`10.0.0.0/31`, `20.0.0.0/31`, `30.0.0.0/31`, `40.0.0.0/31`) for efficient point-to-point router communication.
- Fiber Interconnection: Established backbone connectivity between core routers using fiber-optic links.
- Resilience: Designed the backbone with redundant paths, allowing routers to maintain operation and network communication after failure of an individual cable.

## Internal Network Segmentation
- Distributed LANs: Connected internal /24 networks to the core router infrastructure for end-user and service connectivity.
- Network Allocation:
  - `192.168.0.0/24` — gateway `192.168.0.1`
  - `172.16.0.0/24` — gateway `172.16.0.1`
  - `200.200.0.0/24` — gateway `200.200.0.1`
  - `100.100.0.0/24` — gateway `100.100.0.1`
- Gateway Configuration: Assigned dedicated router interfaces as default gateways for each internal subnet.

## DHCP Infrastructure & Address Management
- DHCP Deployment: Implemented a dedicated DHCP server within each internal network.
- Automatic Addressing: Configured DHCP services to provide hosts with IP addresses and corresponding network parameters.
- Subnet Management: Maintained consistent `/24` addressing across internal LAN segments.
- Connectivity Verification: Confirmed successful communication between hosts located in different internal networks.

## Inter-Network Routing
- Routed Communication: Enabled end-to-end communication between all internal subnets through the interconnected core routers.
- Multi-Network Reachability: Verified connectivity between `192.168.0.0/24`, `172.16.0.0/24`, `200.200.0.0/24`, and `100.100.0.0/24`.
- Backbone Utilization: Used the central router infrastructure to forward traffic between geographically/logically separated LAN segments.

## Fault Tolerance & Network Continuity
- Link Failure Testing: Simulated physical cable failures within the backbone topology.
- Fault Isolation: Confirmed that failure of a single connection does not disable the remaining routers.
- Continued Operation: Verified that available paths continue carrying network traffic after backbone link disruption.

## Cisco Packet Tracer Implementation & Verification
- Topology Design: Built and interconnected the complete router, LAN, and DHCP infrastructure in Cisco Packet Tracer.
- Configuration Validation: Verified interface addressing, gateway reachability, DHCP assignment, and inter-subnet communication.
- Connectivity Testing: Used ICMP (Internet Control Message Protocol) testing and Cisco CLI `show` commands to validate network operation and fault tolerance.
