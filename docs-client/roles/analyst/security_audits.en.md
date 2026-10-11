# Integrated Security Audits (Non-Intrusive Plugins)

During intrusive inspection cycles (**Deep Scan**), RTMS triggers non-destructive automated security plugins to identify critical configuration vulnerabilities.

---

## 1. Email & Mail Server Security Audit (SMTP)

* **Open Mail Relay Detection (RFC 5321)**:  
  Probes whether an internal mail server accepts relaying messages to external untrusted domains without authentication.
  > **Safe Execution Guarantee**: The probe terminates the handshake immediately after `RCPT TO` and resets the TCP session with `RSET`, preventing actual email transmission.
* **Directory Harvesting & User Enumeration (`VRFY`)**:  
  Determines whether attackers can extract corporate email accounts.
* **In-Transit STARTTLS Encryption**:  
  Validates mandatory opportunistic TLS encryption and checks certificate validity.

---

## 2. DNS Integrity & Anti-Spoofing Verification

RTMS inspects corporate DNS resolvers to assess defenses against phishing and domain impersonation:
* **SPF (Sender Policy Framework)**: Validates TXT SPF syntax and hard-fail enforcement (`-all` vs weak `~all`).
* **DKIM (DomainKeys Identified Mail)**: Confirms public key publication and cryptographic strength across corporate selectors.
* **DMARC (Domain-based Message Authentication)**: Evaluates alignment policies (`p=reject` vs permissive `p=none`) and aggregate reporting settings.

---

## 3. Deprecated Protocols & Unprotected Databases

* **Windows SMB Shares & SMBv1 Audit**:  
  Triggers immediate alerts upon detecting legacy SMBv1 (vector for *WannaCry* / *EternalBlue*) or missing mandatory SMB message signing (susceptible to NTLM Relay attacks).
* **Unauthenticated Databases**:  
  Flags exposed PostgreSQL, MySQL/MariaDB, Redis, or MongoDB instances operating with default credentials or zero password authentication.

---

## 4. Cyber Hygiene & Email Security (Continuous NIS 2 Audit)

RTMS features a continuous evaluation engine for email security posture and transport encryption, displayed directly on the dashboard (**Cyber Hygiene & Email Security**).

### A. The 5 Evaluated Pillars
1. **🛡️ Anti-Spoofing (25 pts)**: Presence and strictness of SPF (`-all` or `~all`), DMARC enforcement (`p=reject` or `quarantine`), and DKIM selector cryptographic integrity.
2. **🔒 Transport & DANE (35 pts)**: Mandatory STARTTLS with modern encryption (TLS 1.3), Perfect Forward Secrecy (PFS) cipher suites, and TLSA (DANE) or MTA-STS certificate pinning.
3. **🔏 DNSSEC Zone (20 pts)**: Cryptographic signing of domain and MX DNS records (DS/DNSKEY chain of trust).
4. **🌐 IPv6 Dual-Stack (10 pts)**: Availability and IPv6 reachability of inbound mail servers.
5. **🛣️ RPKI Route Authorisations (10 pts)**: Validation of BGP Route Origin Authorizations (ROA) to prevent BGP hijacking.

### B. Autonomous Backend Scheduling
* **Background Worker Loop**: The RTMS backend executes automatic re-evaluations **every 12 hours** autonomously, guaranteeing fresh scores without requiring user interaction or depending on local sensor probes.
* **On-Demand Audit**: Operators can trigger an instantaneous recalculation at any time via the **"Detailed Audit"** button or in the scanner settings.

### C. Automated Remediation Task Lifecycle (Security Findings)
* **Finding Generation**: If the cyber hygiene score is below **80%** or exhibits critical vulnerabilities (e.g. spoofing risk), the platform automatically creates an actionable remediation task in **Security Findings** (`/findings`), assigned to the system administrator or security officer.
* **Dynamic Severity & Deadlines**:
  * Score < 50% or broken anti-spoofing: **CRITICAL** (due within 7 days).
  * Score between 50% and 70%: **HIGH** (due within 14 days).
  * Score between 70% and 80%: **MEDIUM** (due within 30 days).
* **Auto-Resolution**: Once the DNS or mail server remediation steps are published and validated by the next audit cycle (Score ≥ 80%), the task is automatically marked as **`RESOLVED`**.

