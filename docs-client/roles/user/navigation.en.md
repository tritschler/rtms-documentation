# Getting Started & Interface Navigation

This guide is designed for network operators and users getting started with the **RTMS** web console.

---

## 1. Workspace Layout

The RTMS console is organized into three primary areas:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [🏢 Tenant / Plan]    [🔍 Search Cmd+K]     [⚙️]  [🌐 EN]  [🌙]  [👤 Profile]│
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
   * **Magic Global Search (🔍)**:
     * **Interactive Behavior**: Appears as a subtle magnifying glass icon that smoothly expands upon clicking or pressing the global keyboard shortcut **`Cmd + K`** (macOS) / **`Ctrl + K`** (Windows/Linux).
     * **Asset Searching**: Search instantaneously by IP address (full or partial CIDR), hostname, MAC address, hardware vendor (*Cisco*, *Dell*, *Apple*...), or operating system.
     * **Instant Module Shortcuts**: Type keywords to navigate directly to any suite module (e.g. *"alert"* $\rightarrow$ Security Alerts, *"cve"* $\rightarrow$ Vulnerabilities, *"triage"* $\rightarrow$ Threats, *"users"* $\rightarrow$ User Management, *"probe"* $\rightarrow$ Probe/Scanner Configuration).
     * **Submit via `Enter`**: Automatically navigates to the full asset inventory (`/assets`) with your search filter immediately applied.
     * **Quick Escape**: Press **`Esc`** or click outside to collapse the search pill.
   * **Settings Shortcut (⚙️)**: Direct one-click access to probe and network configuration (`/scanner`).
   * **Tenant & Subscription (Plan)**: Displays the active client organization and subscribed licensing tier.
   * **Language Selector**: Real-time language switching across interface and documentation (English, French, Dutch, German).
   * **Theme Switcher**: Instant toggle between **Dark Mode** (optimized for SOC operations) and **Light Mode (Daylight)**.
   * **Profile & Session Menu**: Account inspection, password rotation, and Multi-Factor Authentication (MFA / TOTP) management.

2. **Left Navigation Sidebar (Dynamic Sidebar)**:
   * The sidebar content is **fully dynamic** and adapts in real time based on:
     1. The **subscribed license edition** (active modules and enterprise add-ons).
     2. Your **RBAC user role** (`admin`, `analyst`, `auditor`, `user`), automatically restricting unauthorized views according to the Principle of Least Privilege.

3. **Main Content Workspace**:
   * Interactive tables, deep inspection drawers, and risk analytics charts.

---

## 2. Interactive Tables & Filtering

All tables across the RTMS platform provide standard controls:
* **Multi-Column Sorting**: Click any column header (e.g. Last Seen, Criticality, IP Address) to reorder data.
* **Quick Status Filters**: Filter by active assets (`Online`), offline hosts, or critical vulnerabilities with a single click.
* **Pagination & Row Density**: Display 10, 25, 50, or 100 rows per page according to preference.
