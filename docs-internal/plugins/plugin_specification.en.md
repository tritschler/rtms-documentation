# RTMS Suite - External Plugin Architecture & Specifications (`plugin.md`)

This document serves as the technical reference for developing, securing, validating, and managing the lifecycle of **external plugins** within the **Risk & Threat Management System (RTMS)** suite.

---

## 1. Architectural Overview & Design Philosophy

The **RTMS Scanner** engine employs a hybrid auditing architecture:
1. **Internal Plugins**: Pre-compiled and bundled directly within the native Nuitka executable (`rtms-scanner`).
2. **External Plugins**: Standalone Python scripts (`.py`) loaded dynamically at runtime during each scan cycle without requiring binary recompilation.

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RTMS Web Dashboard (Admin)                            │
│           • Upload .py script   • Enable / Disable Toggles   • Delete           │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND (/api/settings/plugins/upload)                   │
│  1. Strict file extension validation (.py only)                                  │
│  2. Static AST analysis (rtms_commons.plugin_validator.PluginCodeValidator)      │
│  3. Rejection of dangerous calls (os.system, subprocess, eval, ctypes, etc.)     │
│  4. Automated metadata extraction (self.info)                                    │
│  5. Disk storage ($RTMS_PLUGINS_DIR) & Indexing in admin.external_plugins        │
│  6. Immutable database audit logging (admin.system_audit)                       │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             RTMS SCANNER ENGINE                                 │
│  1. Target discovery & port sweeps (Nmap / ARP / SYN)                           │
│  2. Re-verification via AST before memory execution                             │
│  3. Dynamic secure import (importlib) & Instantiation                           │
│  4. Evaluate check_requirements(target_ip, target_services)                     │
│  5. Isolated execution run_audit(...) protected by Crash Guard                  │
│  6. Record findings into database schema and telemetry                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Security Policy & Static AST Validation Framework

To eliminate Remote Code Execution (RCE) risks when uploading custom Python auditing scripts, the framework enforces AST (**Abstract Syntax Tree**) validation using `rtms_commons.plugin_validator.PluginCodeValidator`.

### A. Golden Rule: Python Only (`.py`)
- Only files ending with the `.py` extension are accepted.
- All other extensions (`.txt`, `.sh`, `.bin`, `.exe`, etc.) are **strictly rejected** with `400 Bad Request`.

### B. Security Integrity & Forbidden Primitives
The source code is evaluated **before being imported into memory or executed**:

| Inspection Layer | Blocked Primitives | Security Rule |
| :--- | :--- | :--- |
| **Forbidden Modules** | `subprocess`, `shutil`, `ctypes`, `pty`, `pickle`, `posix`, `winreg` | **Immediate Rejection**: Prohibits OS shell invocation and low-level memory tampering. |
| **Dangerous Built-ins** | `eval()`, `exec()`, `compile()`, `__import__()` | **Immediate Rejection**: Prohibits opaque dynamic evaluation. |
| **System Mutators** | `.system()`, `.popen()`, `.spawn*()`, `.exec*()`, `.remove()`, `.unlink()`, `.rmdir()`, `.kill()` | **Immediate Rejection**: Protects the host filesystem and daemon processes. |
| **Syntax Validity** | Non-compilable Python 3 code | Rejected with exact line and column coordinates. |

### C. Interface Contract (`BasePlugin`)
Every plugin must strictly:
1. Inherit from `BasePlugin` (`from base_plugin import BasePlugin`).
2. Implement `check_requirements(self, target_ip, target_services)`.
3. Implement `run_audit(self, target_ip, target_services, credentials=None)`.

### D. Execution Crash Guard
In `base_plugin.py`, `execute()` encapsulates every audit invocation in a safe `try...except Exception` handler:
- An unhandled plugin exception (socket timeout, broken pipe, memory error) **never crashes the `rtms-scanner` daemon**.
- Errors are caught cleanly and registered with status `"Error"`.

---

## 3. Plugin Development Guide

### A. Minimal Compliant Template

