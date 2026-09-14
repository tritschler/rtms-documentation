# RTMS (Real-Time Monitoring System) - Technical Requirements

This document details the hardware, software, and network prerequisites necessary for deploying the RTMS (Real-Time Monitoring System) software solution by 3TS Consulting.

RTMS is a 100% software-based solution. It is designed to adapt to the client's existing infrastructure, offering two main deployment methods: a containerized installation (Docker) or a native installation (Bare-Metal/VM) compatible with Windows, macOS, and Linux.

---

## 1. Hardware Prerequisites (All installations)

The performance of RTMS depends on the size of the network to be audited and the frequency of threat database (NVD) synchronizations.

*   **Processor (CPU):** x86_64 (AMD64) or ARM64 (Apple Silicon, Raspberry Pi 5/6) architecture. Minimum 4 cores. 8 cores are recommended for medium to large environments.
*   **Random Access Memory (RAM):**
    *   Minimum: 4 GB (small networks, test environments).
    *   Recommended: 8 GB or more (to support the analysis of large volumes of Nmap data and PostgreSQL in memory).
*   **Storage (Disk):**
    *   Minimum 50 GB of free space.
    *   **Important:** A Solid State Drive (SSD) or NVMe is **strictly recommended**. The system performs frequent writes related to CVE ingestion and network scan logs. Using standard SD cards (on microcomputers) or mechanical hard drives (HDD) will cause severe bottlenecks.
*   **Network:** Gigabit Ethernet (1 Gbps) network interface.

---

## 2. Software Deployment Options

### Option A: Containerized Deployment (Recommended)

This is the preferred method for rapid deployment, ensuring the isolation of dependencies (PostgreSQL, Dashboard, Scan Engine).

*   **Supported Operating Systems:**
    *   Linux (Ubuntu 22.04/24.04, Debian 12, RHEL 9).
    *   Windows 10/11 or Windows Server (via WSL2).
    *   macOS 12+ (Intel or Apple Silicon).
*   **Required Dependencies:**
    *   Docker Engine (version 24.0.0 or higher).
    *   Docker Compose (V2 version).

### Option B: Native Deployment (Bare-Metal / VM)

For environments where containerization is not possible or desired.

*   **Supported Operating Systems:** Windows, macOS, Linux (Debian/Ubuntu/RHEL).
*   **Required Dependencies:**
    *   **Python:** Version 3.13 or 3.14.
    *   **Nmap:** Version 7.90 or higher (required for network discovery and service identification).
    *   **PostgreSQL:** Version 15 or higher (for the central database).
    *   **Privileges:** Running the RTMS engine requires administrative rights (`root` on Linux/macOS, `Administrator` on Windows) to allow Nmap to forge raw packets (SYN scans, OS detection).

---

## 3. Network and Firewall Prerequisites

For RTMS to function and generate its NIS2 compliance reports, specific network flows must be allowed.

### Outbound Flows (Internet)
The server hosting RTMS must be able to reach the internet (directly or via a corporate proxy) for the following services:
*   `TCP/443` to `services.nvd.nist.gov`: Incremental synchronization of the vulnerability database.
*   `TCP/443` to the iTop server (if the CMDB module is enabled).
*   `TCP/587` (or 465) to the SMTP server defined by the client: Sending critical alerts and PDF audit reports.

### Internal Flows (Inbound/Outbound - LAN)
*   **Scan Scope:** The RTMS server must have active network routes to all subnets (VLANs) it is expected to audit.
*   **Internal Filtering:** It is recommended to create an exception in internal firewalls (IDS/IPS) for the RTMS scanner's IP address, to prevent its legitimate discovery requests from triggering false alerts within the local SOC.
*   **Dashboard Access:** Open port `TCP/8501` (or custom port via reverse proxy) to allow administrators to access the local web interface.

---

## 4. Notes on NIS2 Compliance

As part of a continuous compliance approach, it is highly recommended to dedicate a virtual machine (VM) or an exclusive hardware micro-server to RTMS. Co-hosting the tool with other business services on the same operating system is not recommended for reasons of security isolation and performance predictability.