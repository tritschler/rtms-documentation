# Modèle de Contrôle d'Accès Basé sur les Rôles (RBAC)

La plateforme RTMS implémente un modèle **RBAC (Role-Based Access Control)** granulaire à 4 rôles opérationnels, conçu pour refléter l'organisation réelle des centres des opérations de sécurité (SOC), des équipes réseau/système et des auditeurs de conformité réglementaire (**NIS 2 / ISO 27001**).

---

## 1. Principes Fondamentaux

Le modèle repose sur trois piliers de sécurité :
1. **Principe du Moindre Privilège (*Least Privilege*)** : chaque utilisateur dispose uniquement des habilitations strictement requises pour sa mission.
2. **Ségrégation des Tâches (*Segregation of Duties*)** : les tâches de gestion réseau (opérateur) sont séparées du triage des risques et de l'acceptation des vulnérabilités (analyste SOC).
3. **Piste d'Audit Immuable et Isolée** : l'accès aux journaux d'audit de sécurité et de conformité (`/api/audit/*`) est strictement protégé. Les opérateurs réseau n'ont pas accès aux logs d'audit pour éviter tout risque de dissimulation, tandis que les auditeurs (`viewer`) y ont accès sans posséder aucun droit d'écriture.

---

## 2. Définition des 4 Rôles

| Rôle | Désignation | Missions & Responsabilités |
| :--- | :--- | :--- |
| **`admin`** | Administrateur Système | Contrôle total de la plateforme. Gestion des utilisateurs, licences, paramètres système, démarrage/arrêt des services, et purge des données orphelines. |
| **`security_analyst`** | Analyste SOC / Sécurité | Triage des vulnérabilités CVE, acceptation formelle des risques avec justification, création et assignation des *findings*, gestion des alertes d'intrusion et déclenchement de scans de vérification. |
| **`operator`** | Opérateur Réseau / Scanners | Gestion opérationnelle du parc d'actifs (édition, exclusion IP, renommage de sous-réseaux, suppression), configuration des scanners, redémarrage direct des scanners (`RESTART`), gestion des tokens d'agents locaux (révocation/réactivation) et lancement de scans de découverte. |
| **`viewer`** | Auditeur / Conformité | Consultation en lecture seule complète de la cartographie, de l'inventaire, des vulnérabilités et **des journaux d'audit de conformité** (`/api/audit/*`) à des fins de preuve réglementaire (NIS 2 / ISO 27001). **Zéro droit de mutation ou d'action.** |

---

## 3. Matrice Complète des Permissions

| Domaine Fonctionnel / Endpoint | `admin` | `security_analyst` | `operator` | `viewer` (Auditeur) |
| :--- | :---: | :---: | :---: | :---: |
| **Gestion Utilisateurs & Rôles** (`/api/users*`) | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 |
| **Configuration Système & Licences** (`/api/license*`, `/api/system/*`) | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 |
| **Journaux d'Audit Système & Connexions** (`/api/audit/*`) | ✅ Oui | ✅ Oui | ❌ 403 | ✅ **Oui (Preuves NIS 2)** |
| **Démarrer / Arrêter / Mettre en pause les Services** | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 |
| **Redémarrage Scanner Réseau (`RESTART`)** | ✅ Oui | ❌ 403 | ✅ Oui | ❌ 403 |
| **Gestion Tokens Agents Locaux** (Révocation / Réactivation) | ✅ Oui | ❌ 403 | ✅ Oui | ❌ 403 |
| **Déclenchement Scans Réseau** (`/api/services/scanner/trigger`) | ✅ Oui | ✅ Oui | ✅ Oui | ❌ 403 |
| **Gestion des Actifs** (Édition Hostname, Exclusion IP, Ports) | ✅ Oui | ✅ Oui | ✅ Oui | ❌ Lecture Seule |
| **Suppression d'Actifs & Renommage Sous-réseaux** | ✅ Oui | ❌ 403 | ✅ Oui | ❌ 403 |
| **Purge des Actifs Orphelins** (`/api/assets/purge-orphans`) | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 |
| **Inventaire Logiciel** (Ajout, Édition Version, Suppression) | ✅ Oui | ✅ Oui | ✅ Oui | ❌ Lecture Seule |
| **Acceptation des Risques CVE** (`/api/vulnerabilities/accept_risk`) | ✅ Oui | ✅ **Oui (SOC)** | ❌ 403 | ❌ 403 |
| **Création & Gestion des Security Findings** (`/api/findings*`) | ✅ Oui | ✅ **Oui (SOC)** | ❌ 403 | ❌ 403 |
| **Mise à Jour Statut Finding** (Remédiation en cours, Résolu) | ✅ Oui | ✅ Oui | ✅ Oui (Opérations) | ❌ Lecture Seule |
| **Gestion Alertes Sécurité** (Clôture globale, Résolution, Whitelist MAC) | ✅ Oui | ✅ **Oui (SOC)** | ❌ 403 | ❌ 403 |

