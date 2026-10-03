# User Management & Role-Based Access Control (RBAC)

The User Administration console (`/admin/users`) configures accounts, access permissions, and authentication governance for your enterprise.

---

## 1. Available Roles & Permissions Matrix

RTMS enforces a strict Role-Based Access Control (**RBAC**) model:

| Role | Operational Scope & Permissions | Recommended Persona |
| :--- | :--- | :--- |
| **Administrator (`admin`)** | Full platform control: user provisioning, probe settings, network policies, API tokens, SSO/LDAP integration. | IT Director, Lead Security Engineer |
| **SOC Analyst (`security_analyst`)** | Vulnerability triage, threat investigation, alert management, on-demand scan triggering. | SOC Team, Cyber Defense Analyst |
| **Compliance Auditor (`viewer`)** | Read-only inspection across all modules, access to audit trails, and NIS2 compliance reporting. | Internal/External Auditor, CISO, DPO |
| **Operator (`operator`)** | Operational asset editing, host exclusions, and discovery sweeps. | Network Engineer, Systems Administrator |

---

## 2. Password Governance & Multi-Factor Authentication (MFA)

* **Multi-Factor Authentication (MFA / TOTP)**:
  Mandatory for administrative access. Enrolled via standard authenticator apps (Google Authenticator, Microsoft Authenticator, FreeOTP).
* **Adaptive Risk-Based Password Expiration**:
  Enforces a 90-day expiration window with J-14 advance notifications for accounts without MFA. Accounts protected by MFA are permanently exempt from periodic rotation in alignment with NIST SP 800-63B and ISO 27001.
* **Corporate Directory & SSO Integration (LDAP / OIDC)**:
  Direct integration with Active Directory, OpenLDAP, or enterprise identity providers (Keycloak, Okta, Microsoft Entra ID).
