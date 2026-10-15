# Test Specification: Central VPS Gateway Endpoints (Tickets, Updates, Licenses)

This document specifies the complete test procedure for verifying the functionality, cryptographic security, and network isolation of the **three central client-facing endpoints** hosted on the OVH VPS (`https://updates.3ts.ai`).

---

## 1. Architectural & Security Context

```mermaid
sequenceDiagram
    autonumber
    participant Client as RTMS Web (Customer Appliance)
    participant Nginx as NGINX VPS OVH (443 SSL)
    participant Hub as FastAPI Backend (127.0.0.1:8090)
    participant DB as PostgreSQL (customers)

    Note over Client,Nginx: Secure Public Zone (TLS 1.3 / updates.3ts.ai)
    Client->>Nginx: HTTPS Request with Authorization: Bearer <JWT_Ed25519 / Token>
    Nginx->>Hub: Reverse Proxy to FastAPI
    Hub->>Hub: verify_client_token() : Ed25519 Signature or SHA-256 Hash
    Hub->>DB: Write / Read (support_tickets, software_releases, license_requests)
    Hub-->>Client: Encrypted JSON Response
```

* **Public FQDN**: `https://updates.3ts.ai`
* **Public VPS IP**: `135.125.102.194`
* **Listening Port**: `443` (HTTPS - Strong TLS 1.3 cipher suites)
* **Unified Authentication Guard**: FastAPI dependency `verify_client_token` accepting either an ephemeral (15-min) **Ed25519** asymmetric signed JWT or a hashed **Bearer Token** stored in `"3TS".client_tokens`.

---

## 2. Test Cases Matrix

| Test ID | Target Component | Method & Endpoint | Validated Objective |
| :--- | :--- | :--- | :--- |
| **`TC-VPS-TICKETS-01`** | Support & Bug Reports | `POST /api/v1/tickets` | Ticket submission with telemetry from RTMS Web UI |
| **`TC-VPS-TICKETS-02`** | Support & Bug Reports | `POST /api/v1/tickets` | Direct cURL call with Bearer Token |
| **`TC-VPS-TICKETS-03`** | Support & Bug Reports | `POST /api/v1/tickets` | Security rejections (HTTP 401 missing / HTTP 403 invalid token) |
| **`TC-VPS-TICKETS-04`** | Support & Bug Reports | Database `customers` & SMTP | SQL persistence and email alert via `ssl0.ovh.net` |
| **`TC-VPS-UPDATES-01`** | Software Releases | `/opt/rtms-admin/packages` | Package staging (`.tar.gz`) and release publishing on VPS |
| **`TC-VPS-UPDATES-02`** | Software Releases | `GET /api/v1/version` | Automated version discovery from UI `/security/software` |
| **`TC-VPS-UPDATES-03`** | Software Releases | `POST /api/system/updates/apply` | Package download and SHA-256 integrity validation |
| **`TC-VPS-UPDATES-04`** | Software Releases | `GET /api/v1/updates/packages/...` | Direct streaming download via authenticated cURL |
| **`TC-VPS-LICENSES-01`** | Licenses & Quotas | `POST /api/license/generate-renewal-request` | Renewal request submission via UI `/license` |
| **`TC-VPS-LICENSES-02`** | Licenses & Quotas | `POST /api/v1/license-requests` | Direct cURL submission with full hardware telemetry payload |
| **`TC-VPS-LICENSES-03`** | Licenses & Quotas | Database `customers` | Confirmation of pending request in database table |
| **`TC-VPS-LICENSES-04`** | Licenses & Quotas | RTMS Admin | 1-click Approval workflow and `.key` bundle emission |
| **`TC-VPS-NET-01`** | Network & Crypto | TLS 1.3 / Port 443 | SSL encryption, valid Let's Encrypt cert, and HSTS header |
| **`TC-VPS-NET-02`** | Network & Routing | WAN vs VPN Routing | Public WAN IP logged in `/var/log/nginx/access.log` (not 10.0.0.1) |
| **`TC-VPS-NET-03`** | Network & Partitioning | NGINX Public Server | Strict block (404) of admin web console on public port |

---

## 3. Detailed Step-by-Step Test Procedures

### Test Suite 1: Support Ticket Ingestion

#### Case `TC-VPS-TICKETS-01`: Submission via RTMS Web UI
1. **Access**: Log into RTMS Web as an Administrator and navigate to `/help/support`.
2. **Action**:
   * Subject: `Platform qualification test VPS`
   * Category: `incident` | Priority: `high`
   * Description: `Validating public support gateway over WAN.`
   * Check the option *"Include diagnostic data"*.
   * Click **"Submit Support Ticket"**.
3. **Expected Result**:
   * Green toast showing the assigned reference ID (e.g. `RTMS-2026-XXXX`).
   * Ticket appears in the history table with status `open` or `submitted`.

