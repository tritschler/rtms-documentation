# Getting Started & Interface Navigation

This guide is designed for network operators and users getting started with the **RTMS** web console.

---

## 1. Workspace Layout

The RTMS console is organized into three primary areas:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [3TS RTMS Logo]       Global Search (IP, Host, MAC...)        [Profile]│
├─────────────┬──────────────────────────────────────────────────────────┤
│ 📊 Dashboard│                                                          │
│ 🖥️ Assets   │                                                          │
│ ⚠️ Alerts   │                     MAIN WORKSPACE                       │
│ 🛡️ Threats  │               (Tables, Visual Analytics,                 │
│ 📋 Complianc│                  Detailed Asset Profiles)                │
│ ⚙️ Admin     │                                                          │
│ 📖 Docs      │                                                          │
└─────────────┴──────────────────────────────────────────────────────────┘
```

1. **Top Header**:
   * **Global Search**: Filter instantaneously by IP address, hostname, vendor, or MAC address.
   * **Theme Switcher**: Toggle between Dark Mode (ideal for SOC environments) and Light Mode.
   * **Language Selector**: Switch interface and embedded documentation between English and French.
   * **Profile & Session Menu**: Inspect account details and assigned RBAC role.

2. **Left Navigation Sidebar**:
   * One-click navigation to asset inventories, security alerts, NIS2 dashboards, and system settings.

3. **Main Content Workspace**:
   * Interactive tables, deep inspection drawers, and risk analytics charts.

---

## 2. Interactive Tables & Filtering

All tables across the RTMS platform provide standard controls:
* **Multi-Column Sorting**: Click any column header (e.g. Last Seen, Criticality, IP Address) to reorder data.
* **Quick Status Filters**: Filter by active assets (`Online`), offline hosts, or critical vulnerabilities with a single click.
* **Pagination & Row Density**: Display 10, 25, 50, or 100 rows per page according to preference.
