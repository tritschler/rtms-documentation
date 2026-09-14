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
* **Hardware Lock (Hardware Footprint):** The validator runs `sudo dmidecode -s system-uuid` and compares the resulting string with the `machine_id` stored in the license. If the strings do not match (e.g., in the case of a cloned VM or a disk image copied to another server), the license is rejected.
* **Temporal Lock:** It compares the current time (in strict UTC) with the `expires_at` date. If the expiration date has passed by less than 15 days, it continues running while displaying a grace period warning (`Grace period active`). Beyond that, the license expires and `DEMO` mode is activated.

---

## 4. UI License Upload and Validation

When a user uploads a new license via the Subscription interface, the backend performs immediate validation before applying any changes:

### Step 1: Schema Verification
The uploaded JSON file is parsed, and the backend verifies that all mandatory fields are present: `tenant_id`, `license_key_id` (or `license_id`), `raw_payload`, `cryptographic_signature`, and `expires_at`.
* **If missing:** The server immediately rejects the file with a `400 Bad Request` ("Invalid license file schema").

### Step 2: Cryptographic Validation
The `raw_payload` is reformatted using strict canonical JSON encoding to ensure byte-for-byte exactness. The backend then uses the embedded RSA public key to verify the `cryptographic_signature` against this payload.
* **If invalid (altered payload or incorrect signature):** The server blocks the operation with a `400 Bad Request` ("Invalid cryptographic signature").

### What happens if it is not validated?
* **Backend:** No changes are made. The `admin.product_license` database table remains untouched, and the existing `license.key` file is not overwritten. The previous license (or DEMO mode) continues to apply.
* **Frontend:** The UI intercepts the error and displays a red error banner at the top of the tab explaining the specific reason for rejection.

### What happens upon success?
If the license passes both validation steps, the backend securely writes the new license into the `admin.product_license` database table and overwrites the `license.key` file on disk. The UI then automatically refreshes to display the newly activated license details and limits.