#### Case `TC-VPS-TICKETS-02`: Direct API Submission (cURL)
Run from a terminal:
```bash
curl -X POST https://updates.3ts.ai/api/v1/tickets \
  -H "Authorization: Bearer 2c47b3eaad6f415c565556ba5146701195d5bd27320c21781e29ad2614e01242" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "Marc Tritschler",
    "user_email": "support@3tsconsulting.be",
    "company_name": "3TS Client Qualification",
    "instance_id": "INSTANCE-TEST-01",
    "subject": "Direct cURL ticket",
    "category": "incident",
    "priority": "normal",
    "description": "Validating direct API payload delivery",
    "diagnostic_data": {"rtms_version": "0.1.0", "assets_count": 42}
  }'
```
* **Expected Result**: `HTTP 201 Created` with JSON: `{"success": true, "ticket_id": "RTMS-2026-XXXX", "status": "open"}`.

#### Case `TC-VPS-TICKETS-03`: Security Rejection of Unauthorized Calls
```bash
# Missing token -> must return 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://updates.3ts.ai/api/v1/tickets -d '{}'

# Invalid token -> must return 403
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer invalid_token" -X POST https://updates.3ts.ai/api/v1/tickets -d '{}'
```
* **Pass Criteria**: HTTP 401 for the first, HTTP 403 for the second.

#### Case `TC-VPS-TICKETS-04`: Database Verification on VPS
From your Mac (via Ansible):
```bash
cd rtms-installer/ansible
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command \
  -a "su - postgres -c \"psql -d customers -c 'SELECT ticket_id, company_name, subject, priority, status, created_at FROM support_tickets ORDER BY created_at DESC LIMIT 3;'\"" --become
```
* **Pass Criteria**: Row exists with valid `ticket_id` and correct metadata.

---

### Test Suite 2: Software Release Distribution

#### Case `TC-VPS-UPDATES-01`: Release Staging on VPS
1. **Create compiled archive package on VPS**:
   ```bash
   ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "bash -c '
     mkdir -p /opt/rtms-admin/packages /tmp/pkg-tmp
     echo \"RTMS Scanner Binary Release v0.2.0\" > /tmp/pkg-tmp/scanner
     tar -czf /opt/rtms-admin/packages/rtms-scanner-release.tar.gz -C /tmp/pkg-tmp scanner
     rm -rf /tmp/pkg-tmp
     chmod 644 /opt/rtms-admin/packages/rtms-scanner-release.tar.gz
   '" --become
   ```
2. **Publish version record in database**:
   ```bash
   ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "su - postgres -c \"psql -d customers -c \\\"
     INSERT INTO software_releases (version, release_notes, manifest, is_active)
     VALUES ('0.2.0', 'Release 0.2.0 : Optimisations du scan réseau et conformité NIS 2', '{\\\\\\\"version\\\\\\\": \\\\\\\"0.2.0\\\\\\\", \\\\\\\"components\\\\\\\": [{\\\\\\\"name\\\\\\\": \\\\\\\"rtms-scanner\\\\\\\", \\\\\\\"version\\\\\\\": \\\\\\\"0.2.0\\\\\\\"}], \\\\\\\"packages\\\\\\\": {\\\\\\\"rtms-scanner\\\\\\\": {\\\\\\\"filename\\\\\\\": \\\\\\\"rtms-scanner-release.tar.gz\\\\\\\", \\\\\\\"url\\\\\\\": \\\\\\\"/api/v1/updates/packages/rtms-scanner-release.tar.gz\\\\\\\"}}}', true)
     ON CONFLICT (version) DO UPDATE SET is_active = true, updated_at = NOW();
   \\\"\"" --become
   ```

#### Case `TC-VPS-UPDATES-02`: Version Discovery via RTMS Web UI
1. Navigate to **Administration > Software Updates** (`/security/software`).
2. **Pass Criteria**:
   * Banner turns blue: **"Update Available: v0.2.0"**.
   * Release notes are clearly displayed.
   * `rtms-scanner` appears in the components list.

#### Case `TC-VPS-UPDATES-03`: Download & SHA-256 Verification
1. Click **"Download and Stage Update"**.
2. **Pass Criteria**:
   * Package downloaded over HTTPS into `rtms-web/backend/updates/downloads/rtms-scanner-release.tar.gz`.
   * SHA-256 hash computed and verified.
   * UI displays green "Staged" badge.

#### Case `TC-VPS-UPDATES-04`: Direct Binary Stream via cURL
```bash
curl -s -H "Authorization: Bearer 2c47b3eaad6f415c565556ba5146701195d5bd27320c21781e29ad2614e01242" \
  https://updates.3ts.ai/api/v1/updates/packages/rtms-scanner-release.tar.gz | tar -tzv
```
* **Pass Criteria**: Tar archive lists contents cleanly (`-rw-r--r-- scanner`).

---

### Test Suite 3: License Renewal & Expansion Requests

