# Guide de Déploiement & Orchestration Ansible

Ce guide documente le déploiement automatisé et idempotent de la suite **RTMS** à l'aide d'**Ansible**.  
Le moteur d'orchestration est intégré directement dans le dépôt [`rtms-installer`](https://github.com/tritschler/rtms-installer).

---

## 1. Prérequis & Installation : Mac vs VPS

Une des forces d'Ansible est son architecture **Agentless** (sans agent à installer sur les serveurs cibles).

### A. Sur votre Mac (Machine de contrôle)
Pour lancer des déploiements vers votre VPS ou vos environnements clients depuis votre Mac :

* **Option 1 (Recommandée & Sans pollution globale via `uv`) :**  
  Puisque vous utilisez déjà `uv` sur votre Mac, vous n'avez même pas besoin d'installer Ansible globalement :
  ```bash
  cd rtms-installer/ansible
  uv run --with ansible ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml
  ```
* **Option 2 (Installation standard macOS via Homebrew) :**
  ```bash
  brew install ansible
  ```
* **Option 3 (Via pipx) :**
  ```bash
  pipx install ansible
  ```

---

### B. Sur le VPS Ubuntu (Machine cible)
**Vous n'avez RIEN à installer au préalable sur votre VPS Ubuntu !**

Ansible fonctionne sans agent (*Agentless*) :
1. Il se connecte en **SSH** (`ssh ubuntu@vps`).
2. Il utilise l'interpréteur **Python 3** natif d'Ubuntu (`/usr/bin/python3`).
3. Il exécute les tâches et s'assure des permissions `sudo`.

> **Note :** Si vous préférez exécuter l'installation *directement depuis la console du VPS* (sans passer par votre Mac via SSH), lancez simplement le script wrapper :
> ```bash
> sudo ./install.sh
> ```
> Le script installera lui-même Ansible et les dépendances nécessaires (`apt-get install -y ansible`) de manière transparente.

---

## 2. Structure des Rôles & Composants

L'orchestration s'appuie sur 8 rôles modulaires situés dans `rtms-installer/ansible/roles/` :

| Rôle | Description | Composants gérés |
| :--- | :--- | :--- |
| `common` | Socle système et sécurité | Utilisateur système `rtms`, répertoires `/opt/rtms`, génération clé Ed25519 |
| `postgresql` | Base de données locale ou distante | Installation, création user/db, seeding initial et durcissement RBAC |
| `backend` | API FastAPI | Binaire `rtms-backend`, fichier `.env` (JWT), service systemd |
| `frontend` | Interface utilisateur | Compilation Vite/npm ou copie SPA `dist`, serveur NGINX (SSL optionnel) |
| `scanner` | Moteur de scan réseau | Binaire `rtms-scanner`, fichier `scanner.properties`, service systemd |
| `nvd` | Ingestion CVE NIST | Binaire `rtms-nvd`, service d'arrière-plan systemd |
| `local_agent` | Agent endpoint distribué | Binaire `rtms-local-agent`, jeton d'enrôlement, service systemd |
| `admin_hub` | Console centrale & Support Hub | FastAPI, venv Python, NGINX, initialisation tables Postgres OVH |

---

## 3. Scénarios de Déploiement

### Scénario 1 : Appliance On-Premise Standalone (1 seule machine)

Idéal pour une VM ou un serveur physique client hébergeant l'ensemble de la suite.

#### Méthode 1 : Via le script wrapper (recommandé pour le client)
```bash
sudo ./install.sh
```
* Options de compilation et binaires :
  * `--build-from-source` : Force la compilation locale avec `uv`/`build.sh`/`npm`.
  * `--use-precompiled` : Utilise strictement les binaires précompilés du dossier `bin/`.
  * `--non-interactive` : Automatisation batch (idéal pour scripts CI/CD).
  * `--legacy` : Exécute l'ancien script pure-bash en cas de besoin.

#### Méthode 2 : Directement via Ansible
```bash
cd ansible
ansible-playbook -i inventories/standalone/hosts.yml playbooks/site_standalone.yml
```

---

### Scénario 2 : Architecture Distribuée & Flotte d'Agents

Pour les environnements d'entreprise avec un serveur central, des scanners déportés (DMZ) et des dizaines de postes équipés de l'agent local.

1. Définir les adresses IP dans `inventories/distributed/hosts.yml` :
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

2. Déployer le Core et les Scanners :
   ```bash
   ansible-playbook -i inventories/distributed/hosts.yml playbooks/deploy_distributed.yml
   ```

3. Déployer la flotte de **Local Agents** en rolling update :
   ```bash
   ansible-playbook -i inventories/distributed/hosts.yml playbooks/deploy_agents.yml
   ```
   > **Déploiement par vagues :** Les agents sont déployés par vagues successives de 25% des machines (`serial: "25%"`), avec interruption automatique si plus de 10% des postes rencontrent une erreur.

---

### Scénario 3 : Déploiement VPS Central OVH (RTMS Admin)

Pour administrer et mettre à jour votre serveur central de télé-assistance et de licences :

1. Configurer `inventories/vps_ovh/hosts.yml` avec l'IP publique et l'utilisateur SSH (`ubuntu`).
2. Lancer le déploiement depuis votre Mac :
   ```bash
   cd ansible
   uv run --with ansible ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml
   ```

---

## 4. Mode Simulation (Dry-Run) & Validation

Avant d'appliquer des changements en production, vous pouvez tester l'exécution sans rien modifier sur les machines distantes :

```bash
ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml --check --diff
```
