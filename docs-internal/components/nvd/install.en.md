# Installation Guide: RTMS NVD

## Operating Systems
* Linux
* macOS
* Windows

### Linux Requirements
* User: `rtms-nvd` with passwordless `sudo` privileges.

## Database
* **PostgreSQL**: Version 16+
* **Service Role**: `rtms_nvd_user` (Scoped access to schema `nvd` + configuration & heartbeat in `admin`)
* **Owner Role**: `rtms_user`
* **Database**: `rtms_db`

For detailed setup and NIS2 hardening, see the [PostgreSQL Hardening Guide](../../deployment/postgres_hardening_guide.md).

## NIST API Key
A valid NIST API key is required. You can request one from the [NVD Developers Portal](https://nvd.nist.gov/developers/request-an-api-key).

## Alerts
The `admin.cve_alerts_config` table stores notification destinations (Email, Microsoft Teams Webhooks, Slack Webhooks).

Example SQL to configure a Teams webhook for critical vulnerabilities (CVSS $\ge$ 8.0):

```sql
INSERT INTO admin.cve_alerts_config (
    tenant_id, 
    channel_name, 
    channel_type, 
    destination_url, 
    trigger_threshold, 
    is_active
) VALUES (
    '3TS', 
    'Teams SOC', 
    'TEAMS', 
    'https://[YOUR_TEAMS_WEBHOOK_URL]', 
    8.0, 
    true
);
```

Example SQL for a Slack webhook:

```sql
INSERT INTO admin.cve_alerts_config (
    tenant_id, 
    channel_name, 
    channel_type, 
    destination_url, 
    trigger_threshold, 
    is_active
) VALUES (
    '3TS', 
    'Slack SOC', 
    'SLACK', 
    'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK', 
    8.0, 
    true
);
```

## License
A valid license is required, tied to the hardware fingerprint and signed cryptographically.
Without a valid license, the software starts in **demo mode** with constrained functionality.

The license can be supplied via:
1. Environment variable: `RTMS_LICENSE`
2. Database table: `admin.product_license`

## Environment Variables
The following environment variables are required:

```env
RTMS_POSTGRES_PASSWORD=xxxx
RTMS_NVD_API_KEY=xxxx
```
