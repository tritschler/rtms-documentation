# Technical Documentation: Automatic Session Timeout (JWT)

## Overview
This document describes the implementation of the automatic session timeout feature in the RTMS application. The feature ensures that user sessions are automatically invalidated after a period of inactivity, enhancing the security of the application.

## Backend Implementation (FastAPI)
The backend is responsible for generating JSON Web Tokens (JWT) upon successful authentication. 
The token includes an `exp` (expiration time) claim, which dictates how long the token is valid.

**File:** `backend/main.py`
- **Library used:** `PyJWT`
- **Expiration Logic:**
  - Administrators (`role == 'admin'`): 15 minutes.
  - Normal Users: 30 minutes.
- **Response:** The `/api/login` endpoint returns the generated `access_token`, the user object, and an explicitly calculated `expires_at` timestamp (UNIX epoch). 

*Code Snippet:*
```python
import jwt
from datetime import datetime, timedelta, timezone

# Inside login function:
exp_minutes = 15 if user_dict.get('role') == 'admin' else 30
expire = datetime.now(timezone.utc) + timedelta(minutes=exp_minutes)
to_encode = {"sub": request.username, "exp": expire}
encoded_jwt = jwt.encode(to_encode, "super-secret-key-for-rtms", algorithm="HS256")

return {
    "access_token": encoded_jwt,
    "token_type": "bearer",
    "user": user_dict,
    "expires_at": int(expire.timestamp())
}
```

## Frontend Implementation (React)
The frontend receives the `expires_at` timestamp and proactively manages the user session in the browser. 

**File:** `frontend/src/App.tsx`
- **State Management:** The application maintains the `expiresAt` state alongside the authenticated `user` state.
- **Timeout Logic:** A `useEffect` hook monitors the `user` and `expiresAt` states. It calculates the remaining time (in milliseconds) until the session expires.
  - If the time has already elapsed, the `handleLogout()` function is called immediately.
  - If time remains, a `setTimeout` is initialized to automatically trigger the `handleLogout()` function exactly when the token expires.

*Code Snippet:*
```tsx
  useEffect(() => {
    if (user && expiresAt) {
      const timeUntilExpiry = expiresAt * 1000 - Date.now();
      if (timeUntilExpiry <= 0) {
        handleLogout();
      } else {
        const timer = setTimeout(() => {
          handleLogout();
        }, timeUntilExpiry);
        return () => clearTimeout(timer); // Cleanup on unmount or state change
      }
    }
  }, [user, expiresAt]);
```

## Authentication Providers
The RTMS backend utilizes a Strategy Pattern to support multiple authentication providers, configured dynamically via the web interface (`admin.system_config`) or the `RTMS_AUTH_PROVIDER` environment variable. An authentication factory instantiates the corresponding strategy at runtime:

- **Local (`local`)**: The default authentication strategy. It authenticates users against the `admin.users` database table by verifying the provided password against a stored bcrypt hash. Supports mandatory NIS 2 MFA enrollment.
- **LDAP (`ldap`)**: Authenticates users against a corporate active directory using a simple bind. It queries the configured LDAP server, binds with the user credentials, and performs Just-In-Time (JIT) provisioning into `admin.users` with `password_hash = 'ldap_managed'`. If the LDAP server is unreachable, it seamlessly cascades to local accounts for emergency access.
- **SSO / OIDC (`oidc`)**: Enterprise Single Sign-On using OpenID Connect (Keycloak, Microsoft Entra ID, Okta). Handles discovery (`/.well-known/openid-configuration`), secure authorization code exchange, JIT user provisioning with `password_hash = 'sso_managed'`, and full delegation of multi-factor authentication (MFA/TOTP). Provides a dedicated **Break-Glass** local login fallback mode for administrator resilience.

Regardless of the active provider, successful authentications generate the standard JWT session token, record an entry in the `admin.login_audit` table, and update the `last_login` timestamp for the user.

## Data Lifecycle & Telemetry Purge vs. Factory Reset

RTMS strictly separates operational scan telemetry from persistent system configurations:

* **Tenant Telemetry & Vulnerability Purge (`admin.purge_tenant_data`, `admin.purge_tenant_vulnerabilities`)**:
  * Removes discovered host assets, open ports, software inventory, and CVE findings for a given tenant.
  * **100% Preserved:** iTop CMDB configurations (`cmdb_*`), SSO / Keycloak settings (`oidc_*`), LDAP directory bind settings, SMTP alert policies, user profiles (`admin.users`), and product licenses.
