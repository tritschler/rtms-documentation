# Network Policies, Subnets & Deep Scan Targeting

This module configures operational security policies and probing boundaries across subnets discovered by RTMS.

---

## 1. Subnet Naming & Categorization

Each automatically discovered CIDR range (e.g. `10.20.0.0/24`) can be qualified by administrators:
* **Friendly Label**: E.g. *VLAN 20 - Application Servers*, *VLAN 50 - Guest Wi-Fi*, *VLAN 100 - Industrial OT Automation*.
* **Description & Site Location**: Provides vital context during SOC incident response.

---

## 2. Dual Opt-In Security Model for Deep Scan

To protect delicate operational hardware (programmable logic controllers, medical infusion pumps, sorting equipment):

```mermaid
flowchart TD
    A[Discovered Network Host] --> B{1. Global Master Switch Active?}
    B -- No --> E[Soft Discovery Mode Only (ARP/ICMP/MAC)]
    B -- Yes --> C{2. Subnet Explicitly Configured for Deep Scan?}
    C -- No (Default) --> E
    C -- Yes --> D{3. Individual Asset Excluded?}
    D -- Yes --> E
    D -- No --> F[Deep Scan Authorized: Nmap + Security Plugins]
```

* **Zero-Trust Default (`deep_scan = false`)**: Newly discovered subnets are **never subjected to deep scanning** unless explicitly authorized by an administrator.
* **Asset-Level Exclusions**: Even within subnets where Deep Scan is active, delicate individual devices can be shielded by ticking *“Exclude from Deep Scan”* on their asset profile.

---

## 3. Subnet MAC Address Whitelists

For subnets with frequent legitimate turnover or developer testbenches:
* Administrators can whitelist approved MAC addresses per CIDR block.
* Whitelisted devices suppress `NEW_HOST` alerts, eliminating alert fatigue and focusing analyst attention on actual unauthorized intrusions.
