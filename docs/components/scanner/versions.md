# Versions

## v0.1 - April 2026 (demo version for 3 pilots)
- core functions: DISCOVER, CHECK_NETWORK, SCAN_HOSTS
- CVE tracking
- skip license check
- Linux Ubuntu 24.04

## v1.0 - July 2026

- database: postgresql
- no postgres -> results are stored in files
- integrations: iTop, Splunk, Vault, NIST CVE
- Nginx server (simple read-only web server showing results of scans)
- tests: native, docker

- CRA compliance
- skip license check

## v2.0 - September 2026
- Multi-scanner architecture with centralized service registry (`admin.service_registry`)
- Network Scan Archive System (`scanner.scan_archives`) with live diffing and JSON export
- Asynchronous SNMP discovery engine (`snmp_discovery.py`) for router identity and ARP table extraction
- Custom SNMP target IP and community configuration for mock/external devices
- Multi-tier ARP Spoofing & MITM Anomaly Detection (`ARP_SPOOFING_GATEWAY`, `ARP_POISONING_DETECTED`, `IP_MAC_CONFLICT`)
- Real-time SNMP vs wire cross-validation for active poisoning detection
- Local agents native Linux / macOS / Windows inventory integration
- Microsoft Teams, Slack, SMTP, and Splunk multi-channel alert engine
- Dedicated NIS2 Compliance overview and scanning archives UI
- 2-Tier Wi-Fi Scanning Control: Global Master Switch (`admin.system_config.wifi_scan_enabled`) and Per-Scanner Switch (`admin.service_registry.scan_wifi`)
- 2-Tier Ethernet Scanning Control: Global Master Switch (`admin.system_config.ethernet_scan_enabled`, defaults to `true`) and Per-Scanner Switch (`admin.service_registry.scan_ethernet`, defaults to `true`)
- Unified Network Media Scanning Policy UI in Scanner Configuration with real-time feedback and blackout safeguard
- Dedicated Wi-Fi Probe Mode support (Ethernet disabled, Wi-Fi enabled)
- Full deprecation and removal of legacy CLI `--strict` mode
- Strict Ethernet precedence over Wi-Fi on identical subnets
- Real-time event-driven DHCP hostname discovery (`DHCPSnooper`) with immediate `admin.assets` database synchronization and scan priority resolution
- Subnet MAC Whitelist management (`admin.subnet_mac_whitelist`) to suppress `NEW_HOST` and unnamed device alerts per CIDR network

