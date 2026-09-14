# 3TS RTMS: Standalone Mode (Local Storage)

## Overview
The 3TS Real-Time Network Scanner (RTMS) can operate in a fully autonomous **Standalone Mode**. When the PostgreSQL database is disabled, the scanner automatically routes all discovered assets, open ports, and security alerts to local flat files (CSV, JSON, and LOG). 

This mode is highly recommended for tactical deployments (e.g., running from a USB drive, a temporary virtual machine, or a lightweight sensor like a Raspberry Pi) where setting up a full database server is impractical or undesirable.

## Configuration
To activate Standalone Mode, modify your main configuration file:

```properties
# Disable PostgreSQL integration to force local file storage
postgres.enabled=false
```

## Output Architecture
Data is automatically organized hierarchically by Organization Name and Network CIDR to prevent data overlap across different environments. All files are generated inside the data/output/ directory.

data/output/
└── <organization_name>/
    └── net_<network_cidr>/                 
        ├── inventory_hosts.csv             
        ├── inventory_services.csv          
        └── scans/
            ├── alerts_YYYYMMDD_HH.log      
            └── scan_<ip>_YYYYMMDD_HHMMSS.json


## File Specifications
1. inventory_hosts.csv

Maintains the current, up-to-date state of all discovered devices on the specific subnet.

Behavior: If a device is scanned multiple times, its existing row is updated to reflect the latest state. It acts as the primary asset inventory.

Key Fields: ip_address, mac_address, hostname, vendor, os_name, is_up, last_seen.

2. inventory_services.csv

A detailed, flat-file mapping of all open ports and identified services.

Behavior: When a specific IP is rescanned, its previous port entries are dynamically replaced with the fresh results, while keeping the data for other IPs intact.

Key Fields: ip_address, port, protocol, state, service_name, product, version.

3. scans/alerts_*.log

A human-readable, append-only log of security alerts (e.g., new unknown MAC addresses joining the network, or previously stable hosts disappearing).

Behavior: Log files are rotated automatically and grouped by the hour.

Format: [SEVERITY] ALERT_TYPE - IP: <ip_address> - <Description>

4. scans/scan_*.json

The raw, complete JSON output of deep host scans (Nmap module results, OS fingerprinting, NTLM extracts, etc.).

Behavior: These files are preserved historically and are never overwritten. They provide a complete, auditable technical trail of every deep scan executed.