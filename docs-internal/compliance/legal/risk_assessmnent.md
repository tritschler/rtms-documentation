# Cybersecurity Risk Assessment
**Product:** [YOUR_SCANNER_NAME]
**Last Updated:** [DATE]

This document records the cybersecurity risks identified during the development of the scanner and the mitigation measures applied, in accordance with the Cyber Resilience Act (Security by Design).

## Risk Matrix Legend
* **Impact:** Low, Medium, High, Critical
* **Likelihood:** Rare, Unlikely, Possible, Likely
* **Status:** ✅ Mitigated, 🔄 In Progress, ❌ Open

## Threat Modeling & Risk Log

| ID | Risk Description | Likelihood | Impact | Mitigation Strategy (Technical Measures) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | **Malicious Image Injection (RCE)**<br>An attacker uploads a crafted image (e.g., 'decompression bomb' or exploit) to crash the scanner or execute code via the parsing library. | Possible | Critical | 1. Use of `Pillow` library with latest security patches.<br>2. Implementation of strict file size and dimension limits.<br>3. Input validation: Verify file headers (Magic Numbers) before processing. | ✅ Mitigated |
| **R-02** | **Supply Chain Attack**<br>A dependency (pip package) used by the scanner is compromised or contains a known vulnerability (CVE). | Likely | High | 1. Automated SBOM generation (CycloneDX).<br>2. Weekly vulnerability scanning via GitHub Actions (Trivy).<br>3. Dependency pinning in `requirements.txt` (using exact versions). | ✅ Mitigated |
| **R-03** | **Sensitive Data Leak**<br>Scanned documents containing PII are intercepted during network transmission. | Unlikely | High | 1. Enforced TLS 1.3 for all network communications.<br>2. Certificate validation (no self-signed certs allowed in production). | ✅ Mitigated |
| **R-04** | **Hardcoded Secrets**<br>API keys or credentials found in source code could be extracted by reverse engineering. | Possible | High | 1. Use of Environment Variables (`os.getenv`) for all secrets.<br>2. Static Code Analysis (Bandit) in CI/CD pipeline to detect hardcoded strings. | ✅ Mitigated |
| **R-05** | **Lack of Security Updates**<br>Users run an outdated version with known vulnerabilities. | Likely | Medium | 1. The application checks for updates at startup.<br>2. "End of Life" policy published in `SECURITY.md`. | 🔄 In Progress |

## Conclusion
Based on the mitigation measures implemented above, the residual risk is considered acceptable for the intended use of this product.