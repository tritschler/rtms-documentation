# Release & Maintenance Strategy - RTMS Suite

**Project:** RTMS Vulnerability Scanner & Network Auditing Suite  
**Organization:** 3TS Cybersecurity SRL  
**Core Technology Stack:** Python, React, Nginx, PostgreSQL  

---

## 1. Philosophy & Core Principles

The objective of this release strategy is to guarantee operational stability and security across enterprise networks while delivering feature enhancements predictably.

Because individual stack dependencies (Python, React, Nginx) evolve on asynchronous release schedules, RTMS releases are deliberately **decoupled from third-party zero-day upstream releases**, prioritizing proven and battle-tested patch versions:

* **Python:** Major upstream release in October. RTMS migration is deferred to patch version `.1` or `.2` (Q1 of following year) to bypass initial edge-case interpreter defects.
* **Nginx:** Mainline to stable branch sync during spring maintenance.
* **React:** Continuous minor patch adoption with backward compatibility guarantees.

---

## 2. Annual Release Calendar

The RTMS lifecycle follows two predictable bi-annual major milestones, supplemented by continuous asynchronous hotfixes:

### Spring Release (March / April): "Tech & Features"
Focuses on technological foundation upgrades and architectural refactoring:
* **Key Actions:**
  * Adoption of latest stable major Python runtime.
  * Upgrade to the latest stable Nginx branch.
  * Major React dependency baseline upgrades.
  * Deployment of structural network analysis engines.
* **Impact:** May introduce breaking changes requiring a major version increment.

### Autumn Release (October / November): "Features & Consolidation"
Focuses on operational user value, telemetry analytics, and performance optimization, deliberately skipping the freshly released upstream Python version:
* **Key Actions:**
  * Delivery of new UI capabilities and analysis scripts.
  * Probing speed and correlation optimizations.
  * Global codebase consolidation and hardening.
* **Impact:** Minor release, fully backward-compatible.

---

## 3. Asynchronous Hotfix Management

Security and platform stability cannot wait for bi-annual windows. Critical patches deploy asynchronously via CI/CD automation:

* **Application Defects:** Created on a `hotfix/*` branch from `main`. Formally tested and deployed immediately.
* **Upstream CVEs:**
  * Continuous automated scanning of Python and npm supply chains.
  * When a high/critical CVE affects a dependency, a security-only patch version is generated and distributed without functional alterations.

---

## 4. Semantic Versioning Specification

RTMS adheres strictly to `Major.Minor.Patch` (e.g. `2.1.3`):

* **Major (e.g. 2.0.0):** Architectural modernization or breaking changes. Typically aligned with Spring releases.
* **Minor (e.g. 1.3.0):** Additive features and scanning capabilities, fully backward-compatible. Typically aligned with Autumn releases.
* **Patch (e.g. 1.2.4):** Reserved exclusively for bug fixes and CVE remediation. Zero functional modifications.

---

## 5. Distribution via Central VPS Support Hub

Package delivery and version manifest publication leverage the **VPS Support Hub** gateway (`rtms-admin/vps-support-hub`) hosted on OVH:

```
┌─────────────────────────────────┐
│       3TS Build Station         │
│      ./build_releases.sh        │
└─────────────────────────────────┘
                │
                │ scp *.tar.gz & POST /api/v1/updates/releases
                ▼
┌─────────────────────────────────────────────────────────────┐
│             RTMS Central VPS Support Hub                    │
│   • packages/ (*.tar.gz archives)                           │
│   • PostgreSQL: software_releases table                     │
│   • GET /api/v1/version (Active manifest)                   │
│   • GET /api/v1/updates/packages/{package_name}             │
└─────────────────────────────────────────────────────────────┘
                │
                │ HTTPS REST API Polling / "Check for Updates"
                ▼
┌─────────────────────────────────────────────────────────────┐
│             RTMS Web Client Appliance                       │
│   • /api/system/updates/status (detects new releases)       │
│   • /api/system/updates/apply (stage & SHA-256 validation)  │
│   • updates/downloads/ (secure local staging)               │
└─────────────────────────────────────────────────────────────┘
```

### Release Pipeline Stages:
1. **Artifact Compilation**: `build_releases.sh` packages components (`rtms-scanner-release.tar.gz`, `rtms-nvd-onprem-release.tar.gz`, etc.).
2. **Distribution Upload**: Archives upload to `/opt/rtms-support-hub/packages/`.
3. **Manifest Publishing**: Authenticated `POST /api/v1/updates/releases` registers component versions and SHA-256 hashes in `software_releases`.
4. **Appliance Detection & Ingestion**:
   * Client appliances poll `GET /api/v1/version` comparing against local `APP_VERSION`.
   * On operator approval, `POST /api/system/updates/apply` streams the archives, verifies **SHA-256** checksums, applies staged binaries, and records the event in `admin.system_audit`.
5. **Air-Gapped Resilience**: For air-gapped environments, `.tar.gz` bundles can be manually dropped onto the appliance filesystem, triggering local offline ingestion seamlessly.
