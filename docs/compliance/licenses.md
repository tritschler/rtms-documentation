# RTMS Licensing System

## 1. Creation (On your Mac)

The license is generated asymmetrically via your generation script.

* **Inputs:** The script takes the `machine_id` (the DMI UUID of the target machine), the plan type (`PRO`), the maximum number of hosts, and the expiration date.
* **Canonical Serialization:** The dictionary containing this information (the `raw_payload`) is converted into an ultra-strict JSON string. Keys are sorted alphabetically (`sort_keys=True`) and unnecessary whitespaces are removed (`separators=(',', ':')`). This is crucial: any extra space or key reordering would alter the final hash.
* **Cryptographic Signature:** This character string is hashed using **SHA-256**, then encrypted (signed) with your RSA-2048 private key (`private_key.pem`).
* **Output (`license.key`):** The script generates the final JSON file containing the `raw_payload`, the Base64-encoded signature (`cryptographic_signature`), and surface metadata.

---

## 2. Import and DB Injection (On the Dell Server)

Database import is not handled by an external script; it is **automatically managed by the binary at startup**.

* **Who handles it?** The `license_validator.py` module via its `enforce_license_state()` function.
* **When?** At each initial application launch (when you run `./rtms-nvd` or when the systemd service starts `main.py`).
* **Import Mechanics:**
  1. The validator reads the physical `license.key` file located in the application directory.
  2. It verifies its signature (see section 3).
  3. If and only if the local file's signature is **100% valid**, it opens a PostgreSQL connection and calls `sync_license_to_db()`.
  4. It executes an `UPSERT` script (with the clause `ON CONFLICT ON CONSTRAINT unique_product_license_key DO UPDATE`). The license is then pushed or updated in the **`admin.product_license`** table.

---

## 3. Verification: By Whom and When?

This is where the architecture is most robust. The license is verified at two distinct moments: at **Bootstrap** and during **Awake** cycles.

* **By Whom?** Exclusively by the isolated security module `rtms_commons.license_validator`.
* **When?**
  1. **At startup (Bootstrap):** In `main()`, before initializing final logs and verifying the database schema.
  2. **At each cycle (Awake):** Every 120 minutes, as soon as the `BackgroundScheduler` wakes up the `incremental_sync()` function in `vulnerabilities.py`, the very first line of code executed re-invokes the validator.

### Internal Verification Workflow (Decision Flow)

During each verification, the validator runs the following DB-First algorithm:

1. **Primary Attempt (Database - Single Source of Truth):**
   * It connects to PostgreSQL and queries `admin.product_license` for an `ACTIVE` license matching the machine's hardware signature (`LOWER(hardware_id) = ANY(host_signatures)`).
   * *Success:* It validates the RSA cryptographic signature, hardware footprint, and expiration date. If valid, the license is loaded directly from DB without reading disk files.
   * *Failure (No active DB license or empty DB):* It proceeds to step 2.

2. **Fallback / Bootstrap Attempt (Local `license.key` File):**
   * It looks for the physical `license.key` file in the application directory.
   * *Success:* It validates the signature, hardware signature, and expiration date. If valid, it synchronizes/persists the token into PostgreSQL (`sync_license_to_db`) and sets it as `ACTIVE`.
   * *Failure (Missing, corrupt or expired file):* It proceeds to step 3.

3. **Sanction (DEMO Mode / Shutdown):**
   * If both the database and local file checks fail, or if grace period is exceeded, the validator triggers the appropriate degradation (DEMO mode or exit).

### The 3 Locks Validated During Each Verification

For a license (whether from the file or the database) to grant the `PRO` plan, it must pass three gates:

* **Cryptographic Lock:** The RSA-2048 public key decrypts the Base64 signature and verifies that it matches the `raw_payload` byte-for-byte. If anyone modifies even a single character of the payload (e.g., trying to alter `max_hosts`), the signature is broken.
* **Hardware Lock (Hardware Footprint):** The validator resolves the host machine's hardware identity:
  * **Bare-metal Linux:** reads SMBIOS `product_uuid` from `/sys/class/dmi/id/product_uuid` (or `dmidecode`).
  * **macOS:** reads `IOPlatformUUID` via `system_profiler SPHardwareDataType`.
  * **VMware ESXi / Workstation:** normalizes SMBIOS 2.6+ Little-Endian byte-swapping with vCenter formats. Cloned/copied VMs generate new UUIDs and are rejected; legitimately moved VMs preserve their UUID.
  * **Docker:** accesses the underlying host hardware through read-only host mounts (`/etc/host-machine-id` or `/sys/class/dmi/id/product_uuid`). Environment variable overrides (`RTMS_HARDWARE_ID`) are disallowed to prevent spoofing.
* **Temporal Lock:** It compares the current time (in strict UTC) with the `expires_at` date. If the expiration date has passed by less than 15 days, it continues running while displaying a grace period warning (`Grace period active`). Beyond that, the license expires and `DEMO` mode is activated.

