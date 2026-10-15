# Cahier de Recette : Passerelle VPS OVH (Tickets, Updates, Licences)

Ce document détaille le plan de test exhaustif pour valider le fonctionnement, la sécurité et le cloisonnement réseau des **trois endpoints centraux** exposés sur le VPS OVH (`https://updates.3ts.ai`).

---

## 1. Contexte d'Architecture & Sécurité

```mermaid
sequenceDiagram
    autonumber
    participant Client as RTMS Web (Appliance Cliente)
    participant Nginx as NGINX VPS OVH (443 SSL)
    participant Hub as Backend FastAPI (127.0.0.1:8090)
    participant DB as PostgreSQL (customers)

    Note over Client,Nginx: Zone Publique Sécurisée (TLS 1.3 / updates.3ts.ai)
    Client->>Nginx: Requête HTTPS avec Authorization: Bearer <JWT_Ed25519 / Token>
    Nginx->>Hub: Reverse Proxy vers FastAPI
    Hub->>Hub: verify_client_token() : Signature Ed25519 ou SHA-256
    Hub->>DB: Écriture / Lecture (support_tickets, software_releases, license_requests)
    Hub-->>Client: Réponse JSON chiffrée
```

* **Nom de domaine public** : `https://updates.3ts.ai`
* **Adresse IP publique VPS** : `135.125.102.194`
* **Port d'écoute public** : `443` (HTTPS - Chiffrement fort TLS 1.3)
* **Authentification unifiée** : Dépendance FastAPI `verify_client_token` acceptant soit un jeton éphémère (15 min) signé via la clé privée d'instance **Ed25519**, soit un **Bearer Token client** SHA-256.

---

## 2. Matrice des Cas de Test

| ID Test | Composant Cible | Méthode & Endpoint | Objectif Validé |
| :--- | :--- | :--- | :--- |
| **`TC-VPS-TICKETS-01`** | Support & Incidents | `POST /api/v1/tickets` | Soumission de ticket avec diagnostic depuis l'UI RTMS Web |
| **`TC-VPS-TICKETS-02`** | Support & Incidents | `POST /api/v1/tickets` | Appel curl direct avec Bearer Token |
| **`TC-VPS-TICKETS-03`** | Support & Incidents | `POST /api/v1/tickets` | Rejets de sécurité (HTTP 401 sans token / HTTP 403 avec faux token) |
| **`TC-VPS-TICKETS-04`** | Support & Incidents | Base `customers` & SMTP | Persistance SQL et notification email via `ssl0.ovh.net` |
| **`TC-VPS-UPDATES-01`** | Software Releases | `/opt/rtms-admin/packages` | Dépôt d'archive `.tar.gz` et publication en base sur le VPS |
| **`TC-VPS-UPDATES-02`** | Software Releases | `GET /api/v1/version` | Détection de nouvelle version depuis l'UI `/security/software` |
| **`TC-VPS-UPDATES-03`** | Software Releases | `POST /api/system/updates/apply` | Téléchargement du paquet et contrôle d'intégrité SHA-256 |
| **`TC-VPS-UPDATES-04`** | Software Releases | `GET /api/v1/updates/packages/...` | Téléchargement binaire direct par curl authentifié |
| **`TC-VPS-LICENSES-01`** | Licences & Quotas | `POST /api/license/generate-renewal-request` | Demande de renouvellement via l'UI `/license` |
| **`TC-VPS-LICENSES-02`** | Licences & Quotas | `POST /api/v1/license-requests` | Soumission directe curl avec payload matériel complet |
| **`TC-VPS-LICENSES-03`** | Licences & Quotas | Base `customers` | Vérification de la création de la demande au statut `pending` |
| **`TC-VPS-LICENSES-04`** | Licences & Quotas | RTMS Admin | Approbation en 1 clic et émission de la licence `.key` |
| **`TC-VPS-NET-01`** | Réseau & Crypto | TLS 1.3 / Port 443 | Chiffrement SSL, certificat Let's Encrypt et HSTS |
| **`TC-VPS-NET-02`** | Réseau & Routage | Routage WAN vs VPN | Preuve d'IP publique dans `/var/log/nginx/access.log` (pas 10.0.0.1) |
| **`TC-VPS-NET-03`** | Réseau & Cloisonnement | NGINX Zone Publique | Blocage strict (404) de la console web d'administration sur le port public |

