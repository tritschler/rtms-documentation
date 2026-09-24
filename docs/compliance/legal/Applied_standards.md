# Applied Standards & Technical Specifications

**Product:** RTMS (Real-Time Monitoring & Security) Suite  
**Manufacturer:** 3TS Consulting SRL (Perwez, Belgium - BCE BE0805.449.891)  
**Version:** v1.x (Unified Web Portal, Scanner Engine, NVD Engine, Local Agent)  
**Date:** September 2026  

This document lists the harmonised European standards, technical specifications, and international best practices applied during the design, development, and operational maintenance of the RTMS software suite to guarantee strict conformity with the **EU Cyber Resilience Act (CRA)**.

## 1. Regulatory Framework
* **Regulation (EU) 2024/2847 (Cyber Resilience Act - CRA):** Horizontal cybersecurity requirements for products with digital elements. RTMS is classified as an **Important Product with Digital Elements (Class I - Annex III)** due to its core security functions (vulnerability discovery, network mapping, asset discovery, and anomaly detection).
* **Directive (EU) 2022/2555 (NIS 2):** High common level of cybersecurity across the Union (Articles 21.2(a) through 21.2(j)).
* **GDPR (Regulation (EU) 2016/679):** Data protection by design and by default (minimized data collection, local storage isolation, zero cloud exfiltration).

## 2. Technical Standards (Security & Vulnerability Management)

### A. Vulnerability Disclosure & Handling
* **ISO/IEC 29147:2018:** Information technology — Security techniques — Vulnerability disclosure (Coordinated Vulnerability Disclosure - CVD).
    * *Implementation:* Public `SECURITY.md` policy, designated security contact (`security@3ts-consulting.com`), PGP encryption support.
* **ISO/IEC 30111:2019:** Information technology — Security techniques — Vulnerability handling processes.
    * *Implementation:* Strict triage SLA (initial response < 48h, mitigation release plan), compliance with the CRA 24-hour mandatory early warning reporting obligation to national CSIRTs and ENISA for actively exploited zero-days.

### B. Software Supply Chain & Transparency
* **CycloneDX v1.5 (ECMA-424):** Universal standard specification for Software Bill of Materials (SBOM).
    * *Implementation:* Automated generation via CI/CD pipelines and built-in REST API export (`GET /api/compliance/sbom`).
* **Package URL (PURL specification):** Standardized package identification across Python (`pkg:pypi/`) and JavaScript/TypeScript (`pkg:npm/`) dependencies.

### C. Application & Network Security
* **OWASP Top 10 (2021/2025):** Core defense baseline against web application security risks.
    * *Implementation:* Static Application Security Testing (SAST) via Bandit/Semgrep, parameterized database queries (SQLAlchemy), strict CSRF/CORS barriers.
* **CWE (Common Weakness Enumeration):** Systematic mitigation of CWE-20 (Improper Input Validation), CWE-798 (Hard-coded Credentials), CWE-306 (Missing Authentication for Critical Function).
* **RFC 6238 / NIST SP 800-63B:** Mandatory TOTP Multi-Factor Authentication (MFA) for administrative access.

## 3. Cryptographic Standards & Integrity
* **TLS 1.2 / TLS 1.3:** Mandatory encrypted transport for all HTTP REST APIs and scanner-to-hub communications.
* **SHA-256:** Cryptographic checksum validation for database records, local archive diffs, and software release packages.
* **Ed25519 (RFC 8032):** High-speed, tamper-proof asymmetric digital signatures for appliance identity and VPS Support Hub synchronization.
* **RSA-2048 / SHA-256:** Cryptographic licensing engine validation and tamper-evident payload sealing.

## 4. Development Methodologies & Lifecycle
* **Secure SDLC (SSDLC):** Security by design and by default embedded across code reviews, automated unit testing, and dependency scanning.
* **Guaranteed Security Support Period:** 3TS Consulting commits to providing security patches and critical vulnerability fixes for a minimum of 5 years (until December 31, 2030) for each major RTMS release line.