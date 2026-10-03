# Email & DNS Security Audit (SPF, DKIM, DMARC, SMTP)

The **RTMS (Real-Time Monitoring System)** suite incorporates comprehensive email security and DNS resolution audit capabilities, engineered for both air-gapped / enterprise intranets and Internet-facing email architectures.

---

## 1. DNS Audit & Anti-Spoofing Verification (SPF, DKIM, DMARC)

The `dns_audits/dns_integrity.py` module evaluates DNS resolution integrity and validates domain email security policies against spoofing.

### Operation in Isolated Enterprise Networks

In an isolated intranet environment (without egress to public DNS servers like `1.1.1.1` or `8.8.8.8`):
* The scanner queries the **designated internal enterprise DNS server** or the operating system resolver (`/etc/resolv.conf` / Active Directory DNS).
* It verifies the syntax, presence, and alignment of email security records:
  * **SPF (`v=spf1 ...`)**: Validates internal and external IP addresses authorized to send mail.
  * **DMARC (`_dmarc.<domain>`)**: Verifies alignment policies (`p=none`, `quarantine`, or `reject`).
  * **DKIM (`<selector>._domainkey.<domain>`)**: Probes published public keys across standard and custom enterprise selectors.

### Configuration Properties

These parameters can be configured in `scanner.properties` or dynamically provisioned via the Web Console:

| Configuration Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dns.audit` | Boolean | `false` | Enables or disables DNS auditing during scan runs. |
| `dns.test.domain` | String | `example.com` | Target domain name to audit (e.g., `company.local`). |
| `dns.server` | String (IP) | *(empty)* | Internal corporate DNS IP (e.g., `10.0.0.53`). Falls back to system resolver if unset. |
| `dns.dkim_selectors` | CSV List | *(defaults)* | Specific DKIM selectors to test (e.g., `s1,corp,exchange`). |

---

## 2. Internal Security Plugin: SMTP Server Audit (`smtp_security.py`)

The internal security plugin [`internal_plugins/smtp_security.py`](file:///Users/marctritschler/git_projects/rtms-scanner/internal_plugins/smtp_security.py) audits mail servers discovered on the local network during deep scans.

### Execution Policy: Strict Deep Scan Only

> [!IMPORTANT]
> Adhering strictly to RTMS non-intrusive scanning principles, this plugin **NEVER runs during basic discovery (`CMD_DISCOVER`)**. It executes solely when **Deep Scan (`CMD_DISCOVER_SCAN` / `scanner.deep_scan = true`)** is active and mail ports are identified as open.

### Targeted Ports
* **Port 25 (Standard SMTP / Relay)**
* **Port 465 (SMTPS - Implicit TLS)**
* **Port 587 (SMTP Submission)**

### Security Checks Performed

1. **In-Transit Encryption (STARTTLS)**:
   * Probes whether the server advertises `STARTTLS`.
   * Flags a `MEDIUM` severity vulnerability if absent (unencrypted password transmission or plaintext eavesdropping on the LAN).
2. **Open Mail Relay Detection (RFC 5321)**:
   * Initiates an unauthenticated `MAIL FROM` transaction to an external mailbox via `RCPT TO:<untrusted-relay-test@example.org>`.
   * **Safe Probing Guarantee:** The scanner immediately issues an `RSET` (Reset) command. **No email is ever sent.**
   * If the relay accepts the recipient without requiring prior authentication, a `CRITICAL` alert is generated.
3. **User Account Enumeration (`VRFY` / `EXPN`)**:
   * Tests whether directory harvesting commands are permitted (generates a `LOW` finding).

### Plugin Configuration

* **Individual Plugin Disable**: `scanner.plugin.smtp_security = false`
* **Global Plugin Disable**: `scanner.internal_plugins_enabled = false`

---

## 3. Standalone External Tool: `tools/public_smtp_auditor.py`

To audit public Internet-facing SMTP servers outside the internal RTMS scan loop, an independent command-line auditor is included.

### Design & Portability

* **Zero Internal Dependencies:** This script does not import any proprietary RTMS modules.
* **Portable:** [`tools/public_smtp_auditor.py`](file:///Users/marctritschler/git_projects/rtms-scanner/tools/public_smtp_auditor.py) can be moved or copied into any standalone repository or administrative environment.

### Usage Examples

```bash
# Complete audit of a public domain (MX records + DNS SPF/DMARC/DKIM + SMTP Port checks)
python3 tools/public_smtp_auditor.py example.com

# Machine-readable JSON output for CI/CD pipelines
python3 tools/public_smtp_auditor.py --domain example.com --json

# Direct check against a specific mail server (IP or FQDN)
python3 tools/public_smtp_auditor.py --host mail.example.com --port 25

# Check on secure SMTPS port (465)
python3 tools/public_smtp_auditor.py --host mail.example.com --port 465 --ssl
```
