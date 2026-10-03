# PostgreSQL Installation & Hardening Guide (VPS / Production)

This guide provides a step-by-step procedure to deploy, configure, and secure the PostgreSQL database infrastructure of the RTMS platform on a Linux VPS server (Ubuntu / Debian).

This deployment enforces a strict **PoLP (*Principle of Least Privilege*)** architecture in alignment with **NIS 2** and **ISO 27001** regulatory controls.

---

## 1. System Prerequisites

* **Operating System**: Ubuntu 22.04 LTS / 24.04 LTS or Debian 12
* **PostgreSQL Version**: Version 16 or newer
* **Required Extensions**: `uuid-ossp`, `pg_trgm`
* **Access**: `sudo` / `root` administrative privileges

---

## 2. Step 1: Install PostgreSQL

On the target VPS, update repositories and install PostgreSQL alongside standard contrib extensions:

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib
```

Verify that the PostgreSQL service is active and running:

```bash
sudo systemctl enable --now postgresql
sudo systemctl status postgresql --no-pager
```

---

## 3. Step 2: Database & Schemas Initialization

Switch to the `postgres` system user and create database `rtms_db` and master owner user (`rtms_user`):

```bash
# Define a strong password for the owner account
RTMS_DB_PASS="YOUR_STRONG_PASSWORD_FOR_RTMS_USER"

sudo -u postgres psql <<EOF
-- Create master owner user
CREATE USER rtms_user WITH PASSWORD '$RTMS_DB_PASS';

-- Create database
CREATE DATABASE rtms_db OWNER rtms_user;
EOF
```

Enable required extensions and create the 3 segregated schemas:

```bash
sudo -u postgres psql -d rtms_db <<EOF
-- UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;

-- pg_trgm extension for full-text search and trigram similarity
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA public;

-- Create the 3 business schemas owned by rtms_user
CREATE SCHEMA IF NOT EXISTS admin AUTHORIZATION rtms_user;
CREATE SCHEMA IF NOT EXISTS nvd AUTHORIZATION rtms_user;
CREATE SCHEMA IF NOT EXISTS scanner AUTHORIZATION rtms_user;
EOF
```

---

## 4. Step 3: Enforce RBAC Hardening (Least Privilege)

To ensure that a compromised probe or microservice cannot jeopardize the entire database, 3 dedicated service roles are provisioned with compartmentalized privileges:

1. **`rtms_nvd_user`**: NVD Synchronizer (Read/Write on `nvd`, configuration and heartbeat on `admin`, **zero access** to `scanner`).
2. **`rtms_scanner_user`**: Scanning engine (Read/Write on `scanner`, asset insertion on `admin`, **zero access** to `nvd`).
3. **`rtms_web_user`**: Web Backend / UI (Read/Write on `admin` and `scanner`, **strict read-only** on `nvd`).

### Running the Hardening Script:

Define individual service passwords and execute the provisioning block:

```bash
NVD_PASS="SECURE_PASSWORD_NVD"
SCANNER_PASS="SECURE_PASSWORD_SCANNER"
WEB_PASS="SECURE_PASSWORD_WEB"

sudo -u postgres psql -d rtms_db <<EOF
-- 1. Create service roles
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rtms_nvd_user') THEN
        CREATE ROLE rtms_nvd_user WITH LOGIN PASSWORD '$NVD_PASS';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rtms_scanner_user') THEN
        CREATE ROLE rtms_scanner_user WITH LOGIN PASSWORD '$SCANNER_PASS';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rtms_web_user') THEN
        CREATE ROLE rtms_web_user WITH LOGIN PASSWORD '$WEB_PASS';
    END IF;
END
\$\$;

-- 2. Connection and search_paths
GRANT CONNECT ON DATABASE rtms_db TO rtms_nvd_user, rtms_scanner_user, rtms_web_user;

ALTER ROLE rtms_nvd_user SET search_path TO nvd, admin, public;
ALTER ROLE rtms_scanner_user SET search_path TO scanner, admin, public;
ALTER ROLE rtms_web_user SET search_path TO admin, scanner, nvd, public;

-- Lock down public schema
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM rtms_nvd_user, rtms_scanner_user, rtms_web_user;

-- 3. RTMS-NVD Permissions (nvd_user)
REVOKE ALL ON SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA scanner FROM rtms_nvd_user;

GRANT USAGE ON SCHEMA nvd TO rtms_nvd_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nvd TO rtms_nvd_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA nvd TO rtms_nvd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_nvd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rtms_nvd_user;

GRANT USAGE ON SCHEMA admin TO rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA admin FROM rtms_nvd_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA admin FROM rtms_nvd_user;

-- 4. RTMS-SCANNER Permissions (scanner_user)
REVOKE ALL ON SCHEMA nvd FROM rtms_scanner_user;
REVOKE ALL ON ALL TABLES IN SCHEMA nvd FROM rtms_scanner_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA nvd FROM rtms_scanner_user;

GRANT USAGE ON SCHEMA scanner TO rtms_scanner_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA scanner TO rtms_scanner_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA scanner TO rtms_scanner_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA scanner GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_scanner_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA scanner GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rtms_scanner_user;

