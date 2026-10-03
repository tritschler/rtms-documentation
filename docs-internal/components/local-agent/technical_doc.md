# RTMS Local Agent - Technical Documentation

## 1. Architecture Overview & Execution Modes

The **RTMS Local Agent** is an endpoint security and software inventory daemon designed to operate seamlessly across Linux and macOS workstations and servers.

### Execution Modes
1. **Push Mode (`push`) [Default & Recommended]**:
   - Outbound HTTPS/HTTP only towards the RTMS Web Backend (`POST /api/agent/telemetry`).
   - **0 listening ports** on the client endpoint, eliminating inbound network exposure.
   - Periodic transmissions every configured interval (default: 3600s) with $\pm 5\%$ randomized jitter to avoid synchronous load spikes on central servers.
2. **Pull Mode (`pull`)**:
   - Exposes a lightweight Flask HTTP server listening on port `12000` (`GET /api/inventory`).
   - Polled on-demand by the central RTMS Scanner.
3. **Hybrid Mode (`hybrid`)**:
   - Combines periodic outbound push reports with concurrent listening on port `12000` for on-demand queries.

---

## 2. Configuration & Precedence

Configuration is resolved with strict hierarchical precedence:
1. **CLI Arguments**: `--mode`, `--server-url`, `--interval`, `--port`, `--token`.
2. **OS Environment Variables**: `RTMS_AGENT_MODE`, `RTMS_SERVER_URL`, `RTMS_PUSH_INTERVAL`, `RTMS_AGENT_PORT`, `RTMS_AGENT_TOKEN`.
3. **Local `.env` File**: Located in the application directory.
4. **Hardcoded Defaults**: Mode `push`, Server `http://localhost:8000`, Interval `3600s`, Port `12000`.

---

## 3. Zero-Trust Token Lifecycle & Auto-Enrollment

Each endpoint is authenticated individually using personal cryptographic tokens rather than a static shared key:

```
+------------------+                    +--------------------+
| RTMS Local Agent |                    |  RTMS Web Server   |
+------------------+                    +--------------------+
         |                                         |
         | --- 1. POST /api/agent/enroll --------> | (Verifies Master Key)
         |    (machine_id, hostname, mac,          | (Generates rtms_agt_...)
         |     Bearer Master Token)                | (Hashes with SHA-256)
         |                                         | (Stores in admin.agent_tokens)
         | <--- 2. Returns dedicated agent token - |
         |                                         |
         | [Saves to ~/.rtms_agent_token, 0o600]   |
         |                                         |
         | --- 3. POST /api/agent/telemetry -----> | (Validates SHA-256 Hash)
         |    (machine_id, inventory,              | (Anti-Spoofing: machine_id check)
         |     Bearer Dedicated Agent Token)       | (Rejects if REVOKED: HTTP 403)
         |                                         | (Updates last_used_at, last_ip)
         | <--- 4. HTTP 200 OK (Processed) ------- |
```

### Hardware Identity (`machine_id`)
The agent identifies the host persistently across IP changes and reboots:
- **Linux**: Reads `/etc/machine-id` or `/var/lib/dbus/machine-id`.
- **macOS**: Queries the native hardware UUID via `ioreg -rd1 -c IOPlatformExpertDevice` (`IOPlatformUUID`).
- **Fallback**: Persisted UUID in `~/.rtms_agent_machine_id`.

### Anti-Spoofing Protection
During telemetry ingestion, the server verifies that the payload's `machine_id` strictly matches the identity bound to the cryptographic token. Any mismatched report is blocked with `HTTP 403 (Agent token does not match machine identity)`.

### Administrative Revocation
Administrators can selectively revoke any agent's token from the RTMS Web Console (**Services Status**). The revocation takes effect immediately without needing server reboots, blocking rogue or decommissioned endpoints.

---

## 4. Telemetry Collection Engine

The agent collects:
1. **System & Resource Metrics**: Real-time CPU, RAM, and root filesystem usage.
2. **Software Inventory**:
   - Native package managers (`dpkg` on Debian/Ubuntu, `pacman` on Arch Linux, `rpm` on RHEL/Fedora).
   - Running process list cross-referenced against package database to flag untracked or dropped executables.
3. **Security Persistence Checks**:
   - Scans systemd service units (e.g. `/usr/lib/systemd/system/`) and cron directories for unauthorized modifications or persistence artifacts.
4. **Single-Instance Locking**:
   - Uses a POSIX lock file (`/tmp/rtms-local-agent.lock`) with non-blocking exclusive locking to prevent duplicate processes.
