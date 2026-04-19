# SDN Static Routing using POX Controller

**Student:** Roshan | **SRN:** PES1UG24CS387  
**Course:** Computer Networks | **Semester:** 4

---

## Problem Statement

Traditional networks rely on distributed, manually configured routing tables on each device. This project demonstrates how Software-Defined Networking (SDN) centralises routing logic in a single controller, which programs all switches simultaneously using OpenFlow flow rules.

The objective is to implement static routing paths using a POX SDN controller that:
- Installs explicit flow rules on each switch at connection time
- Handles PacketIn events and logs forwarding decisions
- Validates correct packet delivery across all host pairs
- Demonstrates failure and recovery through a regression test

---

## Topology

```
    h1 (10.0.0.1) ──── s1 ──── s2 ──── s3 ──┬── h2 (10.0.0.2)
                                              └── h3 (10.0.0.3)
```

| Element | Detail |
|---|---|
| Switches | s1, s2, s3 — Open vSwitch, OpenFlow 1.0 |
| Hosts | h1 (10.0.0.1), h2 (10.0.0.2), h3 (10.0.0.3) |
| Controller | POX, listening on 0.0.0.0:6633 |
| Links | h1–s1, h2–s3, h3–s3, s1–s2, s2–s3 |

---

## Flow Rule Design

The controller installs the following rules on each switch when it connects (ConnectionUp event):

| Switch | Match | Action | Purpose |
|---|---|---|---|
| s1 | `nw_dst=10.0.0.1` | `output:port1` | Forward to h1 |
| s1 | `nw_dst=10.0.0.2` | `output:port2` | Forward toward s2 |
| s1 | `nw_dst=10.0.0.3` | `output:port2` | Forward toward s2 |
| s2 | `nw_dst=10.0.0.1` | `output:port1` | Forward toward s1 |
| s2 | `nw_dst=10.0.0.2` | `output:port2` | Forward toward s3 |
| s2 | `nw_dst=10.0.0.3` | `output:port2` | Forward toward s3 |
| s3 | `nw_dst=10.0.0.1` | `output:port3` | Forward toward s2 |
| s3 | `nw_dst=10.0.0.2` | `output:port1` | Forward to h2 |
| s3 | `nw_dst=10.0.0.3` | `output:port2` | Forward to h3 |
| all | `dl_type=0x0806` (ARP) | `FLOOD` | ARP flood |

---

## Repository Structure

```
.
├── top.py              # Mininet topology (3 switches, 3 hosts)
├── static_router.py    # POX controller (static routing + PacketIn handler)
└── README.md
```

---

## Setup & Execution

### Prerequisites

```bash
# Install Mininet
sudo apt install mininet -y

# Install POX
cd ~
git clone https://github.com/noxrepo/pox.git

# Copy controller into POX
cp static_router.py ~/pox/ext/
```

### Step 1 — Start POX Controller (Terminal A)

```bash
cd ~/pox
python3 pox.py log.level --DEBUG ext.static_router
```

Expected output:
```
INFO:static_router:Static Router started
INFO:core:POX 0.7.0 (gar) is up.
DEBUG:openflow.of_01:Listening on 0.0.0.0:6633
```

### Step 2 — Start Mininet (Terminal B)

```bash
cd /path/to/project
sudo mn --custom top.py --topo statictopo --controller remote --mac
```

Once switches connect, the controller installs flow rules automatically.

### Step 3 — Run Tests

```bash
# Scenario 1: Normal forwarding
mininet> pingall

# Scenario 2: Failure test — delete all flow rules
mininet> sh ovs-ofctl del-flows s1
mininet> sh ovs-ofctl del-flows s2
mininet> sh ovs-ofctl del-flows s3
mininet> pingall

# Regression test — restart controller, rules reinstalled automatically
# (Ctrl+C POX in Terminal A, then rerun python3 pox.py ...)
mininet> pingall

# iperf throughput test
mininet> h2 iperf -s &
mininet> h1 iperf -c 10.0.0.2 -t 5

# View flow tables
mininet> sh ovs-ofctl dump-flows s1
mininet> sh ovs-ofctl dump-flows s2
mininet> sh ovs-ofctl dump-flows s3
```