* **Factory Reset (`clean_schemas.sql` / `clean_app_data.sql`)**:
  * Empties all tables in `admin` and `scanner` schemas for a clean Setup Wizard re-initialization.

## Security Considerations & Role-Based Access Control (RBAC)
- The session timeout relies on the backend issuing valid JWTs with an expiration claim (`exp`).
- The frontend timer acts as a proactive UX measure, forcing a logout when the token is known to have expired.
- **Granular 4-Role RBAC Model**: Authorization is enforced on every API route via FastAPI dependency injection:
  - `verify_admin`: Reserved for system administrators (user provisioning, system config, licenses, service lifecycle, orphan purge).
  - `verify_security_analyst_or_admin`: Dedicated to SOC analysts and administrators (CVE risk triage & justification, security findings declaration & assignment, alert management, verification scans).
  - `verify_operator_or_admin`: Dedicated to network/scanner operators and administrators (scanner restart `RESTART`, agent token revocation/reenrollment, subnet management, asset deletion).
  - `verify_can_operate`: Allows operational read-write (`admin`, `security_analyst`, `operator`) for asset metadata editing and software inventory tracking.
  - `verify_can_scan`: Allows triggering network discovery scans (`admin`, `security_analyst`, `operator`).
  - `verify_can_view_audit`: Restricts audit log inspection (`/api/audit/*`) to compliance auditors (`viewer`), SOC analysts (`security_analyst`), and `admin`. Operators are explicitly denied (403) to prevent tampering.
- **Root Admin Immobility**: The seeded `admin` account is hard-protected against deactivation or role downgrades.
- Complete architectural specifications are available in the [Modèle RBAC (Permissions)](../../architecture/rbac.md) document.

## Database Schema Reset (Factory Reset)
This section explains the application's behavior when selectively deleting database schemas. 

If the `admin` and `scanner` schemas are deleted from the database but the `nvd` schema is kept intact, the application handles it seamlessly without crashing. This effectively acts as a safe "factory reset" for operational data while avoiding the need to re-download the massive NVD vulnerability dataset.

### Startup Behavior
Upon restarting the `rtms-nvd` or `rtms-scanner` components, the following occurs:

1. **Automatic Schema Recreation**: `rtms_commons.db_client.init_db()` executes `CREATE SCHEMA IF NOT EXISTS` for both `admin` and `scanner` schemas. It automatically detects they are missing and creates empty schemas.
2. **Table Generation**: The application executes the core DDL scripts (`ADMIN_DDL`, `TABLES_DDL`, etc.). Since these use `CREATE TABLE IF NOT EXISTS`, all required tables within `admin` and `scanner` are cleanly recreated from scratch.
3. **Data Bootstrapping**: The default system data is automatically re-inserted (e.g., the default `3TS` tenant, the default `admin` user, and default scanner configurations).
4. **License Restoration**: The `LicenseValidator` module reads the physical `license.key` file from the disk and synchronizes it, safely re-inserting the license payload into the newly recreated `admin.product_license` table.
5. **NVD Sync Continuity**: Because the `nvd` schema remains intact, the vulnerability tables (`nvd.cve`, `nvd.cpe_match`, etc.) are preserved. When the NVD incremental sync scheduler runs, it queries `SELECT MAX(last_modified_date) FROM nvd.cve;` to find the newest known CVE. It then successfully fetches only the newest updates from the NIST API seamlessly.

### Consequences
- **Data Loss**: All operational data stored in the `admin` and `scanner` schemas is completely lost. This includes scanned networks, discovered assets, matched asset vulnerabilities, custom users, and configured alert webhook destinations.
- **Continuity**: The application boots normally with a fresh state, retaining full vulnerability data continuity without requiring hours of data ingestion.

---

## Network Scan Archive System (NIS2 Compliance Snapshots)

To fulfill NIS2 Article 21 requirements regarding configuration management and historical verification of network perimeters, RTMS includes a dedicated **Scan Archive System**.

