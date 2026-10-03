# Role-Based Access Control (RBAC) Security Model

The RTMS platform implements a granular **RBAC (Role-Based Access Control)** model featuring 4 operational roles. It is specifically designed to reflect real-world SOC workflows, network engineering tasks, and regulatory compliance auditing (**NIS 2 / ISO 27001**).

---

## 1. Core Principles

The security model rests upon three pillars:
1. **Principle of Least Privilege**: Each user is granted only the permissions strictly required for their job function.
2. **Segregation of Duties**: Infrastructure and network operations are segregated from risk triage and formal vulnerability acceptance (handled by SOC analysts).
3. **Immutable & Isolated Audit Trail**: Access to compliance and security audit logs (`/api/audit/*`) is strictly guarded. Network operators cannot view audit logs (preventing concealment risks), whereas compliance auditors (`viewer`) have full visibility without any mutation rights.

---

## 2. The 4 Operational Roles

| Role | Designation | Missions & Responsibilities |
| :--- | :--- | :--- |
| **`admin`** | System Administrator | Full control over the platform. User management, license administration, system settings, service lifecycle (start/stop), and orphan record purges. |
| **`security_analyst`** | SOC / Security Analyst | CVE vulnerability triage, formal risk acceptance with justification, finding creation/assignment, intrusion alert handling, and verification scan triggering. |
| **`operator`** | Network / Scanner Operator | Day-to-day asset operations (editing, IP exclusions, subnet renaming, asset deletion), scanner configuration, direct scanner restarts (`RESTART`), local agent token lifecycle management, and discovery scans. |
| **`viewer`** | Auditor / Compliance | Read-only inspection of topology maps, asset inventory, vulnerabilities, and **compliance audit logs** (`/api/audit/*`) for regulatory evidence (NIS 2 / ISO 27001). **Zero mutation or action permissions.** |

---

## 3. Permissions Matrix

| Functional Area / Endpoint | `admin` | `security_analyst` | `operator` | `viewer` (Auditor) |
| :--- | :---: | :---: | :---: | :---: |
| **User & Role Management** (`/api/users*`) | ✅ Yes | ❌ 403 | ❌ 403 | ❌ 403 |
| **System Settings & Licenses** (`/api/license*`, `/api/system/*`) | ✅ Yes | ❌ 403 | ❌ 403 | ❌ 403 |
| **System & Login Audit Logs** (`/api/audit/*`) | ✅ Yes | ✅ Yes | ❌ 403 | ✅ **Yes (NIS 2 Evidence)** |
| **Start / Stop / Pause Services** | ✅ Yes | ❌ 403 | ❌ 403 | ❌ 403 |
| **Restart Network Scanner (`RESTART`)** | ✅ Yes | ❌ 403 | ✅ Yes | ❌ 403 |
| **Local Agent Token Management** (Revoke / Reactivate) | ✅ Yes | ❌ 403 | ✅ Yes | ❌ 403 |
| **Trigger Network Scans** (`/api/services/scanner/trigger`) | ✅ Yes | ✅ Yes | ✅ Yes | ❌ 403 |
| **Asset Management** (Edit Hostname, Exclude IP, Ports) | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Read-Only |
| **Asset Deletion & Subnet Renaming** | ✅ Yes | ❌ 403 | ✅ Yes | ❌ 403 |
| **Purge Orphan Assets** (`/api/assets/purge-orphans`) | ✅ Yes | ❌ 403 | ❌ 403 | ❌ 403 |
| **Software Inventory** (Add, Edit Version, Delete) | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Read-Only |
| **CVE Risk Acceptance** (`/api/vulnerabilities/accept_risk`) | ✅ Yes | ✅ **Yes (SOC)** | ❌ 403 | ❌ 403 |
| **Security Findings Creation & Assignment** (`/api/findings*`) | ✅ Yes | ✅ **Yes (SOC)** | ❌ 403 | ❌ 403 |
| **Update Finding Status** (In Remediation, Resolved) | ✅ Yes | ✅ Yes | ✅ Yes (Ops) | ❌ Read-Only |
| **Intrusion Alerts Management** (Dismiss, Resolve, MAC Whitelist) | ✅ Yes | ✅ **Yes (SOC)** | ❌ 403 | ❌ 403 |

---

## 4. Backend Implementation (FastAPI)

In `backend/main.py`, access control is enforced at the HTTP route level using FastAPI's dependency injection (`Depends(...)`).

Each authenticated request validates the JWT token, resolves the user's role from `admin.users`, and enforces strict guard functions:

```python
def get_current_user_profile(username: str = Depends(get_current_user)) -> dict:
    """Validates active user and resolves their RBAC role."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT role, is_active FROM admin.users WHERE username = :u"),
            {"u": username}
        ).fetchone()
        if not result or not result[1]:
            raise HTTPException(status_code=401, detail="User not active or not found")
        raw_role = (result[0] or "viewer").lower().strip()
        role = "viewer" if raw_role == "user" else raw_role
        return {"username": username, "role": role}

def verify_admin(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized. Admin role required.")
    return user["username"]

def verify_security_analyst_or_admin(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst'):
        raise HTTPException(status_code=403, detail="Not authorized. Security Analyst or Admin role required.")
    return user["username"]

def verify_operator_or_admin(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'operator'):
        raise HTTPException(status_code=403, detail="Not authorized. Operator or Admin role required.")
    return user["username"]

def verify_can_operate(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst', 'operator'):
        raise HTTPException(status_code=403, detail="Not authorized. Read-write role required.")
    return user["username"]

def verify_can_scan(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst', 'operator'):
        raise HTTPException(status_code=403, detail="Not authorized. Scan execution role required.")
    return user["username"]

def verify_can_view_audit(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst', 'viewer'):
        raise HTTPException(status_code=403, detail="Not authorized to inspect audit logs.")
    return user["username"]
```

---

## 5. Root Administrator Account Protection

The initial `admin` account (Super Admin) is natively protected:
* Cannot be demoted or have its role changed.
* Cannot be deactivated or deleted.
* Enforced both at the backend API level (`update_user`) and locked in the frontend UI (`UserManagement.tsx`).

---

## 6. Regulatory Compliance (NIS 2 & ISO 27001)

The RBAC implementation directly satisfies regulatory security controls:
* **NIS 2 Article 21 (2.i)**: Basic cyber hygiene, access control policies, and user privilege management.
* **ISO/IEC 27001 - Control A.9.2**: User access provisioning and allocation of privileged access rights.
* **ISO/IEC 27001 - Control A.12.4**: Logging and monitoring, with tamper-protection ensuring non-administrative users cannot falsify or wipe logs.