#### Case `TC-VPS-LICENSES-01`: UI Submission from RTMS Web
1. Open **Subscriptions & Licenses** (`/license`).
2. Scroll to **"License Renewal & Upgrade Request"** (⚡ icon).
3. Click **"Request Renewal"**.
4. Choose target plan (e.g. `SECURE`) and asset quota (e.g. `250 assets`), then submit.
5. **Pass Criteria**:
   * Green banner: `Renewal request (RTMS-LIC-2026-XXXX) successfully sent to 3TS Central Support Hub !`.
   * A local JSON backup file `rtms_renewal_request_<tenant>.json` downloads automatically.

#### Case `TC-VPS-LICENSES-02`: Direct API Submission (cURL)
```bash
curl -X POST https://updates.3ts.ai/api/v1/license-requests \
  -H "Authorization: Bearer 2c47b3eaad6f415c565556ba5146701195d5bd27320c21781e29ad2614e01242" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "CLIENT-QUALIF-2026",
    "company_name": "Entreprise de Qualification",
    "contact_name": "Marc Tritschler",
    "contact_email": "admin@qualif.be",
    "requested_plan": "COMPLIANCE",
    "requested_assets": 500,
    "notes": "Automated renewal test",
    "request_payload": {
      "scanners": [{"name": "probe-principal", "hardware_id": "hw-qualif-8888"}],
      "components": {"core": "0.1.0"},
      "format_version": "1.0"
    }
  }'
```
* **Pass Criteria**: `HTTP 201 Created` with unique request ID:  
  `{"success": true, "request_id": "RTMS-LIC-2026-XXXX", "status": "pending"}`.

#### Case `TC-VPS-LICENSES-03`: PostgreSQL Verification on VPS
```bash
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command \
  -a "su - postgres -c \"psql -d customers -c 'SELECT id, request_id, tenant_id, requested_plan, requested_assets, status, created_at FROM license_requests ORDER BY created_at DESC LIMIT 2;'\"" --become
```
* **Pass Criteria**: New row exists with `pending` status.

#### Case `TC-VPS-LICENSES-04`: 1-Click Approval in RTMS Admin Backoffice
1. Connect to 3TS Admin Portal over WireGuard: `http://10.0.0.1/`.
2. Open **License Requests**.
3. Click **"Approve"**: The generator signs the RSA license and outputs the `.key` bundle file.

---

### Test Suite 4: Network Security, SSL & Partitioning

#### Case `TC-VPS-NET-01`: SSL / TLS 1.3 & HSTS Inspection
```bash
echo | openssl s_client -connect updates.3ts.ai:443 -servername updates.3ts.ai 2>&1 | grep -E "Protocol|Cipher|Verify return code"
```
* **Pass Criteria**:
  * `Protocol: TLSv1.3`
  * `Cipher: TLS_AES_256_GCM_SHA384`
  * `Verify return code: 0 (ok)`.

#### Case `TC-VPS-NET-02`: Public WAN Routing Audit
1. Execute a curl request to `https://updates.3ts.ai/api/v1/version`.
2. Inspect NGINX logs on the VPS:
   ```bash
   ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "tail -n 2 /var/log/nginx/access.log" --become
   ```
* **Pass Criteria**: Logged source IP is the external WAN IP of your connection, **not the 10.0.0.2** WireGuard IP.

#### Case `TC-VPS-NET-03`: Public Zone Access Restriction
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://updates.3ts.ai/
curl -s -o /dev/null -w "%{http_code}\n" https://updates.3ts.ai/docs/
```
* **Pass Criteria**: Returns **HTTP 404** `{"detail": "Not Found"}`. The web admin console is strictly unreachable from the internet.

---

## 4. Execution Sign-off Matrix

| Test Case | Observed Result | Verdict | Date & Engineer |
| :--- | :--- | :--- | :--- |
| `TC-VPS-TICKETS-01` | Ticket created, reference displayed in UI | ✅ PASSED | 15/10/2026 - Marc Tritschler |
| `TC-VPS-TICKETS-02` | HTTP 201, `ticket_id` returned | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-TICKETS-03` | Strict HTTP 401 & 403 rejection | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-TICKETS-04` | Recorded in `support_tickets` table | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-01` | Package tar.gz & SQL version 0.2.0 active | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-02` | v0.2.0 detected in Web UI | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-03` | Local download & SHA-256 verified | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-04` | Streamed binary unpacked successfully | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-01` | UI submission & backup JSON saved | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-02` | HTTP 201 `RTMS-LIC-2026-9189` | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-03` | Recorded in `license_requests` table | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-04` | Admin 1-click approval validated | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-NET-01` | TLS 1.3 / AES-256-GCM / Let's Encrypt valid | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-NET-02` | Client WAN IP in NGINX access log | ✅ PASSED | 15/10/2026 - 3TS Automation |
| `TC-VPS-NET-03` | HTTP 404 on external Web / Docs paths | ✅ PASSED | 15/10/2026 - 3TS Automation |