### Database Storage (`scanner.scan_archives`)
- Stores complete immutable snapshots of network discovery scans for a specific scanner and subnet.
- **Data structure**:
  - `id`: UUID primary key.
  - `scanner_id`: Scanner service identifier (`admin.service_registry.service_name`).
  - `subnet`: Network CIDR (e.g. `192.168.0.0/24`).
  - `scan_id`: Optional link to the specific `scanner.scans` execution.
  - `snapshot_data`: Comprehensive JSONB payload containing:
    - Complete host inventory (`ip_address`, `mac_address`, `hostname`, `vendor`, `status`, `last_seen`).
    - Open TCP/UDP ports and service banners for each host.
    - Software inventory installed on discovered hosts.
  - `host_count`, `online_count`, `service_count`: Pre-aggregated counters for fast reporting.
  - `label` & `notes`: User-defined audit labels (e.g. *"Baseline Pre-Audit NIS2"*).
  - `created_at`: Exact UTC creation timestamp.

### REST API Endpoints (`backend/main.py`)
- `GET /api/archives/summary`: High-level metrics (total archive count, covered subnets, active scanners, latest timestamp).
- `GET /api/archives`: List filtered archives by scanner or subnet with search support.
- `POST /api/scanners/{service_name}/archive-latest`: One-click snapshot of the latest scan and live assets for a scanner.
- `POST /api/archives`: Manual snapshot creation with custom label and notes.
- `GET /api/archives/{id}`: Detailed inspection of archived host assets and services.
- `GET /api/archives/{id}/export`: Download snapshot as a standalone `.json` file attachment.
- `GET /api/archives/{id}/diff`: Real-time delta comparison between the archive snapshot and current live network state (computes `added`, `removed`, `changed`, and `unchanged` hosts).
- `DELETE /api/archives/{id}`: Hard deletion of an archive snapshot.

---

## SNMP Discovery & Gateway Probing

RTMS incorporates an asynchronous, non-blocking SNMP engine (`rtms-scanner/snmp_discovery.py`) based on PySNMP to interrogate network infrastructure:

1. **System Identity Probe**:
   - Queries standard MIB-II OIDs: `sysDescr` (`.1.3.6.1.2.1.1.1.0`), `sysName` (`.1.3.6.1.2.1.1.5.0`), and `sysObjectID` (`.1.3.6.1.2.1.1.2.0`).
   - Identifies router vendors (Cisco, Fortinet, pfSense, Linux/Net-SNMP) without intrusive scanning.
2. **Remote ARP Cache Discovery**:
   - Walks RFC 1213 `ipNetToMediaTable` (`.1.3.6.1.2.1.4.22.1.2` and `.4`) to discover silent hosts and workstations that ignore ICMP pings behind local firewalls.
3. **Custom SNMP Target Support**:
   - Scanners can be configured with a custom SNMP Target IP (`snmp_target_ip`) and community string (`snmp_community`) in `admin.service_registry`.
   - Allows network administrators to query dedicated SNMP bastions, L3 switches, or Linux mock servers (running `net-snmp`) when the perimeter modem does not expose SNMP.

---

## ARP Spoofing & Network Anomaly Detection

RTMS actively detects layer-2 and layer-3 network attacks through a 3-tier anomaly detection engine implemented in `rtms-scanner/main_scanner.py`:

1. **Gateway Impersonation Detection (`ARP_SPOOFING_GATEWAY`) - Severity: CRITICAL**:
   - **Trigger**: The MAC address of any configured or discovered gateway suddenly changes compared to historical state in `global_known_ips`.
   - **Threat**: Indicates a rogue host forging ARP replies to redirect LAN traffic through itself (Man-In-The-Middle / credential theft).
2. **SNMP vs. Wire Cross-Validation (`ARP_POISONING_DETECTED`) - Severity: CRITICAL**:
   - **Trigger**: A MAC address captured on the local wire for an IP directly contradicts the authoritative hardware ARP table returned by the switch/router via SNMP.
   - **Threat**: Confirms active ARP cache poisoning on the network segment.
3. **Host IP/MAC Conflict Detection (`IP_MAC_CONFLICT`) - Severity: WARNING**:
   - **Trigger**: A known non-gateway IP begins responding with a different MAC address without DHCP release.
   - **Threat**: Detects conflicting static IP configurations or host-level spoofing.

