# CMDB Integration & Reconciliation (iTop)

RTMS integrates with your Configuration Management Database (**CMDB**, specifically **Combodo iTop**) to reconcile active wire reality against declared IT assets.

---

## 1. Reconciliation Principles

Real-time inventory discovered across monitored subnets is automatically reconciled against your CMDB catalog:

```mermaid
flowchart LR
    A[RTMS Probes - Wire Reality] --> C{Reconciliation Engine}
    B[iTop CMDB - Declared Assets] --> C
    C --> D[Matched & Up-to-Date Assets]
    C --> E[Stale CMDB Records (Unreachable)]
    C --> F[Shadow IT: Unregistered Wire Devices]
```

* **Shadow IT Identification**: Highlights connected network hardware that does not exist in the official enterprise CMDB.
* **Ghost Assets**: Detects declared CMDB records that have stopped transmitting network frames for extended periods.

---

## 2. iTop Connector Configuration

In RTMS Administration:
* **iTop REST Web Service Endpoint**: `https://cmdb.company.local/webservices/rest.php`
* **Service Credentials & API Keys**: Dedicated service account with read access to classes `Server`, `PC`, `NetworkDevice`, and `VirtualMachine`.
* **Sync Schedule**: Automated periodic background synchronization (default: hourly) with manual on-demand triggers.
