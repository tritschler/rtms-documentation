# 3TS RTMS: Scanner Operational Modes & Standalone Storage

## Operational Modes Summary

The RTMS Scanner probe (`rtms-scanner`) supports three primary operating models:

| Mode | Communication / Storage | Network Requirements | Best Used For |
| :--- | :--- | :--- | :--- |
| **Decoupled API Mode (Recommended)** | Centralized `rtms-web` via HTTPS REST API (`/api/scanner/*`) | Port 443 / HTTPS to RTMS Web Server | Multi-VLAN enterprise probes, remote branch offices, zero-trust network segments. **No direct database access required.** |
| **Direct Database Mode** | Direct PostgreSQL queries via `psycopg2` | Port 5432 to PostgreSQL Server | Co-located single-host installations where the scanner runs alongside the database. |
| **Autonomous Standalone Mode** | Local flat files (`CSV`, `JSON`, and `LOG`) | 100% air-gapped / offline (Zero network egress) | Tactical deployments, pen-testing USB drives, air-gapped forensic audits, or lightweight Raspberry Pi sensors. |

---

## Autonomous Standalone Mode (Local Storage)

When central servers and PostgreSQL are disabled, the scanner operates in fully autonomous **Standalone Mode**. It routes all discovered assets, open ports, and security alerts to local flat files on disk.

### Configuration
To activate Standalone Mode, disable database and API connectivity in `scanner.properties` or environment variables:

```properties
# Disable database and central server sync to force local file storage
postgres.enabled=false
```

Or omit `RTMS_SERVER_URL` and `ENV_POSTGRES_PASSWORD` when launching the daemon.

## Output Architecture
Data is automatically organized hierarchically by Organization Name and Network CIDR to prevent data overlap across different environments. All files are generated inside the `data/output/` directory:

```
data/output/
└── <organization_name>/
    └── net_<network_cidr>/                 
        ├── inventory_hosts.csv             
        ├── inventory_services.csv          
        └── scans/
            ├── alerts_YYYYMMDD_HH.log      
            └── scan_<ip>_YYYYMMDD_HHMMSS.json
```

## File Specifications

### 1. `inventory_hosts.csv`
Maintains the current, up-to-date state of all discovered devices on the specific subnet.
* **Behavior:** If a device is scanned multiple times, its existing row is updated to reflect the latest state. It acts as the primary asset inventory.
* **Key Fields:** `ip_address`, `mac_address`, `hostname`, `vendor`, `os_name`, `is_up`, `last_seen`.

### 2. `inventory_services.csv`
A detailed, flat-file mapping of all open ports and identified services.
* **Behavior:** When a specific IP is rescanned, its previous port entries are dynamically replaced with the fresh results, while keeping the data for other IPs intact.
* **Key Fields:** `ip_address`, `port`, `protocol`, `state`, `service_name`, `product`, `version`.

### 3. `scans/alerts_*.log`
A human-readable, append-only log of security alerts (e.g., new unknown MAC addresses joining the network, or previously stable hosts disappearing).
* **Behavior:** Log files are rotated automatically and grouped by the hour.
* **Format:** `[SEVERITY] ALERT_TYPE - IP: <ip_address> - <Description>`

### 4. `scans/scan_*.json`
The raw, complete JSON output of deep host scans (Nmap module results, OS fingerprinting, NTLM extracts, etc.).
* **Behavior:** These files are preserved historically and are never overwritten. They provide a complete, auditable technical trail of every deep scan executed.

---

## 5. Resilience & Offline Mode in Decoupled API Operation

In Decoupled API Mode (`RTMS_SERVER_URL`), if the central backend server becomes unreachable (network disconnection, scheduled maintenance, or outage):

1. **Continuous Scanning & Local Configuration Cache:**
   The probe continues auditing without interruption using the last valid configuration cached on disk at `data/config_cache.json`.

2. **Zero-Data-Loss Offline Buffer (`data/offline_buffer/`):**
   Audit reports generated during the network outage are serialized as JSON into `data/offline_buffer/`. As soon as connectivity to `rtms-web` is restored, queued reports are replayed chronologically, synchronized, and cleanly purged from disk.

3. **Log Flood Protection (Anti-Spam & Exponential Backoff):**
   * **Single Initial Notice:** An explicit warning notification is generated at the moment link connectivity drops, signaling fallback to autonomous caching.
   * **Exponential Backoff for Reminders:** Instead of spamming error logs on every retry cycle, the interval between warnings doubles dynamically (5 min, 10 min, 20 min, 40 min, up to a maximum of 4 hours).
   * **Relaxed Disconnected Heartbeats:** Probe retry cadence eases from 15s to 60s when disconnected to avoid socket exhaustion.
   * **Silent Spooling:** Reports spool to disk quietly without log clutter (logged at `DEBUG` level).