---

## 4. Implémentation Backend (FastAPI)

Dans `backend/main.py`, le contrôle d'accès est garanti au niveau du routeur HTTP via le système d'injection de dépendances de FastAPI (`Depends(...)`).

Chaque requête authentifiée vérifie le jeton JWT, interroge l'état actuel de l'utilisateur dans `admin.users` (statut actif, rôle), et applique les gardes stricts :

```python
def get_current_user_profile(username: str = Depends(get_current_user)) -> dict:
    """Valide l'utilisateur actif et résout son rôle RBAC."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT role, is_active FROM admin.users WHERE username = :u"),
            {"u": username}
        ).fetchone()
        if not result or not result[1]:
            raise HTTPException(status_code=401, detail="User not active or not found")
        raw_role = (result[0] or "viewer").lower().strip()
        role = "viewer" if raw_role == "user" else raw_role
        return {"username": username, "role": role}

def verify_admin(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized. Admin role required.")
    return user["username"]

def verify_security_analyst_or_admin(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst'):
        raise HTTPException(status_code=403, detail="Not authorized. Security Analyst or Admin role required.")
    return user["username"]

def verify_operator_or_admin(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'operator'):
        raise HTTPException(status_code=403, detail="Not authorized. Operator or Admin role required.")
    return user["username"]

def verify_can_operate(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst', 'operator'):
        raise HTTPException(status_code=403, detail="Not authorized. Read-write role required.")
    return user["username"]

def verify_can_scan(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst', 'operator'):
        raise HTTPException(status_code=403, detail="Not authorized. Scan execution role required.")
    return user["username"]

def verify_can_view_audit(user: dict = Depends(get_current_user_profile)) -> str:
    if user["role"] not in ('admin', 'security_analyst', 'viewer'):
        raise HTTPException(status_code=403, detail="Not authorized to inspect audit logs.")
    return user["username"]
```

---

## 5. Protection du Compte Administrateur Racine

Le compte `admin` initial (Super Admin) bénéficie d'une protection native :
* Impossible de rétrograder son rôle ou de le modifier.
* Impossible de désactiver ou de supprimer le compte `admin`.
* Cette règle est validée côté Backend (`update_user`) et verrouillée côté Interface Web (`UserManagement.tsx`).

---

## 6. Conformité Réglementaire (NIS 2 & ISO 27001)

L'introduction de ce modèle satisfait explicitement aux exigences :
* **NIS 2 Article 21 (2.i)** : Hygiène informatique de base et formation en cybersécurité, gestion des droits d'accès.
* **ISO/IEC 27001 - Contrôle A.9.2** : Gestion des accès utilisateurs et attribution de droits d'accès privilégiés.
* **ISO/IEC 27001 - Contrôle A.12.4** : Journalisation et surveillance, avec protection des journaux contre la falsification par les opérateurs ou tiers non habilités.
