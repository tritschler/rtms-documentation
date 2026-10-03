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

---

## 5. Résilience et Mode Hors-Ligne en Mode API Découplé

En mode API Découplé (`RTMS_SERVER_URL`), si le serveur backend central devient injoignable (coupure réseau, maintenance, panne temporaire) :

1. **Continuité de scan & Cache de configuration local** :
   Le scanner continue d'auditer le réseau sans interruption en s'appuyant sur la dernière configuration valide mise en cache dans `data/config_cache.json`.

2. **Tampon hors-ligne zéro perte (`data/offline_buffer/`)** :
   Les rapports de scans générés pendant la panne sont sérialisés au format JSON dans `data/offline_buffer/`. Dès que le serveur RTMS est de nouveau disponible, tous les rapports en attente sont automatiquement rejoués et synchronisés dans l'ordre chronologique, puis purgés.

3. **Protection contre la pollution des logs (Anti-Spam & Backoff Exponentiel)** :
   * **Alerte initiale unique** : Une notification d'avertissement est émise au moment précis où la liaison est perdue pour signaler le basculement en mode autonome.
   * **Backoff exponentiel des rappels** : Au lieu d'émettre des avertissements répétitifs à chaque requête, l'intervalle entre deux rappels d'indisponibilité double progressivement (5 min, 10 min, 20 min, 40 min... jusqu'à 4 heures maximum).
   * **Espacement des heartbeats déconnectés** : La cadence des tentatives de vérification passe automatiquement de 15s à 60s pour éliminer la saturation des sockets.
   * **Bufferisation silencieuse** : Les rapports de scans s'accumulent sur le disque sans polluer les journaux d'erreurs (niveau `DEBUG`).