Alerts are routed through `rtms_commons.alerts.dispatch_alert()` to the database (`scanner.alerts`), local logs, and configured external channels (email, Teams, Slack, Splunk). In the frontend, security alerts display dedicated badges and icons (`ShieldAlert`).

---

## Subnet Management & Lifecycle Detection

The RTMS web interface and backend provide granular subnet status determination, custom naming, and intelligent collapsible views to enhance operator readability on multi-VLAN networks.

### 1. Subnet Lifecycle Determination (Connected vs. Inactive vs. Disconnected)
A subnet's operational status is determined via two cascading tiers:

* **Tier 1: Physical Interface Presence ("Non connecté" / Disconnected)**
  - When the scanner starts or checks in (`check_env()`), it enumerates local active network interfaces (`_get_network_details()`).
  - Active CIDRs are published to `admin.service_registry.subnet`.
  - If a subnet known in the inventory has no corresponding active interface on the scanner host, the scanner cannot perform Layer 2 ARP discovery.
  - The backend assigns `subnet_active = false` and `is_up = false` to all hosts on that subnet.
  - The frontend classifies the subnet as **Non connecté** (`isSubnetConnected = false`).
* **Tier 2: Host Availability ("Inactif / Hors ligne" / Inactive)**
  - If the scanner has a valid physical interface on the subnet (`isSubnetConnected = true`), periodic ARP sweeps and host probes are executed.
  - If at least one host responds, the subnet is marked **En ligne** (`isSubnetOnline = true`, green badge).
  - If the sweep completes but zero hosts respond (or all previously discovered hosts are unreachable), `onlineCount == 0`.
  - The frontend classifies the subnet as **Inactif** (`isSubnetOnline = false`).

### 2. Default Collapsed State for Offline / Inactive Subnets
- In `frontend/src/pages/AssetManagement.tsx`, subnets that are disconnected or inactive (`!isSubnetConnected || !isSubnetOnline`) are **collapsed by default** into a single compact header line showing their status badge, host count, and alerts.
- Active subnets with online hosts remain expanded by default.
- Operators can expand or collapse any subnet with a single click on its header line or corresponding Quick Subnet Pill.

### 3. Custom Subnet Naming (`admin.subnet_names`)
- Operators with Administrator privileges can assign friendly custom names (e.g., *DMZ*, *Production*, *Guest Wi-Fi*) to any CIDR block.
- **Data Persistence**: Stored in `admin.subnet_names (subnet_cidr CIDR PRIMARY KEY, name VARCHAR(150), description TEXT, updated_at TIMESTAMPTZ)` and synchronized into `scanner.networks.name`.
- **API Endpoints**:
  - `GET /api/subnets/names`: Fetches custom names mapping.
  - `POST /api/subnets/name`: Upserts custom name with authenticated admin verification (`Authorization: Bearer <token>`).
- Custom names are rendered alongside the CIDR in subnet headers and Quick Subnet navigation pills.

### 4. Subnet MAC Whitelist (`admin.subnet_mac_whitelist`)
To eliminate alert fatigue and prevent false-positive notifications caused by legitimate recurring devices (e.g. IoT appliances, printers, embedded test benches, maintenance laptops), RTMS supports configuring an authorized MAC address whitelist on a per-subnet basis.

#### Data Persistence & Schema
Stored in PostgreSQL table `admin.subnet_mac_whitelist`:
- `id`: Auto-incrementing primary key.
- `subnet_cidr`: Target network CIDR (`CIDR NOT NULL`).
- `mac_address`: Normalized uppercase MAC address (`VARCHAR(17) NOT NULL`).
- `label`: Optional description or rationale (`VARCHAR(150)`).
- `created_by`: Username of the administrator who registered the entry.
- `created_at` / `updated_at`: Audit timestamps.
- `CONSTRAINT uq_subnet_mac UNIQUE (subnet_cidr, mac_address)`: Ensures idempotency and prevents duplicate entries for the same subnet and MAC.

