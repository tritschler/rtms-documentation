# Ansible Deployment & Orchestration Guide

This guide documents the automated, idempotent deployment of the **RTMS** suite using **Ansible**.  
The orchestration engine is housed directly within the [`rtms-installer`](https://github.com/tritschler/rtms-installer) repository.

---

## 1. Prerequisites & Installation: Mac vs VPS

One of Ansible's key strengths is its **Agentless** architecture (no background daemon required on managed nodes).

### A. On your Mac (Control Machine)
To run deployments toward your VPS or client appliances from macOS:

* **Option 1 (Recommended & Isolated via `uv`):**  
  Since you already use `uv`, you do not need a global Ansible installation:
  ```bash
  cd rtms-installer/ansible
  uv run --with ansible ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml
  ```
* **Option 2 (Homebrew):**
  ```bash
  brew install ansible
  ```
* **Option 3 (Via pipx):**
  ```bash
  pipx install ansible
  ```

---

### B. On the Ubuntu VPS (Target Machine)
**You do NOT need to pre-install anything on your target Ubuntu VPS!**

Ansible operates agentlessly:
1. Connects via **SSH** (`ssh ubuntu@vps`).
2. Leverages the native Ubuntu **Python 3** interpreter (`/usr/bin/python3`).
3. Executes modular tasks with elevated `sudo` privileges.

> **Note:** If you choose to execute installation *locally on the VPS console* (without SSH from your workstation), simply execute the wrapper script:
> ```bash
> sudo ./install.sh
> ```
> The script installs Ansible and necessary packages (`apt-get install -y ansible`) transparently.

---

## 2. Roles & Component Structure

Orchestration is organized across 8 modular roles located in `rtms-installer/ansible/roles/`:

| Role | Description | Managed Components |
| :--- | :--- | :--- |
| `common` | System base & security | `rtms` system user, `/opt/rtms` paths, Ed25519 asymmetric keypair |
| `postgresql` | Local or remote database | Installation, user/db creation, schema migration, and RBAC hardening |
| `backend` | FastAPI backend | `rtms-backend` binary, `.env` file (JWT), systemd service |
| `frontend` | User interface | Vite/npm compilation or SPA `dist` deployment, NGINX configuration (optional TLS) |
| `scanner` | Network scanning probe | `rtms-scanner` binary, `scanner.properties`, systemd service |
| `nvd` | NIST CVE ingestion | `rtms-nvd` binary, background ingestion systemd service |
| `local_agent` | Distributed endpoint agent | `rtms-local-agent` binary, enrollment token, systemd service |
| `admin_hub` | Central hub & Support console | FastAPI, Python virtualenv, NGINX, OVH Postgres table seeding |

---

## 3. Deployment Scenarios

### Scenario 1: Standalone On-Premise Appliance (Single Server)

Ideal for client virtual machines or bare-metal servers hosting all RTMS services.

#### Method 1: Via the installation wrapper (Recommended for clients)
```bash
sudo ./install.sh
```
* Compilation & binary options:
  * `--build-from-source`: Force local compilation with `uv`/`build.sh`/`npm`.
  * `--use-precompiled`: Enforce using precompiled binaries in `bin/`.
  * `--non-interactive`: Unattended automated provisioning (ideal for CI/CD).
  * `--legacy`: Fall back to legacy bash installer if necessary.

#### Method 2: Directly via Ansible
```bash
cd ansible
ansible-playbook -i inventories/standalone/hosts.yml playbooks/site_standalone.yml
```

---

### Scenario 2: Distributed Architecture & Fleet Deployment

For enterprise environments featuring a central cluster, remote DMZ network probes, and fleets of endpoints running the local agent.

1. Define target hosts in `inventories/distributed/hosts.yml`:
   ```yaml
   all:
     children:
       rtms_core:
         hosts:
           rtms-core.client.corp:
             ansible_host: 192.168.1.50
       rtms_scanners:
         hosts:
           scanner-dmz.client.corp:
             ansible_host: 192.168.10.5
       rtms_agents:
         hosts:
           srv-prod-01: { ansible_host: 192.168.1.101 }
           srv-db-01:   { ansible_host: 192.168.1.102 }
           ws-user-01:  { ansible_host: 192.168.5.21 }
   ```

2. Deploy Core Services and Remote Probes:
   ```bash
   ansible-playbook -i inventories/distributed/hosts.yml playbooks/deploy_distributed.yml
   ```

3. Deploy **Local Agent** fleet via rolling updates:
   ```bash
   ansible-playbook -i inventories/distributed/hosts.yml playbooks/deploy_agents.yml
   ```
   > **Rolling Deployments:** Agents are updated in batches of 25% of hosts (`serial: "25%"`), with automated failure cutoffs if more than 10% fail.

---

### Scenario 3: Central OVH VPS Deployment (RTMS Admin & Support Hub)

The central OVH VPS hosts the 3TS administrative gateway and telemetry hub for on-premises client RTMS instances (bug reporting, software release distribution, and license renewals).

#### 1. Architecture & Network Security
* **Encrypted WireGuard Access**: Management and Ansible deployments run exclusively over the WireGuard VPN mesh (`10.0.0.1`). Public SSH (port 22) is not exposed to the internet.
* **Isolated `customers` Database**: In contrast to on-premise appliances which run `rtms_db`, the central hub uses a dedicated PostgreSQL database named **`customers`** (holding schema `3TS` for client accounts, licenses, and tokens, and schema `public` for support tickets, renewal requests, and software releases).
* **API-Only Backend Mode**: No frontend React SPA or Node build is deployed (`deploy_admin_frontend: false`). NGINX reverse-proxies directly to the FastAPI backend (Uvicorn on port 8090) with `client_max_body_size 500M`.

#### 2. Inventory & Secret Configuration
Local credentials are kept off Git via `.gitignore`:
1. Host inventory [`ansible/inventories/vps_ovh/hosts.yml`](file:///Users/marctritschler/git_projects/rtms-installer/ansible/inventories/vps_ovh/hosts.yml):
   ```yaml
   all:
     hosts:
       vps_ovh:
         ansible_host: 10.0.0.1
         ansible_user: ubuntu
         ansible_ssh_private_key_file: ~/.ssh/id_ed25519
   ```
2. Variable overrides [`ansible/inventories/vps_ovh/group_vars/all.yml`](file:///Users/marctritschler/git_projects/rtms-installer/ansible/inventories/vps_ovh/group_vars/all.yml) (untracked in Git):
   ```yaml
   rtms_admin_db_user: "rtms_admin"
   rtms_admin_db_password: "<SECURE_PASSWORD>"
   rtms_admin_db_name: "customers"
   rtms_admin_db_host: "localhost"
   rtms_admin_db_port: 5432
   rtms_admin_api_token: "<YOUR_API_TOKEN>"
   rtms_admin_jwt_secret: "<JWT_SECRET_KEY>"
   deploy_admin_frontend: false
   ```

#### 3. Running the Deployment
```bash
cd rtms-installer/ansible
ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml
```

#### 4. The 3 Production Endpoints
Once deployed, the following endpoints are operational:
* **Bug Submission (`POST /api/v1/tickets`)**: Ingestion of crash logs and tickets (up to 50 MB), authorized via client bearer token or Ed25519 asymmetric JWT.
* **Software Updates (`GET /api/v1/version` & `GET /api/v1/updates/packages/{name}`)**: Checking releases and streaming 1 MB chunked package downloads from `/opt/rtms-admin/packages`.
* **License Renewals (`POST /api/v1/license-requests`)**: Automated ingestion of renewal and tier upgrade requests.

---

## 4. Simulation Mode (Dry-Run) & Validation

Before applying modifications to production systems, simulate the execution without altering target hosts:

```bash
ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml --check --diff
```

