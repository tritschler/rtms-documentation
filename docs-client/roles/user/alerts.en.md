# Network Alerts & Incident Tracking

The **Alerts** module (`/alerts`) catalogs in real time all noteworthy events and anomalies detected across audited subnets.

---

## 1. Common Alert Types

| Alert Type | Severity | Description | Recommended Action |
| :--- | :---: | :--- | :--- |
| `NEW_HOST` | 🟡 Info | A previously unseen device has connected to the network. | Verify whether the equipment is authorized or unmanaged Shadow IT. |
| `IP_MAC_CONFLICT` | 🟠 Medium | An existing IP address is claimed by a different MAC address. | Check for static IP conflicts or hardware NIC replacement. |
| `HOST_DOWN` | 🔵 Low | A previously reachable host has stopped responding to sweeps. | Verify whether the shutdown was planned or an unplanned outage. |
| `ARP_SPOOFING_GATEWAY` | 🔴 Critical | Gateway spoofing attempt via ARP table poisoning (Man-in-the-Middle). | Immediately isolate the offending network port and alert the SOC team. |

---

## 2. Acknowledging & Filtering Alerts

* **Severity Filtering**: Filter priority alerts (`Critical`, `High`) to focus immediate response efforts.
* **Alert Acknowledgment**: Mark legitimate or mitigated events as *Acknowledged* to maintain an organized operational backlog.
* **Multi-Channel Dispatch**: Depending on administrative settings, alerts can be forwarded via Email, Microsoft Teams, or Slack webhooks.
