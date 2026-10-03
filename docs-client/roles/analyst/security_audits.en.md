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