GRANT USAGE ON SCHEMA admin TO rtms_scanner_user;
REVOKE ALL ON ALL TABLES IN SCHEMA admin FROM rtms_scanner_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA admin FROM rtms_scanner_user;

-- 5. RTMS-WEB Permissions (web_user)
GRANT USAGE ON SCHEMA admin, scanner, nvd TO rtms_web_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA admin TO rtms_web_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA scanner TO rtms_web_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA admin TO rtms_web_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA scanner TO rtms_web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA admin GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA scanner GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_web_user;

-- NVD strictly READ-ONLY for Web UI
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA nvd FROM rtms_web_user;
GRANT SELECT ON ALL TABLES IN SCHEMA nvd TO rtms_web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT SELECT ON TABLES TO rtms_web_user;
EOF
```

> **Tip:** You can also apply or re-verify these permissions at any time using the installer utility:
> ```bash
> python database/manage_schemas.py setup-rbac
> ```

---

## 5. Step 4: System-Level PostgreSQL Hardening

### A. Network Binding Restrictions (`postgresql.conf`)

By default on a VPS running services locally or through a WireGuard VPN tunnel, PostgreSQL must **never** listen on `0.0.0.0` unrestricted.

Edit the primary configuration file (e.g., `/etc/postgresql/16/main/postgresql.conf`):

```ini
# Listen strictly on localhost (if all RTMS services run locally)
listen_addresses = 'localhost'

# Recommended performance and security directives
password_encryption = scram-sha-256
ssl = on
log_connections = on
log_disconnections = on
log_line_prefix = '%m [%p] %q%u@%d '
```

### B. Client Authentication Restrictions (`pg_hba.conf`)

Edit `/etc/postgresql/16/main/pg_hba.conf` to enforce `scram-sha-256`:

```text
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     scram-sha-256
host    rtms_db         rtms_web_user   127.0.0.1/32            scram-sha-256
host    rtms_db         rtms_nvd_user   127.0.0.1/32            scram-sha-256
host    rtms_db         rtms_scanner_user 127.0.0.1/32          scram-sha-256
host    rtms_db         rtms_user       127.0.0.1/32            scram-sha-256
```

Reload PostgreSQL configuration:

```bash
sudo systemctl restart postgresql
```

---

## 6. Step 5: RTMS Service Configuration

In directory `/opt/rtms/config/`:

### 1. Web Backend (`.env`)
```ini
DATABASE_URL=postgresql+psycopg://rtms_web_user:YOUR_PASSWORD@localhost:5432/rtms_db
RTMS_DB_HOST=localhost
RTMS_DB_PORT=5432
RTMS_DB_NAME=rtms_db
RTMS_DB_USER=rtms_web_user
RTMS_POSTGRES_PASSWORD=YOUR_PASSWORD
```

### 2. NVD Service (`scanner.properties` or environment variables)
```ini
db.host=localhost
db.port=5432
db.name=rtms_db
db.user=rtms_nvd_user
db.password=YOUR_PASSWORD
```

### 3. Scanner Service
* **REST API Mode (Recommended for production)**: The scanner communicates over HTTPS with the backend via `RTMS_SERVER_URL` and `RTMS_SCANNER_TOKEN`.
* **Direct DB Mode (if enabled)**: Connects using `db.user=rtms_scanner_user`.

---

## 7. Step 6: Security Verification Tests

To verify that isolation boundaries are active:

### Test 1: Confirm `rtms-scanner` cannot query `nvd`
```bash
PGPASSWORD="$SCANNER_PASS" psql -h localhost -U rtms_scanner_user -d rtms_db -c "SELECT COUNT(*) FROM nvd.cve;"
```
> **Expected output:** `ERROR: permission denied for schema nvd` ✅

### Test 2: Confirm `rtms-web` cannot mutate NVD data (Read-Only)
```bash
PGPASSWORD="$WEB_PASS" psql -h localhost -U rtms_web_user -d rtms_db -c "DELETE FROM nvd.cve;"
```
> **Expected output:** `ERROR: permission denied for table cve` ✅

### Test 3: Confirm `rtms-nvd` cannot read admin user accounts
```bash
PGPASSWORD="$NVD_PASS" psql -h localhost -U rtms_nvd_user -d rtms_db -c "SELECT * FROM admin.users;"
```
> **Expected output:** `ERROR: permission denied for table users` ✅

### Test 4: Confirm `rtms-web` can query CVEs
```bash
PGPASSWORD="$WEB_PASS" psql -h localhost -U rtms_web_user -d rtms_db -c "SELECT COUNT(*) FROM nvd.cve;"
```
> **Expected output:** Success (returns row count) ✅

---

## 8. Backup & Disaster Recovery

Thanks to schema segregation, backup jobs can be tailored by criticality and volume:

```bash
# Application and scan inventory backup (lightweight)
pg_dump -U rtms_user -d rtms_db -n admin -n scanner -F c -b -v -f rtms_app_backup.dump

# NVD CVE repository backup (~1.5 GB)
pg_dump -U rtms_user -d rtms_db -n nvd -F c -b -v -f rtms_nvd_backup.dump
```