### Step 4 — Packet Capture (Terminal C)

```bash
sudo tcpdump -i any icmp -v
```

---

## Expected Output

### Scenario 1 — Normal Forwarding
```
mininet> pingall
*** Ping: testing ping reachability
h1 -> h2 h3
h2 -> h1 h3
h3 -> h1 h2
*** Results: 0% dropped (6/6 received)
```

### Scenario 2 — Failure (rules deleted)
```
mininet> pingall
*** Results: 100% dropped (0/6 received)
```

### Regression Test (controller restarted, rules reinstalled)
```
mininet> pingall
*** Results: 0% dropped (6/6 received)
```

### iperf Result
```
[ 1] 0.0000-5.0054 sec  15.1 GBytes  25.9 Gbits/sec
```

### Flow Table (s1)
```
cookie=0x0, ip,nw_dst=10.0.0.1 actions=output:s1-eth1
cookie=0x0, ip,nw_dst=10.0.0.2 actions=output:s1-eth2
cookie=0x0, ip,nw_dst=10.0.0.3 actions=output:s1-eth2
cookie=0x0, arp actions=FLOOD
```

---

## Proof of Execution

### Screenshot 1 — Controller Startup & Flow Rule Installation
POX connects to all 3 switches and installs IP forwarding rules and ARP flood rules on each via ConnectionUp event.

### Screenshot 2 — Scenario 1: Normal Forwarding (0% loss)
`pingall` confirms all host pairs can communicate — 6/6 packets received.

### Screenshot 3 — Scenario 2: Failure Test (100% loss)
Flow rules manually deleted from all switches using `ovs-ofctl del-flows`. Subsequent `pingall` shows 100% packet loss confirming rules are essential.

### Screenshot 4 — Controller Restart & Rule Reinstallation
POX controller restarted. All 3 switches reconnect and receive fresh flow rules automatically via ConnectionUp.

### Screenshot 5 — Regression Test Passed (0% loss restored)
`pingall` after controller restart shows 0% loss again — confirming static routing paths are correctly restored.

### Screenshot 6 — Flow Tables (all 3 switches)
`ovs-ofctl dump-flows` shows exact flow entries on s1, s2, s3 with packet/byte counters confirming traffic matched the rules.

### Screenshot 7 — iperf Throughput
TCP bandwidth test between h1 and h2 shows 25.9 Gbits/sec confirming correct end-to-end data plane forwarding.

### Screenshot 8 — tcpdump Packet Capture
tcpdump capture on all interfaces shows ICMP echo request (10.0.0.1 → 10.0.0.2) traversing s1→s2→s3 and ICMP echo reply (10.0.0.2 → 10.0.0.1) returning along the same path, confirming correct static flow rule installation and end-to-end packet delivery.

---

## SDN Concepts Demonstrated

| Concept | Where |
|---|---|
| Centralised control plane | Single POX controller manages all 3 switches |
| ConnectionUp event | Controller installs rules the moment a switch connects |
| PacketIn event | Handler logs all packets that reach the controller |
| Match–action rules | `nw_dst` match → `output:port` action |
| ARP handling | Flood rule ensures ARP resolution works across switches |
| Failure simulation | `ovs-ofctl del-flows` removes rules, causing total loss |
| Regression testing | Controller restart restores exact same routing behaviour |

---

## References

1. Mininet Documentation — http://mininet.org/walkthrough/
2. POX SDN Controller Wiki — https://noxrepo.github.io/pox-doc/html/
3. OpenFlow 1.0 Specification — https://opennetworking.org/wp-content/uploads/2013/04/openflow-spec-v1.0.0.pdf
4. Open vSwitch Documentation — https://docs.openvswitch.org/
