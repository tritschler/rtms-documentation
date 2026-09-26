# RTMS SOC / SIEM & Threat Exposure Correlation Engine
## Technical Architecture & Integration Guide

This document provides a comprehensive technical reference for the **Threat Exposure & Telemetry Correlation Subsystem** of the RTMS platform. It covers data models, ingestion mechanisms, normalization adapters, mathematical risk scoring algorithms, and REST APIs.

---

## 1. Architectural Overview

The RTMS Threat Correlation Engine bridges static vulnerability scanning with real-time operational threat telemetry gathered from enterprise SOC and SIEM systems.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           External Telemetry Sources                            │
├──────────────┬──────────────────┬─────────────────┬──────────────┬──────────────┤
│ Splunk Cloud │ Wazuh / Elastic  │  Suricata IDS   │ MS Sentinel  │ CrowdStrike  │
│  REST / HEC  │    /_search      │  eve.json log   │  Azure KQL   │  Cloud API   │
└──────┬───────┴────────┬─────────┴────────┬────────┴──────┬───────┴──────┬───────┘
       │                │                  │               │              │
       ▼                ▼                  ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Threat Telemetry Provider Adapters                       │
│                     (rtms-web/backend/risk_correlator.py)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ - BaseThreatProvider (Abstract Base Class)                                      │
│   ├── SplunkThreatProvider                                                      │
│   ├── WazuhThreatProvider                                                       │
│   ├── SuricataThreatProvider                                                    │
│   ├── SentinelThreatProvider                                                    │
│   └── CrowdStrikeThreatProvider                                                 │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼ (Normalized AttackMetric objects)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PostgreSQL Telemetry Cache                            │
│                       `admin.threat_telemetry_cache`                            │
│            Unique Constraint: (dest_ip, dest_port, provider)                    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             RiskCorrelator Engine                               │
│  - Correlates ScannedVulnerability with active AttackMetric telemetry           │
│  - Calculates dynamic Contextual Risk Score (1.0 - 10.0)                         │
│  - Assigns Threat Status (ACTIVELY_EXPLOITED, ATTACK_DETECTED, TARGETED, etc.)  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Threat Telemetry Endpoints                         │
│  - GET /api/threats/overview-kpis                                               │
│  - GET /api/threats/top-targeted-services                                       │
│  - GET /api/threats/activity-timeline                                           │
│  - GET /api/threats/correlated                                                  │
│  - POST /api/threats/sync                                                       │
│  - POST /api/settings/soc/test                                                  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       React ThreatExposureDashboard                             │
│                  (frontend/src/components/ThreatExposureDashboard.tsx)           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ingestion Adapters & Protocols

Each provider subclasses `BaseThreatProvider` and implements `fetch_telemetry(window_hours: int = 48) -> List[AttackMetric]`.

### A. Splunk Enterprise & Splunk Cloud (`SplunkThreatProvider`)
- **Transport**: HTTPS REST API (`POST /services/search/jobs/export`).
- **Authentication**: HTTP Header `Authorization: Splunk <token>` or `Bearer <token>`.
- **Search Query**:
  ```spl
  search index=* (sourcetype=suricata* OR sourcetype=pan:threat OR sourcetype=cisco:asa OR action=blocked OR action=alert)
  | stats count, values(signature) as signatures, max(severity) as max_severity, min(_time) as first_seen, max(_time) as last_seen by dest_ip, dest_port
  ```
- **Response Format**: Output mode `json`.

### B. Wazuh / Elasticsearch / OpenSearch (`WazuhThreatProvider`)
- **Transport**: HTTPS REST API (`POST /{index_pattern}/_search`).
- **Index Pattern**: `wazuh-alerts-*`, `filebeat-*`, `suricata-*`.
- **Authentication**: HTTP Basic Auth (`username:password`) or `Authorization: ApiKey <api_key>`.
- **Query DSL**:
  ```json
  {
    "size": 0,
    "query": {
      "bool": {
        "filter": [
          { "range": { "@timestamp": { "gte": "now-48h" } } },
          { "range": { "rule.level": { "gte": 5 } } }
        ]
      }
    },
    "aggs": {
      "by_dest": {
        "terms": { "field": "data.destip.keyword", "size": 1000 },
        "aggs": {
          "by_port": {
            "terms": { "field": "data.destport", "size": 50 },
            "aggs": {
              "max_level": { "max": { "field": "rule.level" } },
              "signatures": { "terms": { "field": "rule.description.keyword", "size": 5 } }
            }
          }
        }
      }
    }
  }
  ```

### C. Suricata Local IDS (`SuricataThreatProvider`)
- **Transport**: Streaming file reader on newline-delimited `eve.json` (e.g. `/var/log/suricata/eve.json`).
- **Filter**: Only lines where `"event_type": "alert"`.
- **Extracted Fields**:
  - `dest_ip`: Target host address.
  - `dest_port`: Destination service port.
  - `alert.signature`: Detection rule message.
  - `alert.severity`: Mapped to severity levels (`1` -> CRITICAL, `2` -> HIGH, `3` -> MEDIUM).
  - `timestamp`: Event ISO-8601 timestamp.