#### REST API Endpoints (`backend/main.py`)
- `GET /api/settings/subnets/mac-whitelist/counts`: Returns a key-value dictionary mapping subnet CIDRs to the count of whitelisted MAC addresses.
- `GET /api/settings/subnets/{subnet_cidr}/mac-whitelist`: Retrieves all whitelisted MAC addresses, labels, and audit metadata for a given subnet.
- `POST /api/settings/subnets/mac-whitelist`: Validates the CIDR and MAC format, upserts the whitelist entry, and writes an audit log entry (`SUBNET_MAC_WHITELIST_ADDED`). Requires administrator privileges.
- `DELETE /api/settings/subnets/mac-whitelist/{item_id}`: Removes an entry by ID and records an audit log (`SUBNET_MAC_WHITELIST_REMOVED`). Requires administrator privileges.

#### User Interface Workflows
1. **Scanner Configuration (`ScannerConfiguration.tsx`)**:
   - The Network Media & Scanner Interfaces table displays a shield badge showing the number of whitelisted MACs for each active subnet.
   - Clicking the whitelist badge/icon opens a modal dialog allowing operators to:
     - Review all whitelisted MACs for that CIDR, including labels, author, and registration dates.
     - Add new MAC addresses with optional labels.
     - Remove obsolete or revoked whitelist entries with one click.
2. **Security Alerts Quick Action (`SecurityAlerts.tsx`)**:
   - On active (unresolved) security incidents (such as `NEW_HOST` or unknown device alerts), a **"Whitelist MAC"** button (`ShieldCheck`) appears next to the resolve button.
   - Clicking it automatically extracts the MAC address, suggests the corresponding `/24` subnet CIDR based on the host's IP address, registers the entry in `admin.subnet_mac_whitelist`, and immediately marks the alert as `RESOLVED`.

#### Scanner Engine Enforcement (`rtms-scanner/main_scanner.py`)
- Loaded dynamically via `rtms_commons.db_client.load_subnet_mac_whitelist(config_db)` and refreshed every scan loop.
- When an IP is discovered on a subnet context (`ctx_target`), its physical MAC address is matched against `subnet_mac_whitelist[ctx_target]`.
- If matched:
  - Suppresses the `NEW_HOST` alert trigger.
  - Suppresses unknown device and missing hostname warnings in scanner logs.
  - Sets hostname fallback to `"Whitelisted-Device"` in `global_known_macs` if DNS resolution returns empty.
  - Logs a debug trace: `[MAC WHITELIST] Host <IP> (MAC: <MAC>) is whitelisted on subnet <SUBNET>. Suppressing unknown device and missing hostname alerts.`

### 5. Excluded Host Status & Presumed Online Detection
Hosts excluded from network scans (`scanner.excluded_ips`, e.g., the primary modem/gateway `192.168.0.1` or sensitive equipment) are never directly probed with ARP sweeps or Nmap packets. 

To prevent misleading red "Stale / Offline" indicators on active infrastructure:
- **Heuristic**: When an excluded host resides on an active subnet with responding hosts (`isSubnetConnected && isSubnetOnline`), the host is classified as **"Presumed Online"** (`excluded_presumed_online`).
- **Visual Design**: Rendered as an emerald green ring (stroke: `#10b981`, translucent emerald fill `rgba(16, 185, 129, 0.18)`, drop shadow) instead of a solid circle, visually denoting a deduced operational status.
- **Filter Integration**: Presumed online excluded devices appear under the "Online" view filter and are excluded from the "Stale" filter.

---

## Scanner Bearer Token Lifecycle Management (`admin.scanner_tokens`)

To adhere to Zero Trust principles and prevent distributed network probes from accessing the central PostgreSQL server directly (port 5432), RTMS implements a dedicated, decoupled **Scanner Token Lifecycle Management** subsystem.

### Architecture & Security Model
- **Decoupled REST API**: Network probes (`rtms-scanner`) connect to `rtms-web` exclusively over HTTPS (`TCP/443` or `TCP/8000`).
- **Cryptographic Hashing**: Cleartext tokens are never stored in the database. When an administrator creates a token, the raw token string (prefixed `rtms_st_...`) is presented to the user **exactly once**. The backend calculates and stores only the `SHA-256` hash in `admin.scanner_tokens.token_hash`.
- **Strict 365-Day Ceiling**: In alignment with enterprise key management standards and NIS2 access control requirements, token lifespans are strictly capped at a maximum of **365 days (1 year)**. Attempting to create or renew a token with an expiration exceeding 365 days results in an HTTP 422 validation error.
- **Instant Revocation & Rotation**: Administrators can revoke compromised or decommissioned probes instantly from the web console, immediately terminating their access.

