# Modèle de Contrôle d'Accès Basé sur les Rôles (RBAC) & Périmètres Évolutifs (Dual-Tier)

La plateforme RTMS implémente un modèle **RBAC (Role-Based Access Control) Dual-Tier**, conçu pour couvrir avec la même efficacité :
1. **Les TPE / PME** (Mode Standard) : attribution simple et directe d'un rôle avec portée globale (`*`), sans charge administrative ni formation requise.
2. **Les Grandes Entreprises & Groupes Multi-sites** (Mode Entreprise) : ségrégation fine avec périmètres d'assignation contextuels (**Scopes** : site géographique, sous-réseau CIDR, tag d'actifs) et synchronisation dynamique avec les annuaires d'entreprise (**SSO / IdP Group Mappings** via Microsoft Entra ID, Okta, Keycloak).

---

## 1. Principes Fondamentaux

Le modèle repose sur quatre piliers de sécurité :
1. **Principe du Moindre Privilège (*Least Privilege*)** : chaque utilisateur dispose uniquement des habilitations strictement requises pour sa mission.
2. **Ségrégation des Tâches (*Segregation of Duties*)** : les tâches de gestion réseau (opérateur) sont séparées du triage des risques (analyste SOC) et de la validation souveraine des dérogations (CISO / RSSI).
3. **Piste d'Audit Immuable et Isolée** : l'accès aux journaux d'audit de sécurité et de conformité (`/api/audit/*`) est strictement protégé. Les opérateurs réseau n'ont pas accès aux logs d'audit pour éviter tout risque de dissimulation, tandis que les auditeurs (`viewer`) et le RSSI y ont accès sans aucun droit d'écriture.
4. **Cloisonnement Contextuel par Périmètre (*Scoped Enforcement*)** : en environnement multi-sites, les habilitations d'un opérateur ou d'un remédiateur sont bornées à leur périmètre technique (ex: `site:paris`, `subnet:10.10.0.0/16`, `tag:env:prod`).

---

## 2. Définition des 6 Rôles Opérationnels

| Rôle | Désignation | Missions & Responsabilités |
| :--- | :--- | :--- |
| **`admin`** | Administrateur Système | Contrôle total de la plateforme. Gestion des utilisateurs, licences, paramètres système, cycle de vie des briques logicielles, et purge des données orphelines. |
| **`ciso`** | RSSI / CISO / Risk Officer | Gouvernance de sécurité et validation souveraine des dérogations CVE (`accept_risk`), supervision transverse des vulnérabilités et consultation des pistes d'audit réglementaires. |
| **`security_analyst`** | Analyste SOC / Sécurité | Triage des vulnérabilités CVE, création et assignation des *findings*, qualification des alertes d'intrusion et déclenchement de scans de vérification. |
| **`remediator`** | Remédiateur / Asset Owner | Responsable applicatif ou DevOps : suivi et mise à jour de l'état de remédiation des tickets/findings sur son périmètre, sans privilège d'administration réseau. |
| **`operator`** | Opérateur Réseau / Scanners | Gestion opérationnelle du parc d'actifs (édition, exclusion IP, renommage de sous-réseaux, suppression), configuration des scanners, redémarrage direct des scanners (`RESTART`), gestion des tokens d'agents locaux et scans de découverte. |
| **`viewer`** | Auditeur / Conformité / DPO | Consultation en lecture seule complète de la cartographie, de l'inventaire, des vulnérabilités et **des journaux d'audit de conformité** (`/api/audit/*`) à des fins de preuve réglementaire (NIS 2 / ISO 27001). **Zéro droit de mutation ou d'action.** |

---

## 3. Matrice Complète des Permissions

| Domaine Fonctionnel / Endpoint | `admin` | `ciso` | `security_analyst` | `operator` | `remediator` | `viewer` (Auditeur) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gestion Utilisateurs & Rôles** (`/api/users*`) | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| **Configuration Système & Licences** (`/api/license*`, `/api/system/*`) | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| **Journaux d'Audit Système & Connexions** (`/api/audit/*`) | ✅ Oui | ✅ **Oui (Gouv)** | ✅ Oui | ❌ 403 | ❌ 403 | ✅ **Oui (Preuves NIS 2)** |
| **Démarrer / Arrêter / Services** | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| **Redémarrage Scanner Réseau (`RESTART`)** | ✅ Oui | ❌ 403 | ❌ 403 | ✅ Oui | ❌ 403 | ❌ 403 |
| **Gestion Tokens Agents Locaux** | ✅ Oui | ❌ 403 | ❌ 403 | ✅ Oui | ❌ 403 | ❌ 403 |
| **Déclenchement Scans Réseau** | ✅ Oui | ❌ 403 | ✅ Oui | ✅ Oui | ❌ 403 | ❌ 403 |
| **Gestion des Actifs** (Hostname, Exclusions) | ✅ Oui | ❌ 403 | ✅ Oui | ✅ Oui | ❌ Lecture Seule | ❌ Lecture Seule |
| **Suppression d'Actifs & Renommage Sous-réseaux** | ✅ Oui | ❌ 403 | ❌ 403 | ✅ Oui | ❌ 403 | ❌ 403 |
| **Purge des Actifs Orphelins** | ✅ Oui | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| **Inventaire Logiciel** (Ajout, Édition) | ✅ Oui | ❌ 403 | ✅ Oui | ✅ Oui | ❌ Lecture Seule | ❌ Lecture Seule |
| **Acceptation des Risques CVE** (`/api/vulnerabilities/accept_risk`) | ✅ Oui | ✅ **Oui (Souverain)** | ✅ Oui (SOC) | ❌ 403 | ❌ 403 | ❌ 403 |
| **Création & Escalade des Findings** | ✅ Oui | ✅ Oui | ✅ **Oui (SOC)** | ❌ 403 | ❌ 403 | ❌ 403 |
| **Mise à Jour Statut Finding / Remédiation** | ✅ Oui | ✅ Oui | ✅ Oui | ✅ Oui | ✅ **Oui (Remédiation)** | ❌ Lecture Seule |
| **Gestion Alertes Sécurité** (Clôture, Whitelist) | ✅ Oui | ✅ Oui | ✅ **Oui (SOC)** | ❌ 403 | ❌ 403 | ❌ 403 |

---

## 4. Architecture Technique des Périmètres (Scopes)

### Schéma de données PostgreSQL :

```sql
-- Habilitations contextuelles
CREATE TABLE admin.user_role_scopes (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES admin.users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    scope_type VARCHAR(32) NOT NULL DEFAULT 'global', -- 'global', 'site', 'subnet', 'tag'
    scope_value VARCHAR(128) NOT NULL DEFAULT '*',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_role_scope UNIQUE(user_id, role, scope_type, scope_value)
);

-- Mappings dynamiques de groupes SSO
CREATE TABLE admin.sso_group_mappings (
    id SERIAL PRIMARY KEY,
    idp_group_name VARCHAR(128) NOT NULL UNIQUE,
    mapped_role VARCHAR(32) NOT NULL,
    scope_type VARCHAR(32) NOT NULL DEFAULT 'global',
    scope_value VARCHAR(128) NOT NULL DEFAULT '*',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
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
* **NIS 2 Article 21 (2.i)** : Hygiène informatique de base et gestion rigoureuse des droits d'accès.
* **ISO/IEC 27001 - Contrôle A.9.2** : Gestion des accès utilisateurs et attribution de droits d'accès privilégiés.
* **ISO/IEC 27001 - Contrôle A.12.4** : Journalisation et surveillance, avec protection des journaux contre la falsification par les opérateurs ou tiers non habilités.