---

## 3. Procédures Détaillées par Cas de Test

### Suite 1 : Ingestion des Tickets de Support

#### Cas `TC-VPS-TICKETS-01` : Soumission via l'Interface Web Client
1. **Accès** : Connectez-vous à RTMS Web avec un compte Administrateur et accédez à `/help/support`.
2. **Action** :
   * Objet : `Test de qualification plateforme VPS`
   * Catégorie : `incident` | Priorité : `high`
   * Description : `Vérification de la passerelle de support via l'IP publique VPS.`
   * Cochez l'option *« Inclure les données de diagnostic »*.
   * Cliquez sur **« Envoyer le ticket de support »**.
3. **Résultat attendu** :
   * Notification verte affichant la référence générée (ex. `RTMS-2026-XXXX`).
   * Le ticket s'affiche dans l'historique en dessous avec le statut `open` ou `submitted`.

#### Cas `TC-VPS-TICKETS-02` : Soumission directe par API (cURL)
Exécutez depuis un terminal :
```bash
curl -X POST https://updates.3ts.ai/api/v1/tickets \
  -H "Authorization: Bearer 2c47b3eaad6f415c565556ba5146701195d5bd27320c21781e29ad2614e01242" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "Marc Tritschler",
    "user_email": "support@3tsconsulting.be",
    "company_name": "3TS Client Qualification",
    "instance_id": "INSTANCE-TEST-01",
    "subject": "Ticket direct curl",
    "category": "incident",
    "priority": "normal",
    "description": "Validation du payload de ticket direct",
    "diagnostic_data": {"rtms_version": "0.1.0", "assets_count": 42}
  }'
```
* **Résultat attendu** : Réponse `HTTP 201 Created` avec JSON : `{"success": true, "ticket_id": "RTMS-2026-XXXX", "status": "open"}`.

#### Cas `TC-VPS-TICKETS-03` : Rejet des accès non autorisés
```bash
# Test sans token -> doit renvoyer 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://updates.3ts.ai/api/v1/tickets -d '{}'

# Test avec token invalide -> doit renvoyer 403
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer faux_token" -X POST https://updates.3ts.ai/api/v1/tickets -d '{}'
```
* **Critère de succès** : HTTP 401 pour le premier, HTTP 403 pour le second.

#### Cas `TC-VPS-TICKETS-04` : Contrôle en Base de Données sur le VPS
Depuis votre Mac (via Ansible) :
```bash
cd rtms-installer/ansible
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command \
  -a "su - postgres -c \"psql -d customers -c 'SELECT ticket_id, company_name, subject, priority, status, created_at FROM support_tickets ORDER BY created_at DESC LIMIT 3;'\"" --become
```
* **Critère de succès** : Présence de la ligne insérée avec son `ticket_id` et son statut.

---

### Suite 2 : Distribution des Mises à Jour Logicielles

#### Cas `TC-VPS-UPDATES-01` : Préparation de Release sur le VPS
1. **Création du paquet binaire sur le VPS** :
   ```bash
   ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "bash -c '
     mkdir -p /opt/rtms-admin/packages /tmp/pkg-tmp
     echo \"RTMS Scanner Binary Release v0.2.0\" > /tmp/pkg-tmp/scanner
     tar -czf /opt/rtms-admin/packages/rtms-scanner-release.tar.gz -C /tmp/pkg-tmp scanner
     rm -rf /tmp/pkg-tmp
     chmod 644 /opt/rtms-admin/packages/rtms-scanner-release.tar.gz
   '" --become
   ```
