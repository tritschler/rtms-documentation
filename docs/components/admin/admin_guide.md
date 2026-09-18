# RTMS Administration & Licensing Workflow

This document explains the complete, end-to-end workflow for managing clients, registering payments, securely generating licenses, and performing maintenance for the RTMS software suite.

The administration tool is built to strictly enforce financial tracking. A license **cannot** be generated without an associated, validated, and sufficient payment.

## Complete Workflow Overview

The standard administrative process follows these steps:
1. **Create the Client**
2. **Generate the Client Password** (for web access)
3. **Register the Payment**
4. **Generate the License**

---

### Step 1: Create a Client

Before any financial transaction or license generation, the client must exist in the database.

**Command:**
```bash
uv run python main.py create_client
```

**What happens:**
- You will be prompted to enter the client's information (Name, Address, Email, etc.).
- A smart `Tenant ID` is automatically suggested based on the client's name.
- A unique `Client ID` is generated (format: `3TS-CLI-YYMM-XXXX`).
- **Security Check:** By default, all newly created clients are given a `"blocked"` status to prevent any unauthorized license generation before payment.

---

### Step 2: Generate the Client Password

To allow the client to log into the RTMS web platform, you must generate a secure password for them.

**Command:**
```bash
uv run python main.py create_password
```

**What happens:**
- The script asks for the `Client ID` and verifies that the client exists.
- A highly secure, random 16-character password is automatically generated.
- The password is mathematically hashed using the `bcrypt` algorithm.
- The hash is securely stored in the database.
- The cleartext password is shown **only once** in the terminal so you can transmit it to the client.

---

### Step 3: Register a Payment

Once the client has paid their invoice, the payment must be recorded in the system.

**Command:**
```bash
uv run python main.py add_payment
```

**What happens:**
- The script will ask for the `Client ID` and verify its existence.
- You will enter the exact `Amount` paid, the `Currency`, and an optional invoice reference.
- **Security Check:** The payment is registered in the database as an "unclaimed" payment.
- **Automation:** If the client's status was `"blocked"`, registering a successful payment will automatically switch their status to `"active"`.

---

### Step 4: Generate the License

This step generates cryptographically signed license keys using your offline RSA private key (`private_key.pem`). Two workflows are available:

#### Mode A: Interactive Manual Creation
Use this when issuing a license for a new customer or single machine manually.

**Command:**
```bash
uv run python main.py create_license
```

**What happens:**
1. **Client Verification:** The script asks for the `Client ID` and verifies that the client exists and is `"active"`.
2. **Payment Verification:** The script searches the database for an "unclaimed" payment. If none is found, generation is blocked.
3. **Pricing Matrix Validation:** 
   - You select a `Plan` (NVD, DISCOVERY, SECURE, COMPLIANCE) and `Max Hosts`.
   - The script interrogates the internal `pricing` table to calculate the exact price required.
   - **Strict Block:** If the payment amount is strictly lower than the expected price, generation is aborted.
4. **Generation & Tracking:** The `license.key` file is generated. The script securely records the license metadata in the `"3TS"` schema and updates the payment row to mark the payment as "consumed".

#### Mode B: Ingest Customer Renewal / Upgrade Request (Automated)
Use this when renewing existing client licenses or processing multi-scanner deployments without manual Hardware ID re-entry.

**Command:**
```bash
python license_manager/license_generator.py --request rtms_renewal_request_<tenant_id>.json
```

**What happens:**
1. **Request Ingestion:** The generator reads the JSON file exported from the customer's RTMS Web portal (or received via the Central VPS Support Hub).
2. **Automatic Hardware Resolution:** Resolves all registered Hardware IDs for Scanners, NVD Engine, and Local Agents.
3. **Database Validation:** Checks client status and unclaimed payments in the `customers` database.
4. **Multi-License Generation:** Generates signed keys for each distinct hardware footprint and creates a unified bundle file `rtms_license_bundle_<tenant_id>.json`.
5. **Customer Delivery:** Deliver the bundle file to the client; they upload it directly on their portal in 1 click.

---

## Maintenance & Database Cleaning

The administration tool includes commands for managing the lifecycle of licenses and performing database maintenance.

### Revoke a License

If a license is compromised or a subscription is cancelled, you can revoke it.

**Command:**
```bash
uv run python main.py revoke_license <license_key>
```

**What happens:**
- The status of the specific `license_key` is updated to `"revoked"` in the database.
- Future checks by the application will reject this license.

### Delete All Licenses (Danger Zone)

For testing purposes or complete resets, you can physically delete all licenses from the tracking database.

**Command:**
```bash
uv run python main.py delete_all_licenses
```

**What happens:**
- A warning message prompts you for confirmation.
- If you type `yes`, all rows in the `licenses` table are physically deleted.

### Full Database Truncation (Manual SQL)

If you need to completely reset the operational tables (clients, licenses, payments) while keeping your schemas and pricing configurations intact, you can run the following SQL command directly on your PostgreSQL `customers` database:

```sql
TRUNCATE TABLE "3TS".payments, "3TS".licenses, "3TS".clients CASCADE;
```

---

## Troubleshooting

- **"Client ID '...' is currently 'blocked'"** 
  You attempted to generate a license for a client that has no registered payments. Use the `add_payment` command first.
- **"No unclaimed payment found for Client"**
  The client has already used their previous payment for another license. A new payment must be registered.
- **"The payment amount is strictly lower than the required price"**
  The client did not pay enough for the selected Plan and Max Hosts limit according to the `pricing` table. Check the invoice or adjust the limit.