---

## 4. UI License Upload and Validation

When a user uploads a new license via the Subscription interface, the backend performs immediate validation before applying any changes:

### Step 1: Schema Verification
The uploaded JSON file is parsed, and the backend verifies that all mandatory fields are present: `tenant_id`, `license_key_id` (or `license_id`), `raw_payload`, `cryptographic_signature`, and `expires_at`.
* Both individual license files and multi-license bundles (`{"licenses": [...]}`) are supported.
* **If missing:** The server immediately rejects the file with a `400 Bad Request` ("Invalid license file schema").

### Step 2: Cryptographic Validation
The `raw_payload` is reformatted using strict canonical JSON encoding to ensure byte-for-byte exactness. The backend then uses the embedded RSA public key to verify the `cryptographic_signature` against this payload.
* **If invalid (altered payload or incorrect signature):** The server blocks the operation with a `400 Bad Request` ("Invalid cryptographic signature").

### What happens if it is not validated?
* **Backend:** No changes are made. The `admin.product_license` database table remains untouched, and the existing `license.key` file is not overwritten. The previous license (or DEMO mode) continues to apply.
* **Frontend:** The UI intercepts the error and displays a red error banner at the top of the tab explaining the specific reason for rejection.

### What happens upon success?
If the license passes both validation steps, the backend securely writes the new license into the `admin.product_license` database table and overwrites the `license.key` file on disk. The UI then automatically refreshes to display the newly activated license details and limits.

---

## 5. Automated Renewal & Upgrade Workflow

RTMS provides an automated, end-to-end renewal cycle that eliminates the need for clients to manually re-run hardware extraction tools.

```
┌────────────────────────────────┐         Direct API / Email          ┌────────────────────────────────┐
│   Client RTMS Web Portal       │ ──────────────────────────────────> │   3TS Central VPS Support Hub  │
│  "Request Renewal / Upgrade"   │                                     │  (POST /api/v1/license-requests│
└────────────────────────────────┘                                     └────────────────────────────────┘
                │                                                                      │
                │ Backup file download                                                 │ Admin review
                ▼                                                                      ▼
 ┌──────────────────────────────┐                                       ┌──────────────────────────────┐
 │ rtms_renewal_request.json    │ ────────────────────────────────────> │  3TS Administrator Mac       │
 │ (Auto-bound Hardware IDs)    │   python license_generator.py        │  (private_key.pem offline)   │
 └──────────────────────────────┘   --request renewal_request.json     └──────────────────────────────┘
                                                                                       │
                                                                                       │ Signs keys
                                                                                       ▼
 ┌──────────────────────────────┐                                       ┌──────────────────────────────┐
 │ RTMS Web: "Upload License"   │ <──────────────────────────────────── │ rtms_license_bundle.json     │
 │ 1-Click Multi-Scanner Active │        Customer receives bundle       │ (or individual .key files)   │
 └──────────────────────────────┘                                       └──────────────────────────────┘
```

### 1. Client Renewal Request Generation (RTMS Web)
* From the **Subscription & License** page, clicking **"Request Early Upgrade"** or **"Upgrade License"** inspects PostgreSQL database records (`admin.service_registry`, `admin.agent_tokens`, `admin.tenant_infra`).
* The system automatically attaches all known Hardware IDs for active Scanners, NVD Engine, and Local Agents.
* Clicking **"Generate Request File"**:
  1. Sends the request directly to the **3TS Central Support Hub VPS** (authenticated via the appliance's Ed25519 signed JWT, or fallback Bearer token).
  2. Simultaneously downloads a local backup copy named `rtms_renewal_request_<tenant_id>.json`.

### 2. Central VPS Ingestion & Notification
* The Central Support Hub (`vps-support-hub`) receives the request via `POST /api/v1/license-requests`.
* It records the request in PostgreSQL (`license_requests`) and assigns a reference ID (`RTMS-LIC-YYYY-XXXX`).
* An automated email alert is immediately sent to `support@3ts-consulting.com` detailing the requested plan, asset count, and all detected hardware footprints.

### 3. Key Generation (3TS Admin Machine)
* The 3TS administrator uses their offline workstation where `private_key.pem` is stored.
* Generation is executed in 1 command without manual Hardware ID re-entry:
  ```bash
  python license_generator.py --request rtms_renewal_request_<tenant_id>.json
  ```
* The generator:
  * Automatically matches target machines.
  * Validates client payment records in `customers` DB.
  * Produces individual `license-<id>.key` files and a unified `rtms_license_bundle_<tenant_id>.json`.

### 4. Client Import & Activation
* The customer receives the bundle file and clicks **"Upload New License"** on their RTMS Web portal.
* The backend activates all renewed licenses in a single transaction, updating quotas and extending subscription validity across all registered scanners.