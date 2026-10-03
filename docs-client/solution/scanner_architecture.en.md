# RTMS Scanner: Architecture & Capabilities

This document details the technical architecture, deployment topologies, and operational capabilities of the **RTMS (Real-Time Monitoring & Security)** network sensor and engine developed by **3TS Consulting**.

Engineered for demanding enterprise and industrial environments, RTMS combines continuous, zero-impact passive network discovery with granular active audits, providing continuous visibility and threat detection across IT, OT, and IoT assets.

---

## 1. Executive Overview & Positioning

Traditional network security approaches typically rely on heavy host agents or blind active network vulnerability scanners that risk network congestion and device instability (such as disrupting programmable logic controllers, printers, or medical devices).

**The RTMS Scanner employs a non-disruptive, hybrid approach:**

* **Real-Time Visibility (Zero-Impact)**: Continuous passive listening to native network broadcast/multicast and discovery traffic (ARP, DHCP, mDNS, LLMNR, SSDP, CDP/LLDP).
* **Early Threat Detection**: Instant alerting for unauthorized devices (*rogue devices*), IP/MAC address conflicts, and anomalous network behaviors.
* **Granular & Controlled Audits**: In-depth discovery of exposed services (*Deep Scan*) and protocol compliance audits, strictly governed by subnet policies.
* **Sovereign Vulnerability Correlation**: Real-time cross-referencing of discovered assets against the NIST National Vulnerability Database (NVD) via a local microservice, with zero external telemetry leakage.

```mermaid
graph TD
    subgraph "Monitored Client Infrastructure"
        SW["Core / Distribution Switch<br/>(Port Mirroring / SPAN / TAP)"]
        LAN["Workstations & Servers"]
        IOT["IoT Devices & Printers"]
        OT["Industrial Automata (OT)"]
        SW --- LAN
        SW --- IOT
        SW --- OT
    end

    subgraph "RTMS Appliance / Probe"
        PROBE["RTMS Scanner Probe"]
        PASSIVE["Passive Engine<br/>(Zero-Impact Discovery)"]
        ACTIVE["Active Audit Engine<br/>(Targeted Deep Scan)"]
        PROBE --> PASSIVE
        PROBE --> ACTIVE
    end

    SW -.->|Mirrored traffic| PROBE

    subgraph "Central RTMS Platform"
        WG["Encrypted WireGuard Tunnel"]
        API["FastAPI Backend & RBAC"]
        DB[("Hardened PostgreSQL<br/>rtms_db")]
        NVD["Local NVD Microservice<br/>(NIST CVE / CPE)"]
        WEB["Web Management Console<br/>(SOC & NIS2 Compliance)"]

        WG --> API
        API --> DB
        API --> NVD
        API --> WEB
    end

    PROBE ==>|Encrypted Telemetry (mTLS / WireGuard)| WG
```

---

## 2. Deployment Topologies

The RTMS probe adapts to any enterprise network architecture, from single-site operations to globally distributed, multi-branch organizations.

### Mode 1: Passive Listening via Port Mirroring (SPAN / TAP)
* **Recommended for**: Core networks, data centers, and critical network segments.
* **Mechanism**: The network switch mirrors broadcast/multicast traffic or monitored VLANs directly to the probe's dedicated capture interface.
* **Security advantage**: The capture interface is **strictly passive** (no IP address assigned on the monitored segment, zero packet transmission, probe is fully invisible and untargetable from the monitored network).

### Mode 2: Multi-Homed Probe (Segregated Capture & Management)
* **Recommended for**: Physical appliance deployments (1U rackmount or hardened industrial mini-PCs).
* **Interface 1 (Monitoring)**: Connected to the local subnet or mirrored VLANs.
* **Interface 2 (Management & Reporting)**: Connected to a dedicated management VLAN or directly established over a point-to-point WireGuard VPN tunnel to the central platform.
* **Security advantage**: Strict network segregation. Even in the event of a local workstation subnet compromise, the monitoring backbone remains isolated and encrypted.

### Mode 3: High Availability (Active / Standby Failover)
* Two RTMS probes are deployed on the same segment in a redundant pair.
* The primary probe actively collects and transmits telemetry.
* The secondary probe tracks the primary's health heartbeat through the central platform; in case of hardware or network failure, the secondary automatically assumes active monitoring with zero data loss.

### Mode 4: Remote Branch Probes (RTMS Local Agent)
* For remote branch offices, teleworkers, or private cloud environments (AWS, Azure, GCP).
* A lightweight, autonomous agent performs local discovery and securely forwards encrypted metrics to the central platform over HTTPS/REST or WireGuard.

---

## 3. Detection Engine & Analytical Capabilities

### A. Asset Mapping & Digital Fingerprinting
Upon startup, the RTMS probe establishes a live, comprehensive inventory of all connected network assets:
* **Instant Host Discovery**: Detects MAC addresses, assigned IP addresses, DHCP leases, NetBIOS names, and mDNS hostnames.
* **Manufacturer Identification**: Automatic hardware resolution against the official IEEE OUI database (Apple, Cisco, Dell, HP, Fortinet, Schneider Electric, Siemens, etc.).
* **OS & Firmware Fingerprinting**: Multi-layer analysis of TCP/IP stack signatures (SYN window sizes, default TTL), mDNS/Bonjour service advertisements, user-agents, and protocol banners.
* **Automated Device Categorization**: Classifies devices into functional groups (Server, Workstation, Printer, Switch/Router, IP Camera, Industrial Controller, Mobile/Tablet).

