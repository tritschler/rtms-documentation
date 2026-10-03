# Guide d'Utilisation : SSO (Keycloak) et Authentification Multi-Facteurs (MFA)

Ce guide détaille l'installation, la configuration et l'utilisation du **Single Sign-On (SSO / OIDC)** couplé au **Multi-Factor Authentication (MFA)** pour la plateforme **RTMS** avec **Keycloak**.

---

## 1. Architecture & Déploiement Keycloak

Keycloak fonctionne dans un environnement Docker isolé avec sa propre base de données PostgreSQL dédiée (aucun impact sur la base de données principale RTMS).

### Démarrage des conteneurs
Dans le dossier `~/keycloak-dev` :
```bash
docker compose up -d
```

### URLs et Ports
* **Console d'administration Keycloak** : `http://localhost:8085`
* **Base PostgreSQL dédiée Keycloak** : port `5433` (interne : `5432`)
* **Interface Web RTMS** : `http://localhost:5173` (ou `http://localhost:8080`)
* **API Backend RTMS** : `http://localhost:8000`

---

## 2. Configuration OIDC dans Keycloak

1. **Realm** : `rtms`
2. **Client OpenID Connect** :
   * **Client ID** : `rtms-web`
   * **Client authentication** : `ON`
   * **Valid Redirect URIs** :
     * `http://localhost:8000/*`
     * `http://localhost:5173/*`
     * `*`
   * **Web Origins** : `*`

---

## 3. Configuration dans RTMS

Dans **Paramètres Système / Configuration Scanner** > **Fournisseur d'Authentification** :
* **Type actif** : `SSO / OpenID Connect`
* **OIDC Issuer URL** : `http://localhost:8085/realms/rtms`
* **Client ID** : `rtms-web`
* **Client Secret** : *(Clé secrète issue de l'onglet Credentials du client Keycloak)*

---

## 4. Identifiants du Compte de Test

Un compte utilisateur de démonstration est préconfiguré :
* **Identifiant (Username)** : `testuser`
* **Mot de passe** : `Password123!`
* **Email** : `testuser@rtms.local`
* **Rôle RTMS** : `user` (provisionné automatiquement Just-In-Time)

---

## 5. Activation du MFA (2FA) dans Keycloak

Dans une architecture SSO, le MFA est entièrement géré par l'Identity Provider (Keycloak) sans nécessiter de code additionnel dans l'application.

### Option A : Activer le MFA pour `testuser` uniquement
1. Rendez-vous sur la console d'administration Keycloak : `http://localhost:8085` (Realm `rtms`).
2. Allez dans **Users** > cliquez sur **`testuser`**.
3. Dans le champ **Required user actions**, sélectionnez **Configure OTP**.
4. Cliquez sur **Save**.

### Option B : Rendre le MFA obligatoire pour tous les utilisateurs (NIS 2)
1. Dans le menu de gauche de Keycloak, allez dans **Authentication**.
2. Cliquez sur l'onglet **Required actions**.
3. Activez la case **Default action** en face de **Configure OTP**.

---

## 6. Déroulement du Flux de Connexion (SSO + MFA)

1. **Accès à RTMS** : Rendez-vous sur `http://localhost:5173`.
2. **Lancement du SSO** : Cliquez sur le bouton **« Se connecter avec SSO d'entreprise »**.
3. **Mire Keycloak (Facteur 1)** :
   * Saisissez `testuser` et `Password123!`.
4. **Validation MFA (Facteur 2)** :
   * **Première connexion** : Keycloak affiche un QR code. Scannez-le avec une application TOTP (*Google Authenticator*, *Microsoft Authenticator*, *FreeOTP*, etc.) puis entrez le code à 6 chiffres.
   * **Connexions suivantes** : Saisissez simplement le code à 6 chiffres généré par votre application.
5. **Redirection vers RTMS** : L'utilisateur est validé et arrive connecté sur son tableau de bord avec les droits appropriés.

---

## 7. Gestion des Sessions et Mode Secours (Break-Glass)

### Durée de validité de la session SSO
* **Inactivité (Idle)** : 30 minutes par défaut (reconnexion requise si inactif).
* **Durée maximale (Max)** : 10 heures.
* *(Ces durées sont ajustables dans Keycloak : Realm Settings > Sessions).*

### Pour forcer une ré-authentification lors des tests
* Ouvrir une nouvelle **fenêtre de navigation privée**.
* Ou révoquer les sessions actives depuis Keycloak : **Sessions** > **Revoke all active sessions**.

### Mode Secours Local (Break-Glass - Exigence NIS 2)
Si le serveur SSO est en maintenance ou inaccessible :
1. Sur la page de login RTMS, cliquez sur **« 🔒 Compte de secours local (Break-Glass) »**.
2. Connectez-vous directement avec le compte administrateur local (ex: `admin`).