2. **Publication de la version en base de données** :
   ```bash
   ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "su - postgres -c \"psql -d customers -c \\\"
     INSERT INTO software_releases (version, release_notes, manifest, is_active)
     VALUES ('0.2.0', 'Release 0.2.0 : Optimisations du scan réseau et conformité NIS 2', '{\\\\\\\"version\\\\\\\": \\\\\\\"0.2.0\\\\\\\", \\\\\\\"components\\\\\\\": [{\\\\\\\"name\\\\\\\": \\\\\\\"rtms-scanner\\\\\\\", \\\\\\\"version\\\\\\\": \\\\\\\"0.2.0\\\\\\\"}], \\\\\\\"packages\\\\\\\": {\\\\\\\"rtms-scanner\\\\\\\": {\\\\\\\"filename\\\\\\\": \\\\\\\"rtms-scanner-release.tar.gz\\\\\\\", \\\\\\\"url\\\\\\\": \\\\\\\"/api/v1/updates/packages/rtms-scanner-release.tar.gz\\\\\\\"}}}', true)
     ON CONFLICT (version) DO UPDATE SET is_active = true, updated_at = NOW();
   \\\"\"" --become
   ```

#### Cas `TC-VPS-UPDATES-02` : Détection depuis l'UI RTMS Web
1. Ouvrez la page **Administration > Mises à jour logicielles** (`/security/software`).
2. **Critère de succès** :
   * L'encart passe en alerte bleue : **« Mise à jour disponible : v0.2.0 »**.
   * Les notes de version *« Release 0.2.0 : Optimisations du scan réseau et conformité NIS 2 »* sont affichées.
   * Le composant `rtms-scanner` apparaît dans la liste des composants à mettre à jour.

#### Cas `TC-VPS-UPDATES-03` : Téléchargement et Contrôle d'Intégrité SHA-256
1. Cliquez sur le bouton **« Télécharger et Préparer la Mise à Jour »**.
2. **Critère de succès** :
   * Le backend télécharge l'archive depuis le VPS via HTTPS.
   * L'archive est stockée localement dans `rtms-web/backend/updates/downloads/rtms-scanner-release.tar.gz`.
   * L'empreinte SHA-256 est calculée et validée.
   * Le statut de mise en attente (*Staged*) s'affiche en vert dans l'interface.

#### Cas `TC-VPS-UPDATES-04` : Téléchargement Direct en Streaming (cURL)
```bash
curl -s -H "Authorization: Bearer 2c47b3eaad6f415c565556ba5146701195d5bd27320c21781e29ad2614e01242" \
  https://updates.3ts.ai/api/v1/updates/packages/rtms-scanner-release.tar.gz | tar -tzv
```
* **Critère de succès** : Liste les fichiers de l'archive tar sans erreur (`-rw-r--r-- scanner`).

---

### Suite 3 : Renouvellement & Extension de Licences

#### Cas `TC-VPS-LICENSES-01` : Demande depuis l'UI RTMS Web
1. Accédez à la page **Abonnements & Licences** (`/license`).
2. Faites défiler jusqu'au bloc **« Demande de Renouvellement & Upgrade »** (icône ⚡).
3. Cliquez sur **« Demander un renouvellement »**.
4. Sélectionnez le plan cible (ex. `SECURE`) et la jauge d'actifs (ex. `250 actifs`), puis validez.
5. **Critère de succès** :
   * Bandeau vert : `Renewal request (RTMS-LIC-2026-XXXX) successfully sent to 3TS Central Support Hub !`.
   * Un fichier de secours `rtms_renewal_request_<tenant>.json` est automatiquement téléchargé dans votre dossier Téléchargements.

#### Cas `TC-VPS-LICENSES-02` : Soumission directe par API (cURL)
```bash
curl -X POST https://updates.3ts.ai/api/v1/license-requests \
  -H "Authorization: Bearer 2c47b3eaad6f415c565556ba5146701195d5bd27320c21781e29ad2614e01242" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "CLIENT-QUALIF-2026",
    "company_name": "Entreprise de Qualification",
    "contact_name": "Marc Tritschler",
    "contact_email": "admin@qualif.be",
    "requested_plan": "COMPLIANCE",
    "requested_assets": 500,
    "notes": "Test de renouvellement automatisé",
    "request_payload": {
      "scanners": [{"name": "probe-principal", "hardware_id": "hw-qualif-8888"}],
      "components": {"core": "0.1.0"},
      "format_version": "1.0"
    }
  }'
```
* **Critère de succès** : Réponse `HTTP 201 Created` avec un numéro d'enregistrement unique :  
  `{"success": true, "request_id": "RTMS-LIC-2026-XXXX", "status": "pending"}`.