```python
"""
my_plugin.py - Compliant RTMS Security Plugin Template
"""
from base_plugin import BasePlugin

class MyAuditPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        # Required metadata (extracted automatically during upload)
        self.info = {
            "name": "My Explicit Plugin Name",
            "description": "Concise summary of the audited security condition.",
            "severity": "Medium",  # Allowed: 'Info', 'Low', 'Medium', 'High', 'Critical'
            "cve": None,           # e.g., 'CVE-2024-XXXX' or None
            "version": "1.0.0"
        }

    def check_requirements(self, target_ip, target_services):
        """
        Determines whether the plugin should execute against this target.
        target_services is either a dict {port: "service_name"} or a list [80, 443].
        Returns True to execute, False to skip.
        """
        if isinstance(target_services, dict):
            return 6379 in target_services or 'redis' in str(target_services).lower()
        return 6379 in target_services

    def run_audit(self, target_ip, target_services, credentials=None):
        """
        Executes non-destructive network inspection logic.
        Must return self.format_result(status, proof, details).
        """
        # Recognized statuses: "OK", "Vulnerable", "Warning", "Skipped", "Error"
        return self.format_result(
            status="OK",
            proof="Port 6379 inspected successfully",
            details="Password authentication enforced and active."
        )
```

---

### B. Production Reference Example: SSL/TLS Certificate Audit (`ssl_tls_audit.py`)

Complete implementation deployed in `rtms-scanner/external_plugins/ssl_tls_audit.py`:

```python
import socket
import ssl
from datetime import datetime, timezone
from base_plugin import BasePlugin

class SslTlsAuditPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.info = {
            "name": "SSL/TLS Security & Certificate Audit",
            "description": "Audits HTTPS and SSL services for certificate expiration, self-signed certificates, and deprecated protocols (TLS 1.0/1.1).",
            "severity": "Medium",
            "cve": None,
            "version": "1.0.0"
        }
        self.ssl_ports = [443, 8443, 9443, 4433, 10443]
        self.discovered_ssl_ports = []

    def check_requirements(self, target_ip, target_services):
        self.discovered_ssl_ports = []
        if isinstance(target_services, dict):
            for port, s_name in target_services.items():
                s_name_lower = str(s_name).lower()
                if port in self.ssl_ports or "ssl" in s_name_lower or "https" in s_name_lower:
                    self.discovered_ssl_ports.append(port)
        elif isinstance(target_services, (list, set)):
            for port in self.ssl_ports:
                if port in target_services:
                    self.discovered_ssl_ports.append(port)

        return len(self.discovered_ssl_ports) > 0

    def run_audit(self, target_ip, target_services, credentials=None):
        findings = []
        is_vulnerable = False

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        for port in self.discovered_ssl_ports:
            try:
                with socket.create_connection((target_ip, port), timeout=5.0) as sock:
                    with ctx.wrap_socket(sock, server_hostname=target_ip) as ssock:
                        tls_version = ssock.version()
                        cert = ssock.getpeercert()

                        # Deprecated protocols
                        if tls_version in ("TLSv1", "TLSv1.1", "SSLv2", "SSLv3"):
                            is_vulnerable = True
                            findings.append(f"Port {port}: Deprecated protocol '{tls_version}' accepted (NIS2 non-compliance).")

                        # Expiration verification
                        if cert and "notAfter" in cert:
                            expire_str = cert["notAfter"]
                            expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                            days_left = (expire_dt - datetime.now(timezone.utc)).days

                            if days_left < 0:
                                is_vulnerable = True
                                findings.append(f"Port {port}: SSL certificate EXPIRED {abs(days_left)} days ago.")
                            elif days_left < 15:
                                findings.append(f"Port {port}: Certificate expiring soon ({days_left} days).")
                            else:
                                findings.append(f"Port {port}: Valid certificate ({tls_version}), expires in {days_left} days.")
                        else:
                            findings.append(f"Port {port}: Connected with {tls_version} (self-signed certificate).")
            except Exception as e:
                findings.append(f"Port {port}: TLS error: {str(e)}")

        status = "Vulnerable" if is_vulnerable else "OK"
        return self.format_result(status, proof=f"Audited ports: {self.discovered_ssl_ports}", details=" ; ".join(findings))
```

