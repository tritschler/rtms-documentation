# Dynamic Network Asset Inventory

The **Assets** module (`/assets`) maintains a real-time inventory of your monitored infrastructure.

---

## 1. Automated Host Discovery

Every device present on audited subnets is automatically mapped by RTMS probes:
* **IP Address & CIDR Subnet**: Logical network location.
* **MAC Address & Hardware Vendor (OUI)**: Physical hardware manufacturer (e.g. *Cisco*, *Dell*, *Apple*, *Schneider Electric*).
* **Resolved Hostname**: Resolved through reverse DNS queries, NetBIOS/mDNS banners, or passive DHCP request interception (**DHCP Snooping**).
* **Operating System (OS)**: TCP/IP stack fingerprinting derived via Nmap.
* **Presence Status**: Highlights whether the asset responded during the latest sweep cycle (`Online`) or historical duration since last seen.

---

## 2. Asset Profile & Detailed Inspection

Clicking any device in the list opens its technical profile:

* **Open Ports & Services**: Exhaustive inventory of listening TCP/UDP ports, transport protocols, service banners, and software versions.
* **Associated CVEs**: List of known vulnerabilities affecting detected software packages, enriched with CVSS v3 ratings.
* **Detection History**: Timestamps documenting initial network discovery and latest active response.
* **Deep Scan Status**: Confirms whether the device is eligible for deep security audits or excluded (e.g. sensitive industrial PLC or medical device).

---

## 3. Search & Report Export

* **Global Search & Local Filtering**: Leverage the top header magic search bar (`Cmd + K`) or the in-table filter input to immediately pinpoint an IP address fragment (e.g. `192.168.1.`), hardware vendor, or server hostname.
* **Export Formats**: Download the active inventory state in **CSV** or **JSON** for reporting or CMDB reconciliation.
