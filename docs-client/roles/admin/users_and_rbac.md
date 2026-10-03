# Gestion des Utilisateurs & Rôles d'Accès (RBAC)

La console d'administration des utilisateurs (`/admin/users`) permet de configurer les comptes, les autorisations et les politiques d'authentification de votre organisation.

---

## 1. Rôles Disponibles & Permissions

RTMS propose un modèle de contrôle d'accès basé sur les rôles (**RBAC**) strict :

| Rôle | Périmètre & Droits | Idéal Pour |
| :--- | :--- | :--- |
| **Administrateur (`admin`)** | Accès total : gestion des utilisateurs, configuration des sondes, paramétrage réseau, tokens API, intégration SSO/LDAP. | Responsable informatique, Administrateur sécurité |
| **Analyste SOC (`analyst`)** | Triage des vulnérabilités, gestion des menaces, acquittement des alertes, lancement de scans à la demande. | Équipe SOC, Analyste cybersécurité |
| **Auditeur (`auditor`)** | Consultation en lecture seule de l'ensemble du système, accès aux journaux d'audit et export des rapports de conformité NIS2. | Auditeur interne/externe, RSSI, DPO |
| **Utilisateur (`user`)** | Consultation de l'inventaire des actifs et consultation des alertes réseau. | Opérateur réseau, Technicien support |

---

## 2. Politiques de Sécurité des Mots de Passe & MFA

* **Authentification Multi-Facteurs (MFA/TOTP)** :
  Obligatoire pour les comptes administrateurs. Configurable via une application standard (Google Authenticator, Microsoft Authenticator, FreeOTP).
* **Expiration Adaptative des Mots de Passe** :
  Expiration tous les 90 jours avec préavis d'avertissement à J-14 pour les comptes sans MFA. Les comptes sécurisés par MFA sont exemptés de rotation forcée conformément aux recommandations NIST SP 800-63B et ISO 27001.
* **Intégration d'Annuaire d'Entreprise (LDAP / SSO)** :
  Connexion possible à Active Directory, OpenLDAP, ou à un fournisseur d'identité OIDC/SAML (ex : Keycloak, Okta, Azure AD / Entra ID).
