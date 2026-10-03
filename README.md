# RTMS Documentation

Welcome to the central documentation repository for the **RTMS (Real-Time Monitoring & Security)** platform.

This repository serves as the **Single Source of Truth** for the entire RTMS platform, split into **two distinct documentation spheres**:

1. 🔒 **Internal Technical Portal (`docs-internal/`)**:
   * Destined exclusively for **3TS Consulting SRL**, core engineers, nomadic installers, and AI development agents.
   * Covers internal system architecture, data models, Ansible deployment playbooks, PostgreSQL hardening, scanner internals, and licensing.
   * Built via `mkdocs.internal.yml` $\rightarrow$ `site-internal/` (local server: `http://127.0.0.1:8008`).

2. 👥 **Client & User Guide (`docs-client/`)**:
   * Destined for **end-clients and operators**, served in HTML via Nginx and embedded directly inside the RTMS Web Console (`/help/documentation`).
   * Structured by the **4 RTMS RBAC Roles**:
     * 🔰 **1. Opérateur & Utilisateur Réseau** (Prise en main, Inventaire des actifs, Alertes)
     * 🛡️ **2. Analyste de Sécurité / SOC** (Dashboard Menaces, Triage CVE, Corrélation SIEM)
     * 📋 **3. Auditeur & Conformité** (Directive NIS2, Cyber Resilience Act CRA, Journal d'audit)
     * ⚙️ **4. Administrateur Client** (Utilisateurs RBAC, Gestion des sondes, Deep Scan, CMDB)
   * Built via `mkdocs.client.yml` $\rightarrow$ `site-client/` (local server: `http://127.0.0.1:8009`).

---

## 🛠️ Build & Serve Commands (Makefile)

A `Makefile` is provided for convenient building and local preview:

```bash
# Compile both documentations strictly
make build-all

# Compile individually
make build-internal   # Outputs to site-internal/
make build-client     # Outputs to site-client/

# Run local preview servers
make serve-internal   # Live on http://127.0.0.1:8008
make serve-client     # Live on http://127.0.0.1:8009
```

---

## Table of Contents

### 1. Architecture & Data Flow
* [**Global System Overview**](docs/architecture/overview.md) — Architecture diagrams, components breakdown, and inter-service communication protocols.
* [**Network & WireGuard Guide**](docs/architecture/wireguard.md) — Multi-site tunneling and scanner connectivity via WireGuard.
* **Data Models:**
  * [Scanner Data Model](docs/architecture/data_models/scanner_data_model.md) — Probing database schema, host discovery tables, and scan results.
  * [NVD Data Model](docs/architecture/data_models/nvd_data_model.md) — CVE database schema, CPE mappings, and CVSS scoring tables.

### 2. Component Technical Documentation
Detailed technical specifications for each individual subsystem:
* **RTMS Scanner (`rtms-scanner`):**
  * [Technical Requirements (EN)](docs/components/scanner/technical_requirements_en.md) / [Requirements (FR)](docs/components/scanner/technical_requirements_fr.md)
  * [Standalone Mode Guide](docs/components/scanner/stand_alone.md)
  * [Versions & Changelog](docs/components/scanner/versions.md)
* **RTMS Web (`rtms-web`):**
  * [Web Platform Technical Documentation](docs/components/web/technical_documentation.md) — FastAPI endpoints, React frontend architecture, WebSocket feeds.
  * [Production Nginx & Frontend Setup](docs/components/web/frontend_nginx_setup.md)
  * [Enterprise SSO Keycloak & OIDC Integration](docs/components/web/sso_keycloak_guide.md)
  * [Web Backend Startup Guide](docs/components/web/startup.md)
* **RTMS Local Agent (`rtms-local-agent`):**
  * [Agent Technical Architecture](docs/components/local-agent/technical_doc.md) — Host metrics, package inventory, and process polling.
  * [Agent Installation Guide](docs/components/local-agent/install.md)
* **RTMS NVD Microservice (`rtms-nvd`):**
  * [NVD Service Documentation](docs/components/nvd/rtms_nvd_documentation.md) — Local CVE mirror and lookup engine.
  * [Installation Guide](docs/components/nvd/install.md)
  * [Startup & Ingestion Guide](docs/components/nvd/readme_startup.md)
  * [Exporting CVE Reports](docs/components/nvd/readme_export_cve.md)
* **RTMS Admin & CLI (`rtms-admin`):**
  * [Admin Tools & Management](docs/components/admin/admin_guide.md)

### 3. Extensible Plugin Framework
* [**Plugin Specification & Developer Guide**](docs/plugins/plugin_specification.md) — Architecture of the hot-reloadable Python security plugin system, AST safety validator rules, lifecycle hooks, and plugin authoring tutorial.

### 4. Governance, Compliance & Releases
* [**NIS2 Compliance Specification**](docs/compliance/nis2.md) — Complete mapping of RTMS security controls to the European NIS2 Directive articles.
* [**Software Licenses & Legal Notices**](docs/compliance/licenses.md) — Licensing terms, third-party libraries, and proprietary software copyrights.
* [**Release & Versioning Strategy**](docs/compliance/release_strategy.md) — Semantic versioning and deployment lifecycle across the RTMS stack.

---

## Repository Ecosystem

```
git_projects/
├── rtms-documentation/    # Central documentation portal (this repository)
├── rtms-web/              # Central Web Dashboard & REST API
├── rtms-scanner/          # Network discovery & auditing probe engine
├── rtms-commons/          # Shared Python libraries & AST plugin validator
├── rtms-local-agent/      # Deep inspection endpoint agent
├── rtms-nvd/              # Offline CVE ingestion and search service
├── rtms-installer/        # Automation scripts & systemd services
└── rtms-admin/            # Central administration CLI & WireGuard tools
```

> **Developer Note:** Each individual repository contains a concise `README.md` covering local environment setup (`uv sync`, `npm install`), test suites (`pytest`), and environment variables.