### Database Schema (`admin.scanner_tokens`)
```sql
CREATE TABLE IF NOT EXISTS admin.scanner_tokens (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS idx_scanner_tokens_hash ON admin.scanner_tokens(token_hash);
```

### REST API Endpoints (`backend/main.py`)
| Method | Path | Description | Access Control |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/scanner/tokens` | List all registered scanner tokens with validity and expiration | Admin Only (JWT) |
| `POST` | `/api/scanner/tokens` | Generate a new Bearer token (returns raw token once) | Admin Only (JWT, max 365 days) |
| `DELETE` | `/api/scanner/tokens/{id}` | Revoke an existing token immediately | Admin Only (JWT) |
| `POST` | `/api/scanner/renew-token` | Renew/rotate a scanner token before expiration | Scanner Bearer Auth (max 365 days) |
| `POST` | `/api/scanner/heartbeat` | Report probe status, interface IPs, and active media policy | Scanner Bearer Auth |
| `GET` | `/api/scanner/config` | Pull dynamic scanner configuration and polling interval | Scanner Bearer Auth |
| `POST` | `/api/scanner/sync-results` | Ingest discovery scans, open ports, and security anomalies | Scanner Bearer Auth |

---

## Central VPS Support, Licensing & Distribution Hub

RTMS includes an integrated, enterprise-grade connection to the **3TS Central Support Hub** hosted on an OVH Cloud VPS (`vps-054fcfa2.vps.ovh.net` / `support-api.3ts-consulting.com`).

### Architecture & Capabilities
- **Central Gateway**: Provides a high-availability cloud interface (`rtms-admin/vps-support-hub`) for support ticketing, license renewals, and software releases.
- **Zero-Trust Asymmetric Authentication (Ed25519)**:
  - The local appliance holds a private key (`/opt/rtms/config/instance.key`, `chmod 0600`) generated at installation.
  - Outgoing requests generate an ephemeral JWT (15-minute lifespan) signed via `EdDSA`.
  - The VPS validates the JWT signature against the customer's enrolled public key (`"3TS".client_keys`).
  - No permanent shared secrets circulate on the network, preventing credential replay or exfiltration risks.
  - Automatic fallback to legacy static Bearer tokens (`RTMS_SUPPORT_VPS_API_KEY`) if asymmetric keys are not yet configured.
- **Triple Purpose Integration**:
  1. **Support Ticketing**: Direct incident filing, diagnostic attachment ingestion, and real-time status tracking.
  2. **License Renewal Ingestion**: Automatic transmission of customer renewal requests containing hardware footprints for scanners, NVD engine, and local agents.
  3. **Software Releases & Updates**: Dynamic version manifest discovery (`/version`) and secure download of signed component packages (`.tar.gz`) with SHA-256 integrity verification.

### Key REST API Endpoints (`backend/main.py`)
- `GET /api/settings/support-hub`: Retrieves current Support VPS URL, masked legacy token status, and the appliance's **Ed25519 Cryptographic Instance Identity** (public key PEM and SHA-256 fingerprint).
- `POST /api/settings/support-hub`: Saves Support VPS URL and optional legacy Bearer API Token to `admin.system_config` with audit logging.
- `POST /api/settings/instance-identity/regenerate`: Performs cryptographic keypair rotation, generating a new Ed25519 keypair and updating system audit trails.
- `POST /api/settings/support-hub/test`: Tests live connectivity and cryptographic handshake against the VPS Support Hub (`GET /api/v1/version`).
- `POST /api/support/tickets`: Accepts ticket category, subject, description, priority, and optional diagnostics, returning a unique support ticket ID (`RTMS-YYYY-XXXX`).
- `GET /api/support/tickets/history`: Retrieves the customer's historical ticket log, resolution status, and technician notes.
- `POST /api/subscription/license/request-renewal`: Automatically transmits hardware footprint request to `{support_vps_url}/api/v1/license-requests` authenticated via signed JWT.
- `GET /api/system/updates/status`: Resolves the active release manifest from the VPS hub using signed JWT authentication and displays target versions and package availability.
- `POST /api/system/updates/apply`: Downloads signed `.tar.gz` packages from the VPS, validates their SHA-256 hash, and stages them for maintenance cycle application.






