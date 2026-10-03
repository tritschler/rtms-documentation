# Data Model: RTMS-NVD

This document describes the database tables utilized by the `rtms-nvd` microservice to store, synchronize, and query vulnerability data (CVE) ingested from the NIST National Vulnerability Database.

---

## Schema `nvd`

This schema contains raw security definitions and vulnerability catalogs.

### 1. `nvd.cve`
Primary table storing core Common Vulnerabilities and Exposures (CVE) definitions:
- **`cve_id`** (`VARCHAR(50)`, Primary Key): Unique CVE identifier (e.g., `CVE-2021-44228`).
- **`description`** (`TEXT`): Detailed text description of the vulnerability.
- **`cvss_v3_score`** (`NUMERIC`): CVSS v3 base severity score.
- **`cvss_v3_severity`** (`VARCHAR(50)`): CVSS v3 severity rating (e.g., `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **`published_date`** (`TIMESTAMP WITH TIME ZONE`): Initial CVE publication date.
- **`last_modified_date`** (`TIMESTAMP WITH TIME ZONE`): Date of latest modification by NIST.

### 2. `nvd.cpe_match`
Stores CPE (Common Platform Enumeration) criteria linked to each CVE, matching vulnerable software configurations (vendors, products, and versions):
- **`id`** (`SERIAL`, Primary Key): Match criterion unique identifier.
- **`cve_id`** (`VARCHAR(50)`, Foreign Key to `nvd.cve`): Associated CVE ID.
- **`vulnerable`** (`BOOLEAN`): Indicates whether this criterion represents an exploitably vulnerable configuration (`true`) or a required dependency.
- **`criteria`** (`TEXT`): Full or partial CPE URI string (e.g., `cpe:2.3:a:apache:log4j:...`).
- **`version_start_including`** (`VARCHAR(100)`): Minimum version bound (inclusive).
- **`version_start_excluding`** (`VARCHAR(100)`): Minimum version bound (exclusive).
- **`version_end_including`** (`VARCHAR(100)`): Maximum version bound (inclusive).
- **`version_end_excluding`** (`VARCHAR(100)`): Maximum version bound (exclusive).

### 3. `nvd.cve_cache`
High-speed cache table accelerating CPE prefix matching during inventory audits:
- **`cpe_prefix`** (`VARCHAR(255)`, Primary Key): Cached CPE identifier prefix.
- **`cve_data`** (`JSONB`): Pre-compiled JSON payload of corresponding CVEs.
- **`last_sync`** (`TIMESTAMP WITH TIME ZONE`): Timestamp of the last sync for this prefix.
- **`last_modified_cve`** (`TIMESTAMP WITH TIME ZONE`): Timestamp of the most recent CVE change in this cache partition.

### 4. `nvd.sync_history`
Audit history and operational telemetry tracking each NIST NVD sync execution:
- **`id`** (`SERIAL`, Primary Key): Run identifier.
- **`tenant_id`** (`VARCHAR(50)`): Tenant ID (defaults to `3TS`).
- **`sync_start`** (`TIMESTAMP WITH TIME ZONE`): Sync start timestamp.
- **`sync_end`** (`TIMESTAMP WITH TIME ZONE`): Sync completion timestamp.
- **`duration_ms`** (`INTEGER`): Total run duration in milliseconds.
- **`cve_count`** (`INTEGER`): Number of CVEs inserted or updated.
- **`cpe_count`** (`INTEGER`): Number of CPE match records processed.
- **`status`** (`VARCHAR(20)`): Execution status (`RUNNING`, `SUCCESS`, `FAILED`).
- **`error_message`** (`TEXT`): Error details upon ingestion failure.
- **`cve_ids`** (`TEXT[]`): Array of CVE identifiers downloaded during the cycle (capped at 1,000 IDs for inspection).
- **`impacted_inventory_count`** (`INTEGER`): Number of vulnerabilities correlated with active inventory or the Global Watchlist.
- *Index*: `idx_sync_history_start ON nvd.sync_history (sync_start DESC)`

---

## Schema `admin`

This schema contains configuration and logging parameters for the NVD ingestion process.

### 5. `admin.nvd_config`
Dynamic operational parameters for NVD sync execution (intervals, API keys, batch sizes):
- **`tenant_id`** (`VARCHAR(50)`): Tenant identifier (`SYSTEM` for global routines).
- **`config_key`** (`VARCHAR(50)`): Configuration property key (e.g., `NVD_SYNC_INTERVAL_MINUTES`).
- **`config_value`** (`VARCHAR(255)`): Configuration property value.
- *Primary Key*: `(tenant_id, config_key)`

### 6. `admin.tenant_logs`
Database logging table capturing NVD background job executions (starts, successes, warnings, errors):
- **`id`** (`SERIAL`, Primary Key): Log entry identifier.
- **`tenant_id`** (`VARCHAR(50)`): Associated tenant ID (or `SYSTEM`).
- **`log_level`** (`VARCHAR`): Log severity (`INFO`, `ERROR`, `WARNING`).
- **`message`** (`TEXT`): Detailed message or stack trace.
- **`created_at`** (`TIMESTAMP WITH TIME ZONE`): Log creation timestamp.

### 7. `admin.cve_alerts_config`
The NVD microservice monitors this table to hot-reload alert channels when newly ingested CVEs trigger notification rules:
- **`id`** (`SERIAL`, Primary Key): Alert rule identifier.
- **`tenant_id`** (`VARCHAR(50)`, Foreign Key): Associated tenant ID.
- **`channel_type`** (`VARCHAR(20)`): Channel medium (e.g., `webhook`, `email`).
- **`channel_name`** (`VARCHAR(100)`): Friendly name of the notification target.
- **`destination_url`** (`TEXT`): Webhook endpoint URL or target recipient.
- **`trigger_threshold`** (`NUMERIC`): Minimum CVSS severity score required to fire an alert.
- **`is_active`** (`BOOLEAN`): Activation toggle for the alert rule.
- **`created_at`** (`TIMESTAMP WITH TIME ZONE`): Rule creation timestamp.