### B. Continuous Network Posture Monitoring
The engine continuously inspects network-layer traffic to detect low-level anomalies:
* **Rogue Device Detection**: Instant alert when an unapproved or unknown device connects to a subnet for the first time.
* **Address Spoofing Detection (ARP Spoofing)**: Identifies IP/MAC conflicts (two different MAC addresses claiming the same IP) and Man-in-the-Middle (MitM) attempts.
* **Gateway & DNS Drift**: Immediate warnings if an unauthorized rogue DHCP server or deceptive default gateway appears on the network.

### C. Granular Deep Scan & Targeted Audits
Unlike indiscriminate vulnerability scanners, RTMS allows security teams to configure **subnet-specific scan policies**:
* **Configurable Port Profiles**: Essential infrastructure ports, web services, top 1000 ports, or custom ranges.
* **Stealth TCP Scanning (SYN / Connect)**: Accurately evaluates exposed attack surface while strictly throttling packet rates to prevent switch buffer exhaustion.
* **Exclusion of Sensitive OT Zones**: Subnets can be designated as "Strictly Passive" (e.g., manufacturing lines, medical equipment) to completely prohibit active scanning probes.

### D. Integrated Specialized Audits
The probe features dedicated security audit modules:
* **Mail & Open Relay Audit**: Verifies local SMTP servers to eliminate spam relay and domain spoofing risks.
* **Legacy Protocol Auditing**: Audits SMBv1 file shares (primary propagation vector for ransomware like WannaCry), unencrypted Telnet sessions, and deprecated SSL/TLS web ciphers.
* **Remote Access Exposure**: Detects inadvertently exposed RDP, VNC, and SSH interfaces across internal segments.

---

## 4. Sovereign Vulnerability Intelligence (Local NVD Microservice)

The RTMS platform incorporates a localized instance of the NIST **National Vulnerability Database (NVD)**:

* **Zero Information Leakage**: Your asset inventory, firmware revisions, and software versions never leave your infrastructure. All CPE (*Common Platform Enumeration*) correlations occur locally on your private RTMS server.
* **Continuous Incremental Updates**: Scheduled background synchronization with the NIST API to ingest latest CVE bulletins, CVSS v3.1 severity scores, and attack vectors.
* **Severity-Based Prioritization**: Automated triage highlighting critical vulnerabilities (CVSS ≥ 9.0) with confirmed impact on discovered assets.

---

## 5. Probe Hardening, Security & Sovereignty

The RTMS probe is designed according to **defense-in-depth** cybersecurity principles:

| Security Domain | Implemented Controls |
| :--- | :--- |
| **External Listening Surface** | Zero open listening ports on network capture interfaces. |
| **Probe-to-Server Authentication** | Unique, revocable cryptographic Bearer tokens bound to hardware Machine IDs. |
| **Data-in-Transit Encryption** | All telemetry is encapsulated within encrypted WireGuard tunnels (ChaCha20-Poly1305) or HTTPS/TLS 1.3. |
| **Offline Resilience** | Local telemetry buffering during network disconnections; seamless automatic resynchronization upon reconnection. |
| **RBAC Isolation** | Strict segregation of duties (Operator, SOC Analyst, Compliance Auditor, Administrator) enforcing least privilege. |

---

## 6. Enterprise Integration & Regulatory Compliance

### European NIS 2 Directive Alignment
RTMS directly supports compliance mandates for Essential and Important entities under the EU NIS 2 Directive:
* **Article 21 (Risk Management Measures)**: Automated, continuously updated asset inventory and proactive vulnerability management.
* **Article 23 (Incident Reporting)**: Real-time discovery of rogue or compromised devices, providing evidence trails required for mandatory 24-hour notifications.

### Enterprise SIEM & CMDB Connectors
* **CMDB Reconciliation (iTop)**: Automated bidirectional reconciliation between discovered network reality and the declared CMDB inventory.
* **SOC / SIEM Export**: Out-of-the-box Syslog RFC 5424 streaming to enterprise SIEM platforms (Wazuh, Splunk, Elastic, Microsoft Sentinel).

---

## 7. Technical Specifications Summary

| Feature | Specification |
| :--- | :--- |
| **Capture Modes** | Passive (libpcap / raw sockets), Targeted Active (TCP SYN/Connect, ICMP, DNS, SMB, SMTP) |
| **Passive Protocols Inspected** | ARP, DHCP, mDNS, LLMNR, SSDP, CDP, LLDP, NetBIOS, IPv4, IPv6 |
| **Collection Frequency** | Continuous real-time passive listening; scheduled active audit cycles (e.g., 2h, 6h, 24h) |
| **Hardware Probe Footprint** | Physical appliance x86_64 / ARM (Raspberry Pi 4/5, ruggedized mini-PC) or Virtual Appliance (VMware, Proxmox, Hyper-V, KVM) |
| **Supported Operating Systems** | Hardened Linux (Debian 12, Ubuntu 22.04/24.04 LTS, Rocky Linux, Alpine) |
| **Network Bandwidth Requirement** | Less than 50 KB/s in steady-state operations (compressed metadata and events) |
| **Vulnerability Database** | Locally replicated NIST NVD (CVE, CPE, CVSS v2 / v3.1) |

---

*To schedule a technical evaluation or live demonstration within your network environment, contact **3TS Consulting** at [https://3ts.ai](https://3ts.ai) or via email at `contact@3ts.ai`.*
