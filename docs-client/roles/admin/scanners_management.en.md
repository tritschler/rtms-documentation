# Probe Fleet & Scanner Management

The **Services Status & Probes** dashboard (`/admin/services` or the **Services Status** modal) centralizes operational oversight of all distributed network scanning probes deployed across your enterprise sites.

---

## 1. Overview & Heartbeat Monitoring

Each RTMS probe deployed throughout your infrastructure transmits periodic encrypted heartbeats to the central web server:
* **Probe Identifier & Hostname**: Device name (e.g. `rtms-scanner-hq`, `rtms-scanner-branch01`).
* **Host IP & Audited Subnets**: Active network interfaces monitored by the probe.
* **Software Version**: Verifies fleet homogeneity and tracks pending updates.
* **Operational Health**: `RUNNING`, `STANDBY` (high-availability failover), or `OFFLINE`.

---

## 2. Token Lifecycle Management (Bearer Tokens)

To authenticate against the RTMS REST API securely without static shared credentials:
* **Dedicated Bearer Tokens**: Distinct cryptographic API keys generated for each individual probe.
* **Security & Storage**: Raw tokens are hashed with SHA-256 before database persistence.
* **Strict Validity Window**: Token lifetime is capped at **365 days (1 year)**.
* **Instant Administrative Revocation**: In the event of decommissioned hardware or physical probe theft, operators can revoke tokens with a single click.

---

## 3. Network Media Policies (Wi-Fi vs Ethernet)

Administrators can customize authorized network media per probe:
* **Ethernet Only**: Scans are restricted to physical wire interfaces (ideal for rackmount server appliances).
* **Dedicated Wi-Fi Probe Mode**: Ethernet disabled, Wi-Fi enabled for dedicated wireless audit appliances.
* **Strict Ethernet Precedence**: If both interfaces share an identical subnet, Ethernet takes priority to prevent unnecessary wireless saturation.
