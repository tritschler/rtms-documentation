# Applied Standards & Technical Specifications

**Product:** [YOUR_SCANNER_NAME]
**Version:** [e.g., v1.x]
**Date:** [DATE]

This document lists the harmonised standards, technical specifications, and best practices applied during the design and development of this software to ensure conformity with the **EU Cyber Resilience Act (CRA)**.

## 1. Regulatory Framework
* **Regulation (EU) 2024/xxxx:** Horizontal cybersecurity requirements for products with digital elements (Cyber Resilience Act).
* **GDPR (Regulation (EU) 2016/679):** Data protection by design and by default (minimized data collection).

## 2. Technical Standards (Security)

### A. Vulnerability Management
* **ISO/IEC 29147:** Information technology — Security techniques — Vulnerability disclosure.
    * *Implementation:* `SECURITY.md` policy and dedicated email contact.
* **ISO/IEC 30111:** Information technology — Security techniques — Vulnerability handling processes.
    * *Implementation:* Internal triage process within 48h (SLA).

### B. Software Supply Chain & Transparency
* **CycloneDX v1.5:** Specification for Software Bill of Materials (SBOM).
    * *Implementation:* Automated generation via `cyclonedx-py` in CI/CD pipeline.
* **Package URL (PURL):** Standardized identification of software packages.

### C. Application Security
* **OWASP Top 10 (2021/2025):** Standard awareness document for web application security.
    * *Implementation:* Static Application Security Testing (SAST) using **Bandit** for Python.
* **CWE (Common Weakness Enumeration):**
    * *Focus:* Improper Input Validation (CWE-20), Hard-coded Credentials (CWE-798).

## 3. Cryptographic Standards
* **TLS 1.3:** Transport Layer Security for all network communications.
* **SHA-256:** Hashing algorithm used for file integrity verification.

## 4. Development Methodologies
* **Secure SDLC:** Security checks are integrated into the GitHub Actions workflow (Shift-Left Security).
* **Versioning:** Semantic Versioning 2.0.0 (SemVer).