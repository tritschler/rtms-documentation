# RTMS-NVD Startup Sequence

This document describes the initialization and startup sequence of the `rtms-nvd` component (`main_rtms_nvd.py`).

---

## 1. Configuration Loading & Validation
At boot, the daemon reads `rtms-nvd.properties` from its working directory:
* **Missing File & Environment Fallback:** If absent, the daemon initializes empty configuration and falls back to environment variables (`RTMS_DB_HOST`, `RTMS_DB_PORT`, `RTMS_DB_USER`, `RTMS_DB_NAME`). If any of these 4 variables is missing, startup halts (`sys.exit(1)`).
* **Whitelist Validation:** Active keys are validated against a strict property whitelist (`VALID_PROPERTIES`). Unknown keys (e.g. typos or injection attempts) trigger log warnings and are rejected.
* **Environment Variable Precedence:** Environment variables `RTMS_DB_*` take precedence over file properties (enabling 12-factor cloud/container deployments).

---

## 2. License Validation
Before establishing database connectivity, the daemon executes `license_validator.enforce_license_state`:
* Prioritizes local file `license.key`.
* If unreadable, queries `admin.product_license` for the latest synchronized license payload.
* Verifies cryptographic signature (RSA/Ed25519), expiration date, and hardware footprint.
* If missing or invalid, falls back gracefully to **DEMO mode** rather than crashing. DEMO mode imposes functional caps (e.g. maximum of 5 monitored hosts).

---

## 3. Logging & Execution Context
* Log rotation is initialized (`log.max_mb` size thresholds and `log.backups` file retention).
* Resolves deployment topology: `saas` (central multi-tenant VPS) vs `onprem` (local client appliance).

---

## 4. Database Schema Initialization
Calls `db.init_db` to ensure schema boundaries (`nvd`, `admin`, `scanner`) exist, then invokes `nvd_db_upgrades.verify_and_upgrade_schema` to apply schema updates and missing columns.

---

## 5. Vulnerability Catalog Bootstrap
The engine checks for a local seed archive `rtms_nvd_vulnerabilities_data_sql.gz`:
* **Local Snapshot Import (Fast Path):** Uses PostgreSQL native `COPY` into staging memory tables (`temp_cve`, `temp_cpe_match`), followed by `INSERT ... ON CONFLICT DO NOTHING`. Upon completion, renames the archive to `.processed`.
* **API Ingestion (Fallback):** If the database has 0 rows in `nvd.cve`, triggers an asynchronous full bootstrap download from NIST API v2.0 with backoff and rate-limiting.

---

## 6. Dynamic Configuration (Self-Healing & Hot Reload)
Queries runtime parameters from `admin.nvd_config` via `get_dynamic_config`:
* **Auto-Healing:** If keys are absent, inserts default entries into the database.
* **Hot-Reload:** In-memory values are overridden by database entries, allowing administrators to modify polling intervals via the Web UI without restarting the daemon.

---

## 7. Background Task Scheduler
Leverages `BackgroundScheduler` to manage asynchronous jobs:
1. **Daily License Audit**: Verifies license expiration and validity.
2. **Configuration Refresh**: Periodically checks for modified webhook alert rules in `admin.cve_alerts_config`.
3. **NVD Incremental Sync**: Executes `incremental_sync` according to `nvd.fetch.minutes`. At the conclusion of each sync, runs inventory correlation (`correlate_cpes`) and dispatches targeted alerts (`dispatch_inventory_alerts`).

The primary thread enters a sleep loop (`while True: time.sleep(1)`) maintaining scheduler persistence.
