# RTMS Documentation

Welcome to the central documentation repository for the **RTMS (Real-Time Monitoring & Security)** platform.

This repository serves as the **Single Source of Truth** for overall system architecture, technical specifications, cross-cutting features, security compliance, and deployment guides.

---

## Running the Documentation Site (MkDocs Material)

To browse this documentation with the interactive, dark/light themed Material portal:

```bash
# Start local live-reloading web server (http://127.0.0.1:8000)
uv run mkdocs serve

# Build production static website (output: site/)
uv run mkdocs build
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