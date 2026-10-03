# RTMS NVD Execution Lifecycle & Database Interaction Specification

This document provides a comprehensive technical breakdown of the actions performed by the RTMS NVD synchronization engine from startup to steady-state execution, along with its precise database interactions across schemas `nvd` and `admin`.

---

## 1. Execution Sequence (Startup to Steady-State Ingestion Loop)

The `rtms-nvd` daemon (`main_rtms_nvd.py`) executes the following sequential stages:

1. **Initialization & Configuration Loading**
   - Resolves application runtime root and parses `rtms-nvd.properties`.
   - Overrides properties with system environment variables (`RTMS_DB_HOST`, etc.).
   
2. **Cryptographic License Verification**
   - Verifies operational entitlement via `license_validator`. Injects active license tier ("PROD" or "DEMO") into memory.

3. **Logging System Configuration**
   - Configures rotating log handlers (file size thresholds and archive retention counts).

4. **Schema Verification & Database Bootstrap (`check_and_bootstrap`)**
   - Initializes core database connectivity via `db.init_db()`.
   - Executes `verify_and_upgrade_schema`:
     - Applies unified DDL scripts.
     - Migrates legacy NVD tables (e.g. `nvd.alerts_config` to `admin.cve_alerts_config`) and provisions missing CPE schema columns.
   - Creates the accelerated cache table `nvd.cve_cache`.

5. **NVD Seed Sequence (Bootstrap)**
   - Checks row count in `nvd.cve`. If empty or uninitialized, triggers the bootstrap routine:
   - **Attempt 1 (Local Compressed SQL Stream)**: Fast streaming ingestion of compressed SQL archives (`rtms_nvd_vulnerabilities_data_sql.gz`) using PostgreSQL bulk `COPY`.
   - **Attempt 2 (Remote NIST Fallback)**: If local seed archives are missing, logs a warning and initiates paginated remote bulk downloads directly via the NIST REST API.

6. **Dynamic Runtime Configuration (`get_dynamic_config`)**
   - Pulls tenant-scoped database parameters (sync cadence, instance UUID, NIST API endpoints). Auto-heals missing defaults and commits them to the database.

7. **Task Scheduler Initialization**
   - Schedules daily cryptographic license verification.
   - Loads configured alert notification targets (`db.load_alerts_configuration`).
   - Dispatches initial incremental synchronization cycle (`incremental_sync`).

8. **Incremental Synchronization Execution (`incremental_sync`)**
   - Calculates synchronization time window based on `MAX(last_modified_date)` of known CVEs.
   - Queries NIST API v2.0 for modified or newly published CVE records.
   - Performs atomic Upsert of CVE definitions and recreates associated CPE matching criteria.
   - Executes asset correlation (`correlate_cpes`) against discovered IT inventory and the Global Watchlist.
   - Dispatches deduplicated alerts across configured webhook/email channels for critical newly impacted assets.
   - **Records Ingestion Telemetry (`nvd.sync_history`)**: Commits execution start/end timestamps, elapsed duration (`duration_ms`), counts of processed CVEs/CPEs, list of CVE IDs, and impacted inventory matches.

9. **Main Daemon Steady-State Loop**
   - Enters infinite monitoring loop sleeping 60 seconds between evaluations.
   - On each wake cycle, performs non-disruptive hot-reloading of dynamic configuration and alert routes without service restart.

---

## 2. Table-by-Table Data Interaction Matrix

### Schema `nvd`

| Table | Retrieved Information | Stored Information |
| :--- | :--- | :--- |
| **`nvd.cve`** | - Evaluates `COUNT(*)` at boot to determine bootstrap requirement.<br>- Retrieves `MAX(last_modified_date)` to define the delta window for incremental syncs. | - Upserts core vulnerability records: `cve_id`, `description`, `cvss_v3_score`, `cvss_v3_severity`, `published_date`, `last_modified_date`. |
| **`nvd.cpe_match`** | - Queried by `admin.vulnerability_view` during `correlate_cpes` to match asset configurations with vulnerable CPE criteria. | - Inserts CPE matching expressions (vendors, products, version bounds).<br>- *Note:* On CVE updates, previous CPE bindings are purged (`DELETE`) before reinsertion. |
| **`nvd.cve_cache`** | - N/A (Maintained for fast prefix matching queries). | - Ensures table and index presence via `db.create_cve_cache_table()`. |
| **`nvd.sync_history`** | - Queried by the Web backend (`/api/nvd/sync-history`) for telemetry displays and audit cards in the UI. | - Inserts execution telemetry after every sync: `tenant_id`, `sync_start`, `sync_end`, `duration_ms`, `cve_count`, `cpe_count`, `status`, `cve_ids`, `impacted_inventory_count`. On failure, records `FAILED` status and `error_message`. |