---

## 4. Plugin Catalog & Capabilities

| Plugin Name | Target Ports | Evaluated Threat / Condition | Severity | Type / Implementation |
| :--- | :--- | :--- | :--- | :--- |
| **Unauthenticated Databases** | 6379, 27017, 9200, 11211 | Redis, MongoDB, Elasticsearch exposed without authentication | **Critical** | **✅ INTERNAL (`unauth_database.py`)** |
| **Anonymous FTP Access** | 21 | FTP servers accepting `anonymous` guest logins | **Medium** | **✅ INTERNAL (`ftp_anonymous.py`)** |
| **SSL/TLS Certificate Audit** | 443, 8443, 9443 | Expired certificates, deprecated TLS 1.0/1.1, weak ciphers | **Medium** | **✅ EXTERNAL (`ssl_tls_audit.py`)** |
| **SMB & Message Signing Audit** | 445, 139 | Active SMBv1 (MS17-010 / EternalBlue), unsigned SMB (NTLM Relay) | **Critical / High** | **✅ INTERNAL (`smb_security.py`)** |
| **SSH Server Hardening** | 22 | Weak ciphers (3DES, RC4, CBC), SHA-1 KEX, regreSSHion (CVE-2024-6387) | **Critical / High** | **✅ INTERNAL (`ssh_hardening.py`)** |
| **Default Factory Credentials** | 80, 443, 8080, 23 | Routers, switches, cameras with default credentials (`admin:admin`, etc.) | **High** | **✅ INTERNAL (`default_credentials.py`)** |
| **SNMP Community Strings** | 161 UDP | Trivial community strings (`public`, `private`) granting MIB read/write | **Critical / High** | **✅ INTERNAL (`snmp_community.py`)** |
| **SMTP Security & Open Relay** | 25, 465, 587 | Unauthenticated Open Mail Relay, missing STARTTLS, VRFY user enumeration | **Critical / High** | **✅ INTERNAL (`smtp_security.py`)** |

---

## 5. Deployment, Registry & Database Audit Trail

### A. Filesystem Storage (`RTMS_PLUGINS_DIR`)
- **Production Mode**: `/opt/rtms/plugins/` (configured via `RTMS_PLUGINS_DIR`).
- **Development Mode**: `rtms-scanner/external_plugins/` or `rtms-web/backend/data/plugins/`.

Both the Web API and Scanner daemon share this path for instant synchronization.

### B. Database Registry (`admin.external_plugins`)
```sql
CREATE TABLE IF NOT EXISTS admin.external_plugins (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,       -- 'python'
    file_size_bytes BIGINT DEFAULT 0,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    author VARCHAR(255) DEFAULT 'Custom',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### C. Immutable Audit Log (`admin.system_audit`)

| Action | Trigger | Tracked Telemetry |
| :--- | :--- | :--- |
| **`EXTERNAL_PLUGIN_UPLOADED`** | Upload `.py` script | Timestamp, user, source IP, plugin name, filename, version, unique ID |
| **`EXTERNAL_PLUGIN_TOGGLED`** | Toggle switch | Timestamp, user, source IP, plugin ID, new state (`enabled=true/false`) |
| **`EXTERNAL_PLUGIN_DELETED`** | Click delete button | Timestamp, user, source IP, plugin name, deleted filename, version, ID |

---

## 6. Automated Testing & Verification

Execute the test suite:
```bash
cd rtms-commons
uv run python -m unittest tests/test_plugin_validator.py
```
Validates:
- Acceptance of valid plugins with accurate metadata parsing.
- Rejection of Python syntax errors with line/column coordinates.
- Enforcement against forbidden imports (`subprocess`, `shutil`, `ctypes`, etc.).
- Blocking of operating system mutators (`os.system`, `eval`, `exec`).
- Contract enforcement requiring inheritance from `BasePlugin`.
