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

* **Politique de Complexité & Validation Centralisée** :
  Tout mot de passe défini ou modifié (premier login, renouvellement, changement via profil, création ou réinitialisation par un administrateur) doit respecter la politique stricte de sécurité validée côté serveur :
  * **Longueur minimale** : 8 caractères (recommandé 12 caractères).
  * **Composition** : Au moins une majuscule (`A-Z`), une minuscule (`a-z`) et un chiffre (`0-9`).
  * **Sécurité contextuelle** : Le mot de passe ne peut pas être identique au mot de passe actuel et ne doit pas contenir le nom d'utilisateur.
  * **Validation interactive** : Une checklist visuelle dynamique valide chaque critère en temps réel sur l'écran de profil et de réinitialisation.
* **Génération Automatique de Mot de Passe Temporaire** :
  Depuis la console d'administration (`Créer un utilisateur` ou `Modifier un utilisateur`), un bouton **Générer** permet de produire un mot de passe temporaire cryptographiquement robuste de 12 caractères (majuscules, minuscules, chiffres et caractères spéciaux). L'option de renouvellement forcé à la première connexion (`must_change_password`) est automatiquement activée.
* **Authentification Multi-Facteurs (MFA/TOTP)** :
  Obligatoire pour les comptes administrateurs. Configurable via une application standard (Google Authenticator, Microsoft Authenticator, FreeOTP).
* **Expiration Adaptative des Mots de Passe** :
  Expiration tous les 90 jours avec préavis d'avertissement à J-14 pour les comptes sans MFA. Les comptes sécurisés par MFA sont exemptés de rotation forcée conformément aux recommandations NIST SP 800-63B et ISO 27001.
* **Intégration d'Annuaire d'Entreprise (LDAP / SSO)** :
  Connexion possible à Active Directory, OpenLDAP, ou à un fournisseur d'identité OIDC/SAML (ex : Keycloak, Okta, Azure AD / Entra ID). Pour ces comptes, la politique de mot de passe est déléguée au fournisseur d'identité d'entreprise.