### D. Microsoft Sentinel (`SentinelThreatProvider`)
- **Transport**: Two-step Azure REST communication:
  1. **Token Acquisition**:
     - `POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token`
     - Form parameters: `grant_type=client_credentials`, `client_id=...`, `client_secret=...`, `scope=https://api.loganalytics.io/.default`.
  2. **Log Analytics Query Execution**:
     - `POST https://api.loganalytics.io/v1/workspaces/{workspace_id}/query`
     - Header: `Authorization: Bearer <access_token>`
     - KQL Query:
       ```kql
       CommonSecurityLog
       | where TimeGenerated >= ago(48h) and Activity != ""
       | summarize TotalHits = count(), MaxSeverity = max(LogSeverity), Signatures = make_set(Activity) by DestinationIP, DestinationPort
       ```

### E. CrowdStrike Falcon (`CrowdStrikeThreatProvider`)
- **Transport**: Two-step Falcon Cloud REST API:
  1. **Token Acquisition**:
     - `POST https://{base_url}/oauth2/token`
     - Form parameters: `client_id=...`, `client_secret=...`.
  2. **Alert Query & Entity Details**:
     - `GET https://{base_url}/alerts/queries/alerts/v2?limit=500`
     - `GET https://{base_url}/alerts/entities/alerts/v2?ids=...`
     - Extracted attributes: `local_ip`, `local_port`, `description`, `severity_name`.

---

## 3. Database Schema Specifications

### `admin.threat_telemetry_cache`

```sql
CREATE TABLE IF NOT EXISTS admin.threat_telemetry_cache (
    id SERIAL PRIMARY KEY,
    dest_ip INET NOT NULL,
    dest_port INTEGER,
    total_hits INTEGER NOT NULL DEFAULT 1,
    max_severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    signatures TEXT[] DEFAULT '{}',
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    provider VARCHAR(50) NOT NULL DEFAULT 'splunk',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_telemetry_target UNIQUE (dest_ip, dest_port, provider)
);

CREATE INDEX IF NOT EXISTS idx_threat_telemetry_ip ON admin.threat_telemetry_cache(dest_ip);
CREATE INDEX IF NOT EXISTS idx_threat_telemetry_port ON admin.threat_telemetry_cache(dest_port);
CREATE INDEX IF NOT EXISTS idx_threat_telemetry_provider ON admin.threat_telemetry_cache(provider);
CREATE INDEX IF NOT EXISTS idx_threat_telemetry_last_seen ON admin.threat_telemetry_cache(last_seen);
```

### `admin.system_config` Keys

| Configuration Key | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `soc_enabled` | `BOOLEAN` | `false` | Master toggle for SOC telemetry integration |
| `soc_type` | `VARCHAR(50)` | `Splunk` | Active provider (`Splunk`, `Wazuh`, `Suricata`, `Sentinel`, `CrowdStrike Falcon`) |
| `soc_url` | `TEXT` | `""` | Splunk REST API URL |
| `soc_splunk_token` | `TEXT` | `""` | Splunk Bearer authentication token |
| `soc_splunk_verify_ssl` | `BOOLEAN` | `true` | Enable/disable SSL validation for Splunk |
| `soc_wazuh_host` | `TEXT` | `"localhost"` | Wazuh / Elasticsearch node IP or hostname |
| `soc_wazuh_port` | `INTEGER` | `9200` | Wazuh / Elasticsearch port |
| `soc_wazuh_index` | `TEXT` | `"wazuh-alerts-*"` | Wazuh index pattern |
| `soc_wazuh_user` | `TEXT` | `"admin"` | Wazuh basic auth username |
| `soc_wazuh_password` | `TEXT` | `""` | Wazuh basic auth password |
| `soc_wazuh_api_key` | `TEXT` | `""` | Elasticsearch API key (alternative to password) |
| `soc_wazuh_ssl` | `BOOLEAN` | `false` | Enable/disable TLS for Wazuh |
| `soc_suricata_eve_path` | `TEXT` | `"/var/log/suricata/eve.json"` | Absolute file path to Suricata EVE JSON log |
| `soc_sentinel_workspace_id` | `TEXT` | `""` | Azure Log Analytics Workspace GUID |
| `soc_sentinel_tenant_id` | `TEXT` | `""` | Azure Entra Tenant ID |
| `soc_sentinel_client_id` | `TEXT` | `""` | Azure Registered Application Client ID |
| `soc_sentinel_client_secret` | `TEXT` | `""` | Azure Registered Application Client Secret |
| `soc_sentinel_table` | `TEXT` | `"CommonSecurityLog"` | Target KQL table |
| `soc_crowdstrike_client_id` | `TEXT` | `""` | CrowdStrike Falcon API Client ID |
| `soc_crowdstrike_client_secret`| `TEXT` | `""` | CrowdStrike Falcon API Client Secret |
| `soc_crowdstrike_base_url` | `TEXT` | `"api.crowdstrike.com"` | CrowdStrike Falcon Cloud Region Base URL |

