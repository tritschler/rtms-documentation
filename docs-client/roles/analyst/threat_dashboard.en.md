# User Guide & Operations Manual: Threat Exposure Dashboard & SOC / SIEM Integration

This guide is intended for **cybersecurity analysts**, **system administrators**, and **SOC team leads** operating the RTMS platform. It details operational workflows, telemetry interpretation, and configuration procedures for the **Threat Exposure & SOC/SIEM Telemetry Correlation Dashboard**.

---

## 1. Overview & Operational Philosophy

In traditional architectures, vulnerability management (periodic static scans) and intrusion detection (SOC / SIEM) operate in segregated silos. A host exhibiting 20 vulnerabilities might face zero exploitation attempts, while an exposed critical asset with a single moderate vulnerability could experience active remote exploitation in real time.

The RTMS Threat Correlation Engine converges these two perspectives in real time:
- **Discovered Inventory & CVEs**: Gathered by distributed RTMS probes and endpoint agents.
- **Live Attack Telemetry**: Ingested from enterprise detection layers (**Splunk**, **Wazuh**, **Suricata**, **Microsoft Sentinel**, **CrowdStrike Falcon**).

### Core Benefits:
1. **Elimination of Alert Fatigue**: Focuses patching efforts directly on assets and services facing active threat vectors.
2. **Dynamic Contextual Risk Score ($CRS$)**: Automatically scales vulnerability severity according to observed hostile traffic.
3. **Immediate Incident Response**: Identifies `ACTIVELY_EXPLOITED` events requiring emergency isolation or remediation.

---

## 2. Navigating the Threat Dashboard (`/vulnerabilities?tab=threats`)

To access the dashboard:
1. In the primary navigation sidebar, click **Vulnerabilities** (or navigate to `/vulnerabilities`).
2. In the top sub-navigation bar, select the **Threats & SIEM** tab (radar icon).

```
┌────────────────────────────────────────────────────────────────────────┐
│                         VULNERABILITY CENTER                           │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│    Overview     │ Vulnerabilities │  Threats & SIEM  │  NVD History    │
└─────────────────┴─────────────────┴────────┬─────────┴─────────────────┘
                                             │
                                    [ Current Location ]
```

### A. Key Performance Indicators (KPI Cards)

At the top of the interface, 4 summary cards highlight overall posture:

* **Active Attack Telemetry**: Total volume of threat events ingested within the rolling 24h–48h window.
* **Actively Exploited CVEs (`ACTIVELY_EXPLOITED`)**: Vulnerabilities where both IP and destination port match active hostile traffic.
* **Targeted Assets**: Count of discovered network devices receiving confirmed malicious traffic.
* **Active Telemetry Provider**: Badge displaying current SIEM integration (*Wazuh*, *Splunk*, *Suricata*, *Sentinel*, *CrowdStrike*).

### B. Distribution Charts & Trend Telemetry

1. **Top Targeted Services & Ports**:
   - Ranks the 10 most attacked ports across your monitored networks (e.g., `Port 443 HTTPS`, `Port 22 SSH`, `Port 3389 RDP`).
   - Details total hit counts, active attacks, and severity levels.
2. **48-Hour Activity Histogram**:
   - Time-series chart divided into 4-hour intervals.
   - Highlights traffic spikes, automated sweeps, or targeted exploitation campaigns.

### C. Correlated Vulnerabilities Matrix

The central table correlates discovered CVEs against live hostile telemetry:

| Column | Description |
| :--- | :--- |
| **CVE ID & Severity** | Vulnerability identifier with NIST link and nominal CVSS rating (CRITICAL, HIGH, etc.). |
| **Asset / Host** | Targeted hostname and IP address. |
| **Port / Service** | Service port (includes indicator confirming exact match with attack telemetry). |
| **Contextual Score** | Dynamic severity score (up to 10.0) calculated by RTMS. |
| **Threat Status** | Operational state badge (`ACTIVELY_EXPLOITED`, `ATTACK_DETECTED`, etc.). |
| **Signatures & Telemetry** | Triggered SIEM / IDS rule names and recorded hit volume. |
| **Actions** | Create security incident, inspect details, or filter views. |

---

## 3. Threat Statuses & Contextual Risk Scoring

### Threat Status Tiers

| Status | Visual Badge | Operational Meaning | Recommended Action |
| :--- | :--- | :--- | :--- |
| **`ACTIVELY_EXPLOITED`** | Pulsing Crimson | **Urgent**. IP and exact port of this vulnerable service face active hostile requests (< 24h). | Immediate firewall isolation or emergency patch application. |
| **`ATTACK_DETECTED`** | Amber / Orange | Host IP is targeted by hostile traffic, but on an unrelated port or as part of a general sweep. | Heightened monitoring and firewall rule inspection. |
| **`TARGETED`** | Indigo / Purple | Host IP has received reconnaissance scans within the past 48h. | Schedule remediation during standard maintenance window. |
| **`POTENTIAL`** | Blue | Unexploited vulnerability with elevated CVSS base score. | Standard preventative patching. |
| **`DORMANT`** | Slate Gray | Minor vulnerability with zero detected hostile interest. | Routine lifecycle management. |

### Contextual Risk Score Calculation ($CRS$)