#### Cas `TC-VPS-LICENSES-03` : Contrôle en Base de Données sur le VPS
```bash
ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command \
  -a "su - postgres -c \"psql -d customers -c 'SELECT id, request_id, tenant_id, requested_plan, requested_assets, status, created_at FROM license_requests ORDER BY created_at DESC LIMIT 2;'\"" --become
```
* **Critère de succès** : La demande apparaît avec le statut `pending` et les quotas demandés.

#### Cas `TC-VPS-LICENSES-04` : Approbation & Émission dans RTMS Admin
1. Ouvrez la console d'administration 3TS via WireGuard sur `http://10.0.0.1/`.
2. Accédez à la rubrique des demandes de licence (*License Requests*).
3. Cliquez sur **« Approuver »** : le générateur signe le certificat RSA et génère le fichier de licence `.key` prêt à être transmis au client.

---

### Suite 4 : Sécurité Réseau, SSL & Cloisonnement

#### Cas `TC-VPS-NET-01` : Validation du Chiffrement SSL & HSTS
```bash
echo | openssl s_client -connect updates.3ts.ai:443 -servername updates.3ts.ai 2>&1 | grep -E "Protocol|Cipher|Verify return code"
```
* **Critère de succès** :
  * `Protocol: TLSv1.3`
  * `Cipher: TLS_AES_256_GCM_SHA384`
  * `Verify return code: 0 (ok)` (Certificat officiel Let's Encrypt valide).

#### Cas `TC-VPS-NET-02` : Vérification du Routage Public (Hors VPN)
1. Exécutez une requête curl vers `https://updates.3ts.ai/api/v1/version`.
2. Inspectez les journaux NGINX du VPS :
   ```bash
   ansible -i inventories/vps_ovh/hosts.yml vps_ovh -m command -a "tail -n 2 /var/log/nginx/access.log" --become
   ```
* **Critère de succès** : L'adresse IP source enregistrée est l'IP publique WAN de votre box/connexion (ex. `178.51.x.x`), et **non l'IP 10.0.0.2** du tunnel VPN.

#### Cas `TC-VPS-NET-03` : Cloisonnement de l'Interface Administrative
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://updates.3ts.ai/
curl -s -o /dev/null -w "%{http_code}\n" https://updates.3ts.ai/docs/
```
* **Critère de succès** : Renvoie strictement **HTTP 404** `{"detail": "Not Found"}`.  
  La console Web React et la documentation interne ne sont accessibles **que** via le tunnel privé WireGuard (`http://10.0.0.1/`).

---

## 4. Grille d'Émargement Finale (Rapport d'Exécution)

| Cas de Test | Résultat Obtenu | Conformité | Date & Testeur |
| :--- | :--- | :--- | :--- |
| `TC-VPS-TICKETS-01` | Ticket créé, référence affichée | ✅ Conforme | 15/10/2026 - Marc Tritschler |
| `TC-VPS-TICKETS-02` | HTTP 201, `ticket_id` généré | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-TICKETS-03` | Rejet HTTP 401 & 403 strict | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-TICKETS-04` | Enregistrement table `support_tickets` | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-01` | Paquet tar.gz & SQL version 0.2.0 | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-02` | Détection v0.2.0 dans l'UI Web | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-03` | Téléchargement local & contrôle SHA-256 | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-UPDATES-04` | Flux binaire décompressé avec succès | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-01` | Soumission UI & JSON téléchargé | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-02` | HTTP 201 `RTMS-LIC-2026-9189` | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-03` | Enregistrement table `license_requests` | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-LICENSES-04` | Validation workflow approbation admin | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-NET-01` | TLS 1.3 / AES-256-GCM / Let's Encrypt | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-NET-02` | IP WAN publique dans Nginx access.log | ✅ Conforme | 15/10/2026 - 3TS Automation |
| `TC-VPS-NET-03` | HTTP 404 sur les routes Web/Docs externes | ✅ Conforme | 15/10/2026 - 3TS Automation |