---

## 4. Contextual Risk Correlator Algorithm

The `RiskCorrelator` class executes the contextual calculation dynamically.

### Inputs
- **`scanned: List[ScannedVulnerability]`**: Scanned vulnerabilities from `admin.asset_vulnerabilities` and `nvd.cve`.
- **`metrics: List[AttackMetric]`**: Telemetry hits from `admin.threat_telemetry_cache`.

### Correlation Keys
Correlation occurs on:
$$\text{Key} = (\text{dest\_ip}, \text{dest\_port})$$

### Mathematical Formula

$$\text{ContextualRiskScore} = \min\left(10.0, CVSS_{base} + \Delta_{hits} + \Delta_{port} + \Delta_{severity} + \Delta_{recency}\right)$$

1. **Volume Multiplier ($\Delta_{hits}$)**:
   $$\Delta_{hits} = \min\left(2.0, \log_{10}(\text{hits} + 1) \times 0.65\right)$$
   - $1 \text{ hit} \approx +0.20$
   - $10 \text{ hits} \approx +0.68$
   - $100 \text{ hits} \approx +1.30$
   - $\ge 1200 \text{ hits} \approx +2.00$

2. **Port Matching Bonus ($\Delta_{port}$)**:
   $$\Delta_{port} = \begin{cases} +1.5 & \text{if } \text{dest\_port}_{\text{vuln}} == \text{dest\_port}_{\text{attack}} \\ 0.0 & \text{otherwise} \end{cases}$$

3. **SIEM Severity Bonus ($\Delta_{severity}$)**:
   $$\Delta_{severity} = \begin{cases} +1.5 & \text{CRITICAL} \\ +1.0 & \text{HIGH} \\ +0.5 & \text{MEDIUM} \\ 0.0 & \text{LOW / INFO} \end{cases}$$

4. **Recency Bonus ($\Delta_{recency}$)**:
   $$\Delta_{recency} = \begin{cases} +1.0 & \text{if } t_{now} - t_{last} \le 24\text{ hours} \\ +0.5 & \text{if } 24\text{ hours} < t_{now} - t_{last} \le 48\text{ hours} \\ 0.0 & \text{otherwise} \end{cases}$$

---

## 5. REST API Endpoints Specification

### 1. `GET /api/threats/overview-kpis`
Returns platform headline metrics.

**Response Structure (`ThreatOverviewKPIs`)**:
```json
{
  "active_attacks_count": 42,
  "actively_exploited_cves_count": 3,
  "targeted_assets_count": 7,
  "total_hits_24h": 1845,
  "provider": "wazuh",
  "delta_attacks_pct": 14.5
}
```

### 2. `GET /api/threats/top-targeted-services`
Returns top 10 targeted network ports.

**Response Structure (`List[TopTargetedService]`)**:
```json
[
  {
    "port": 443,
    "service_name": "HTTPS",
    "total_hits": 850,
    "active_attacks": 12,
    "risk_level": "CRITICAL"
  },
  {
    "port": 22,
    "service_name": "SSH",
    "total_hits": 520,
    "active_attacks": 8,
    "risk_level": "HIGH"
  }
]
```

### 3. `GET /api/threats/activity-timeline`
Returns 48h histogram data points for time-series trend charting.

**Response Structure (`List[TimelineDataPoint]`)**:
```json
[
  {
    "timestamp": "2026-09-26T04:00:00Z",
    "total_hits": 120,
    "critical_hits": 15,
    "high_hits": 45,
    "medium_hits": 60
  }
]
```

### 4. `POST /api/settings/soc/test`
Validates real-time connectivity to the selected SOC/SIEM without saving configuration.

**Request Structure (`TestSocRequest`)**:
```json
{
  "soc_type": "wazuh",
  "wazuh_host": "10.0.0.50",
  "wazuh_port": 9200,
  "wazuh_index": "wazuh-alerts-*",
  "wazuh_user": "admin",
  "wazuh_password": "SecretPassword123!",
  "wazuh_ssl": true
}
```

**Response Structure**:
```json
{
  "success": true,
  "reachable": true,
  "events_count": 350,
  "message": "Successfully connected to Wazuh (10.0.0.50:9200). Fetched 350 telemetry attack events."
}
```

---

## 6. Verification & Automated Testing

The backend includes a comprehensive unit test suite in `rtms-web/backend/test_risk_correlator.py`:
- 16 unit tests covering `RiskCorrelator`, `SplunkThreatProvider`, `WazuhThreatProvider`, `SuricataThreatProvider`, `SentinelThreatProvider`, and `CrowdStrikeThreatProvider`.
- Execution command:
  ```bash
  cd /Users/marctritschler/git_projects/rtms-web/backend
  uv run python test_risk_correlator.py
  ```
