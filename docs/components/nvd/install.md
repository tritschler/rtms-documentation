# Installation Guide

## Operating Systems
* Linux
* macOS
* Windows

### Linux Requirements
* User: `rtms-nvd` with passwordless `sudo` privileges.

## Database
* **PostgreSQL**: Version 16+
* **User (Service)**: `rtms_nvd_user` (Accès restreint au schéma `nvd` + configuration & heartbeat dans `admin`)
* **User (Owner/Migration)**: `rtms_user`
* **Database**: `rtms_db`

Pour la mise en place sécurisée et le durcissement conforme NIS 2, consultez le [Guide d'Installation & Durcissement PostgreSQL](../../deployment/postgres_hardening_guide.md).

## NIST API Key
A valid NIST API key is required. You can request one from the [NVD Developers Portal](https://nvd.nist.gov/developers/request-an-api-key).

## Alerts
The `admin.cve_alerts_config` table holds the alert configurations (emails, Microsoft Teams Webhooks, and Slack Webhooks).

Example SQL to insert a Teams webhook configuration for critical vulnerabilities (CVSS $\ge$ 8.0):

```sql
-- Insert a Teams webhook configuration for critical vulnerabilities (CVSS >= 8.0)
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
    'https://[TON_WEBHOOK_URL_MICROSOFT_TEAMS]', 
    8.0, 
    true
);
```

Example SQL to insert a Slack webhook configuration for critical vulnerabilities (CVSS $\ge$ 8.0):

```sql
-- Insert a Slack webhook configuration for critical vulnerabilities (CVSS >= 8.0)
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
    'https://example.com/services/YOUR/SLACK/WEBHOOK', 
    8.0, 
    true
);
```

## License
A valid license is required, which is linked to the hardware ID and signed with a private key.
Without a valid license, the software will start in **demo mode** with limited capabilities.

The license can be provided in one of two ways:
1. Environment variable: `RTMS_LICENSE`
2. Database table: `license.licenses`

## Environment Variables
The following environment variables are required to be set:

```env
RTMS_POSTGRES_PASSWORD=xxxx
RTMS_NVD_API_KEY=xxxx
```
