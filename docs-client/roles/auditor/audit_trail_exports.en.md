# Audit Trail & Regulatory Compliance Exports

The RTMS audit framework guarantees immutable traceability of platform activities and provides export capabilities satisfying regulatory compliance reviews.

---

## 1. Immutable Audit Logging

All sensitive administrative and operational events are recorded in an append-only audit trail:
* **Authentication & Access**: Successful and failed login attempts, remote IP address, authentication mechanism (Local, LDAP, SSO Keycloak), and precise UTC timestamp.
* **Vulnerability Triage & Risk Acceptance**: Every analytical status modification (e.g. marking as false-positive or accepting risk) records the author, timestamp, and formal operational justification.
* **Configuration & Policy Modifications**: Subnet provisioning, scan timing adjustments, probe token generation or revocation.

---

## 2. Report Generation & Exports

Compliance auditors can generate and download audit evidence on demand:
* **Global Asset Inventory (CSV / Excel)**: Comprehensive asset mapping, MAC addresses, hardware vendors, operating systems, and open ports.
* **Executive Vulnerability Summary (PDF)**: High-level overview of enterprise risk posture, CVSS distribution, and remediation progress.
* **NIS 2 Compliance Assessment**: Point-by-point compliance report directly addressing Articles 21 and 23 of the European directive.
