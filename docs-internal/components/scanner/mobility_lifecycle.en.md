# Scanner Mobility, Lifecycle & Multi-Network Management

This document describes the architectural and operational behavior of `rtms-scanner` and the RTMS platform when a machine running the scanner transitions across network environments (mobility / roaming, e.g., moving a laptop from a corporate office network to a home or customer network).

---

## 1. Context & Mobility Challenge

In numerous operational scenarios (field security audits, roaming analyst workstations, hybrid working setups), an appliance hosting RTMS Scanner may:
1. Discover and audit devices on Subnet A (e.g., corporate `10.20.0.0/24`).
2. Be powered down or disconnected.
3. Be rebooted on a completely distinct Subnet B (e.g., home network `192.168.1.0/24`).

This document clarifies key lifecycle questions:
* **What happens to the existing scanner record in the Services registry?**
* **Are previous subnets and discovered assets deleted?**
* **How is the newly discovered network incorporated?**

---

## 2. Lifecycle in the Service Registry (`admin.service_registry`)

### A. Hardware Identification (`machine_id`)
Each `rtms-scanner` instance computes a persistent hardware fingerprint (`machine_id`) at boot, derived from immutable system properties (DMI/Apple IORegistry hardware UUIDs, primary MAC addresses).

This identifier accompanies every periodic heartbeat transmitted to `rtms-web`.

### B. Offline State Detection
* When the scanner leaves Subnet A or is terminated, heartbeat broadcasts stop.
* The RTMS server health monitor (`services_health_monitor_worker`) evaluates probe freshness:
  * If a scanner fails to report within **30 seconds**, its status automatically transitions from `RUNNING` to **`OFFLINE`**.
  * The record remains visible in the Services dashboard to alert operators.

### C. Reactivation on the New Subnet
As soon as the probe powers on and boots on Subnet B:
1. **Deduplication Lookup:** The server receives the initial heartbeat containing `machine_id` and hostname. It queries `admin.service_registry` for existing records matching this hardware:
   ```sql
   SELECT id, service_name, status, started_at
   FROM admin.service_registry
   WHERE (service_name = :s OR (machine_id = :mid AND service_name LIKE 'rtms-scanner%'))
   ORDER BY ... LIMIT 1;
   ```
2. **In-Place Update:** The existing record is updated directly:
   * Status transitions back to **`RUNNING`** (green).
   * Host IP address (`host_ip`) is updated with the new local address.
   * The `subnet` column is replaced by newly discovered local CIDR blocks (e.g., `192.168.1.0/24`).
   * `last_heartbeat` is updated to the current timestamp.
3. **Orphan Cleanup:** Any stale duplicate rows with matching `machine_id` have their scan records reparented and are cleanly removed.
4. **Leader Election (High Availability):** If another probe is already actively auditing Subnet B, the joining probe transitions to **`STANDBY`** (failover redundancy). If it is the sole probe, it assumes the active **`RUNNING`** role.

---

## 3. Network & Asset Inventory Persistence

A common question is whether roaming wipes previously audited subnets or devices. **The answer is NO.**

RTMS adheres strictly to compliance and traceability standards (NIS2, Cyber Resilience Act). The inventory operates as a persistent historical configuration management database (CMDB):

### A. Subnet Retention (`scanner.networks`)
* The historical subnet (e.g., `10.20.0.0/24`) **is retained** in `scanner.networks`.
* In the Asset Inventory UI:
  * Since no local network interface on the probe currently matches this CIDR, the subnet is designated as **"Disconnected"** (`isSubnetConnected = false`).
  * It is automatically **collapsed into a single compact line** to keep the dashboard organized while preserving full historical records.

### B. Device Retention (`admin.assets`)
* Workstations, servers, and printers discovered on Subnet A **are not deleted**.
* They retain complete profiles: IP, MAC, vendor, operating system, open ports/services, and historical `last_seen` timestamp.
* **Isolated Offline Scoping:** When scan cycles run on Subnet B, unreachable host invalidation (`is_up = false`) is **strictly scoped to the currently scanned subnet**:
  ```sql
  UPDATE admin.assets
  SET is_up = false
  WHERE (network_id = :nid OR network_id IN (
      SELECT id FROM scanner.networks WHERE cidr = CAST(:cidr AS cidr)
  )) AND NOT (ip_address = ANY(:seen_ips));
  ```
  Consequently, assets residing on Subnet A are never marked offline or modified by scans running on Subnet B.

### C. Provisioning of the New Subnet
* Upon completion of the first sweep on Subnet B, `scanner.networks` provisions a new record (e.g., `Subnet 192.168.1.0/24`) if absent.
* Newly discovered assets are mapped and cataloged.
* Scan snapshots (`scanner.scan_archives`) and execution runs (`scanner.scans`) remain segregated by subnet and timestamped.

---

## 4. Behavior Summary Table

| Component / Record | Before Roaming (Subnet A) | Scanner Stopped | After Boot (Subnet B) |
| :--- | :--- | :--- | :--- |
| **Service Status** | `RUNNING` | `OFFLINE` (after 30s) | `RUNNING` (or `STANDBY` if peer active) |
| **Service Subnet Display** | Subnet A (`10.20.0.0/24`) | Subnet A | Subnet B (`192.168.1.0/24`) |
| **Subnet A Database Row** | Active (`scanner.networks`) | Retained | **Preserved** (Disconnected, collapsed row) |
| **Assets on Subnet A** | `is_up = true` | `is_up` unchanged | **Preserved** with historical `last_seen` |
| **New Subnet B** | Absent or idle | Absent or idle | **Created / Activated**, hosts mapped |
| **Scan History** | Subnet A archives saved | Saved | Subnet A archives remain queryable in *Scan Archives* |

---

## 5. Maintenance & Optional Cleanup

If auditing Subnet A was purely temporary (e.g., one-off demonstration, ephemeral test lab) and an administrator wishes to purge historical data:

1. **Manual Asset Removal:**
   * Open **Asset Management**, filter by desired subnet or organization, and delete obsolete entries.
2. **Purge Offline Services:**
   * In the **Services** view, click **"Purge Offline Services"** to clean probes inactive for more than 48 hours.
3. **Automated Database Maintenance:**
   * Scheduled background workers (`automated_db_maintenance_worker`) periodically purge transient scan logs and inactive records exceeding 90 days.