The contextual score originates from the CVSS v3 base score and incorporates weighted adjustments:
- **Attack Volume**: Logarithmic scaling based on suspicious hit volume (up to $+2.0$).
- **Port Match**: $+1.5$ points when attack telemetry precisely targets the listening service port.
- **SIEM Severity Rating**: Up to $+1.5$ points if the external SIEM rates the event as CRITICAL.
- **Telemetry Recency**: $+1.0$ point if the attack was observed within the past 24 hours.
- **Cap**: The combined score is strictly capped at **10.0**.

> **Example**: An OpenSSL vulnerability with CVSS base **7.5 (HIGH)** running on a web server (port 443). The SIEM reports 450 hostile payload requests on port 443 within the last 6 hours. The score escalates to **10.0 (CRITICAL - ACTIVELY EXPLOITED)**.

---

## 4. Setup Guide: Configuring SOC / SIEM Providers

To configure your telemetry source:
1. In the sidebar, navigate to **Settings** (`/settings`).
2. Scroll to the **SOC & Attack Telemetry Integration** card.
3. Toggle **Enable SOC / SIEM Correlation**.
4. Select your provider from the dropdown.

---

### Option 1: Splunk Enterprise / Splunk Cloud

1. **Provider Type**: Select `Splunk Enterprise / Cloud`.
2. **Splunk API URL**: Enter HTTPS access URL and management port (defaults to `8089` on-premise, or search head URL for Splunk Cloud):
   - Example: `https://splunk.corp.local:8089`
3. **Authentication Token**: Paste your Splunk Bearer Token (*Settings > Tokens*).
4. **Verify SSL**: Ensure checked in production to validate TLS certificate chains.
5. Click **Test Splunk Connection**.

---

### Option 2: Wazuh / Elasticsearch / OpenSearch

1. **Provider Type**: Select `Wazuh / Elasticsearch`.
2. **Wazuh Host**: Hostname or IP of the indexer node (e.g., `10.0.0.50` or `wazuh-indexer.corp.local`).
3. **Port**: Elasticsearch REST API port (default `9200`).
4. **Index Pattern**: Target indices (default `wazuh-alerts-*`).
5. **Authentication**: Enter username & password, or an Elasticsearch API Key.
6. **Enable SSL/TLS**: Enable if the cluster serves HTTPS.
7. Click **Test Wazuh Connection**.

---

### Option 3: Local Suricata (EVE JSON Log)

1. **Provider Type**: Select `Suricata (Local EVE Log)`.
2. **EVE JSON Log Path**: Absolute filesystem path to the log:
   - Linux default: `/var/log/suricata/eve.json`
3. **Permissions**: The RTMS system user (`rtms`) requires read access (`chmod 644 /var/log/suricata/eve.json`).
4. Click **Test Suricata Connection**.

---

### Option 4: Microsoft Sentinel (Azure Log Analytics)

1. **Provider Type**: Select `Microsoft Sentinel`.
2. **Workspace ID**: GUID of your Log Analytics workspace (*Log Analytics workspaces > Overview*).
3. **Tenant ID (Directory ID)**: Azure Entra ID tenant GUID.
4. **Application (Client) ID**: Registered Azure Application ID.
5. **Client Secret**: Application secret key.
6. **Target Table**: Table hosting security alerts (default `CommonSecurityLog` or `SecurityAlert`).
7. **Azure Permissions**: Application requires the **Log Analytics Reader** role on the workspace.
8. Click **Test Sentinel Connection**.

---

### Option 5: CrowdStrike Falcon

1. **Provider Type**: Select `CrowdStrike Falcon`.
2. **Falcon API Client ID**: Client ID provisioned in Falcon Console (*Support and resources > API clients and keys*).
3. **Falcon API Client Secret**: Corresponding secret.
4. **Falcon Cloud Base URL**: Select region matching your subscription:
   - `api.crowdstrike.com`: US-1
   - `api.us-2.crowdstrike.com`: US-2
   - `api.eu-1.crowdstrike.com`: EU-1 (Frankfurt - Recommended in Europe)
   - `api.laggar.gcw.crowdstrike.com`: GovCloud
5. **Required Permissions**: Read scope on **Alerts** (`Alerts: Read`).
6. Click **Test CrowdStrike Connection**.

---

## 5. Telemetry Synchronization

### Scheduled Ingestion
When enabled, RTMS polls configured telemetry sources every 15 minutes, refreshing `admin.threat_telemetry_cache`.

### On-Demand Ingestion
You can trigger an immediate refresh at any time:
1. Navigate to `/vulnerabilities?tab=threats`.
2. In the table toolbar, click **Sync Telemetry** (circular refresh icon).
3. A notification confirms the count of synchronized attack events.

---

## 6. Analyst Incident Response Playbook

When an `ACTIVELY_EXPLOITED` finding is identified:

```
[ ACTIVELY_EXPLOITED Detected ]
               │
               ▼
   1. Identify Target Asset & Port
               │
               ▼
   2. Restrict Hostile Flow at Firewall
               │
               ▼
   3. Create RTMS Finding / Incident
               │
               ▼
   4. Apply Security Patch / Workaround
               │
               ▼
   5. Trigger Scan & Validate Resolution
```

1. **Investigate Telemetry**: Click the finding row to inspect source IPs and attack signatures.
2. **Immediate Containment**: If non-essential, restrict the vulnerable port at perimeter firewalls.
3. **Open Security Incident**: Click **Create Incident** on the row to track remediation.
4. **Post-Patch Verification**: Execute a targeted rescan from the **Scanner** console. Finding resolves automatically.