### Schema `admin`

| Table | Retrieved Information | Stored Information |
| :--- | :--- | :--- |
| **`admin.tenant_infra`** | - Reads tenant-specific NIST API key (`nist_api_key`) to benefit from elevated rate limits. | - Provisions default tenant (`3TS`) or migrates legacy entries. |
| **`admin.nvd_config`** | - Hot-reloads tenant-specific parameters (`WHERE tenant_id = %s`): sync intervals, URLs.<br>- Validates `is_mandatory` flags to enforce required configurations. | - Self-healing: Injects default keys and properties from configuration files if absent. |
| **`admin.cve_alerts_config`** | - Loads active webhook endpoints, destinations, and CVSS thresholds. | - Migrated automatically from legacy schemas. |
| **`admin.cve_alerts`** | - Deduplication lookup: Checks whether `channel_config_id` was already notified for a given `cve_id`. | - Writes notification audit record: `cve_id`, `channel_config_id`, `cve_score`, `trigger_threshold`, `sent_at`. |
| **`admin.tenant_logs`** | - N/A | - Writes warning and error logs upon database anomalies for administrator review. |
| **`admin.product_license`** | - Validates cryptographic signature and license expiration date. | - Initial license storage or update. |
| **`admin.assets`** | - Queried via relational views to cross-reference inventory with NVD criteria. | - Adds missing OS/CPE fingerprint columns during bootstrap if needed. |
| **`admin.asset_vulnerabilities`** | - N/A | - During `correlate_cpes()`, links discovered hosts and software to matched CVEs (`tenant_id`, `asset_id`, `software_id`, `cve_id`). |

---

## 3. Database Hardening & Least-Privilege Isolation

### Direct Database Connection Rationale
Unlike remote `rtms-scanner` probes which communicate exclusively over HTTPS REST APIs, the `rtms-nvd` microservice maintains a direct SQL connection to PostgreSQL. This engineering decision stems from strict performance demands:
1. **Massive Data Volume**: NVD catalogs over **250,000 CVEs** and millions of CPE match rules.
2. **High-Throughput Streaming (Bulk COPY)**: Initial seeding streams compressed data directly into the database engine.
3. **Complex Relational CPE Matching**: Matching software against CPE criteria leverages PostgreSQL native indexes and relational joins. Routing this data through an API layer would cause severe memory and network overhead.

### Security Hardening: `harden_nvd_user.sql`
To enforce Least Privilege and eliminate lateral movement risks, `rtms-nvd` connects using a dedicated role: **`rtms_nvd_user`**.

The hardening script enforces:

```sql
-- 1. Full permissions strictly restricted to schema nvd
GRANT USAGE ON SCHEMA nvd TO rtms_nvd_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nvd TO rtms_nvd_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA nvd TO rtms_nvd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_nvd_user;

-- 2. Restrict Search Path
ALTER ROLE rtms_nvd_user SET search_path TO nvd;

-- 3. Strict Revocation on Sensitive Schemas
REVOKE ALL ON SCHEMA admin FROM rtms_nvd_user;
REVOKE ALL ON SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON SCHEMA public FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA admin FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM rtms_nvd_user;
```

Benefits:
- `rtms_nvd_user` cannot access authentication credentials (`admin.users`, password hashes, MFA secrets) or scan topology (`scanner.*`).
- In the event of a vulnerability in NIST payload processing, the blast radius remains strictly isolated to the public CVE catalog tables in schema `nvd`.
