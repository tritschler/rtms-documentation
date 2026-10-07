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

### Scénario 3 : Déploiement VPS Central OVH (RTMS Admin & Support Hub)

Le VPS central OVH héberge la passerelle technique 3TS pour les instances RTMS déployées chez les clients (remontée de bugs, mises à jour logicielles et demandes de licences).

#### 1. Architecture & Sécurité Réseau
* **Accès chiffré WireGuard** : Le déploiement et l'administration s'effectuent via le tunnel VPN WireGuard mesh (`10.0.0.1`). L'IP publique OVH et le port SSH 22 ne sont pas exposés sur Internet pour l'administration.
* **Base de données isolée `customers`** : Contrairement aux appliances clientes qui exécutent `rtms_db`, le VPS central héberge une base PostgreSQL dédiée nommée **`customers`** (schéma `3TS` pour les comptes, licences et tokens, et schéma `public` pour les tickets de bugs, demandes de renouvellement et versions logicielles).
* **Mode Backend pur (API Only)** : Aucun frontend React ou build Node.js n'est déployé (`deploy_admin_frontend: false`). NGINX reverse-proxy route directement toutes les requêtes (`/` et `/api/`) vers l'API FastAPI (Uvicorn port 8090) avec `client_max_body_size 500M`.

#### 2. Configuration de l'inventaire & Secrets
Les secrets et mots de passe locaux sont exclus du dépôt Git via `.gitignore` :
1. Fichier d'inventaire [`ansible/inventories/vps_ovh/hosts.yml`](file:///Users/marctritschler/git_projects/rtms-installer/ansible/inventories/vps_ovh/hosts.yml) :
   ```yaml
   all:
     hosts:
       vps_ovh:
         ansible_host: 10.0.0.1
         ansible_user: ubuntu
         ansible_ssh_private_key_file: ~/.ssh/id_ed25519
   ```
2. Fichier de variables [`ansible/inventories/vps_ovh/group_vars/all.yml`](file:///Users/marctritschler/git_projects/rtms-installer/ansible/inventories/vps_ovh/group_vars/all.yml) (non suivi par Git) :
   ```yaml
   rtms_admin_db_user: "rtms_admin"
   rtms_admin_db_password: "<MOT_DE_PASSE_SECURISE>"
   rtms_admin_db_name: "customers"
   rtms_admin_db_host: "localhost"
   rtms_admin_db_port: 5432
   rtms_admin_api_token: "<VOTRE_API_TOKEN>"
   rtms_admin_jwt_secret: "<CLE_SECRETE_JWT>"
   deploy_admin_frontend: false
   ```

#### 3. Exécution du déploiement
```bash
cd rtms-installer/ansible
ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml
```

#### 4. Les 3 Endpoints Centraux Opérationnels
Une fois déployé, le serveur expose immédiatement :
* **Remontée de bugs (`POST /api/v1/tickets`)** : Réception des rapports de tickets et logs chiffrés (jusqu'à 50 Mo), authentifiés par token client Bearer ou signature asymétrique Ed25519 JWT.
* **Mises à jour logicielles (`GET /api/v1/version` & `GET /api/v1/updates/packages/{name}`)** : Détection et téléchargement par chunk de 1 Mo des paquets déposés dans `/opt/rtms-admin/packages`.
* **Renouvellement de licences (`POST /api/v1/license-requests`)** : Soumission automatisée des demandes de licences et renouvellements depuis les appliances clientes.

---

## 4. Mode Simulation (Dry-Run) & Validation

Avant d'appliquer des changements en production, vous pouvez tester l'exécution sans rien modifier sur les machines distantes :

```bash
ansible-playbook -i inventories/vps_ovh/hosts.yml playbooks/deploy_vps_admin.yml --check --diff
```

---

## 5. Aide-Mémoire d'Exploitation & Diagnostic Rapide (VPS OVH)

Ces commandes s'exécutent **directement depuis votre Mac** sans avoir à ouvrir une session interactive manuelle sur le serveur.

### A. Commandes Ansible Ad-Hoc (Depuis `rtms-installer/ansible`)

```bash
cd rtms-installer/ansible

# 1. Tester la connectivité WireGuard vers le VPS
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m ping

# 2. Vérifier l'état de PostgreSQL (pg_isready)
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "pg_isready"

# 3. Vérifier le statut des services systemd
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "systemctl status nginx --no-pager" --become
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "systemctl status rtms-admin --no-pager" --become
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "systemctl status postgresql --no-pager" --become

# 4. Redémarrer ou recharger un service
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m systemd -a "name=rtms-admin state=restarted" --become
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m systemd -a "name=nginx state=reloaded" --become

# 5. Consulter les logs en temps réel (30 dernières lignes)
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "journalctl -u rtms-admin -n 30 --no-pager" --become
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "tail -n 30 /var/log/nginx/error.log" --become
```

### B. Commandes SSH One-Liners Rapides (Depuis n'importe où sur votre Mac)

```bash
# 1. Vérification express NGINX (statut + syntaxe configuration)
ssh ubuntu@10.0.0.1 "sudo systemctl status nginx --no-pager && sudo nginx -t"

# 2. Vérification express PostgreSQL (connexion + liste des tables customers)
ssh ubuntu@10.0.0.1 "pg_isready && sudo -u postgres psql -d customers -c \"SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('3TS', 'public') ORDER BY table_schema, table_name;\""

# 3. Vérification express RTMS Admin Backend (service + ports en écoute 80, 443, 8090, 5432)
ssh ubuntu@10.0.0.1 "sudo systemctl status rtms-admin --no-pager && sudo ss -tulpn | grep -E '(80|443|8090|5432)'"

# 4. Test rapide de l'endpoint Healthcheck
ssh ubuntu@10.0.0.1 "curl -s http://127.0.0.1:8090/api/health"

# 5. Consulter les derniers tickets reçus dans la base
ssh ubuntu@10.0.0.1 "sudo -u postgres psql -d customers -c \"SELECT ticket_id, subject, user_name, status, created_at FROM public.support_tickets ORDER BY created_at DESC LIMIT 5;\""
```


