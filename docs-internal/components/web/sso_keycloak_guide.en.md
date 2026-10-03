# User Guide: Enterprise SSO (Keycloak) & Multi-Factor Authentication (MFA)

This guide details the setup, configuration, and operation of **Single Sign-On (SSO / OIDC)** integrated with **Multi-Factor Authentication (MFA)** for the **RTMS** platform via **Keycloak**.

---

## 1. Keycloak Architecture & Deployment

Keycloak runs within an isolated Docker environment with its own dedicated PostgreSQL instance (no interference with the main RTMS database).

### Starting the Containers
Inside directory `~/keycloak-dev`:
```bash
docker compose up -d
```

### URLs and Ports
* **Keycloak Admin Console**: `http://localhost:8085`
* **Keycloak PostgreSQL Database**: Port `5433` (internal: `5432`)
* **RTMS Web Frontend**: `http://localhost:5173` (or `http://localhost:8080`)
* **RTMS Backend API**: `http://localhost:8000`

---

## 2. OIDC Configuration in Keycloak

1. **Realm**: `rtms`
2. **OpenID Connect Client**:
   * **Client ID**: `rtms-web`
   * **Client authentication**: `ON`
   * **Valid Redirect URIs**:
     * `http://localhost:8000/*`
     * `http://localhost:5173/*`
     * `*`
   * **Web Origins**: `*`

---

## 3. Configuration in RTMS Web

In **System Settings / Scanner Configuration** > **Authentication Provider**:
* **Active Type**: `SSO / OpenID Connect`
* **OIDC Issuer URL**: `http://localhost:8085/realms/rtms`
* **Client ID**: `rtms-web`
* **Client Secret**: *(Client secret copied from the Keycloak Credentials tab)*

---

## 4. Test Account Credentials

A pre-configured demo user is available:
* **Username**: `testuser`
* **Password**: `Password123!`
* **Email**: `testuser@rtms.local`
* **RTMS Role**: `user` (provisioned automatically via Just-In-Time enrollment)

---

## 5. Enabling MFA (2FA) in Keycloak

In an SSO architecture, MFA is managed entirely by the Identity Provider (Keycloak) without requiring custom code in the application layer.

### Option A: Enable MFA for `testuser` only
1. Open Keycloak Admin Console: `http://localhost:8085` (Realm `rtms`).
2. Navigate to **Users** > click **`testuser`**.
3. In **Required user actions**, select **Configure OTP**.
4. Click **Save**.

### Option B: Enforce MFA for All Users (NIS 2 Mandatory Control)
1. In Keycloak left menu, open **Authentication**.
2. Click the **Required actions** tab.
3. Check the **Default action** toggle next to **Configure OTP**.

---

## 6. Login Flow Walkthrough (SSO + MFA)

1. **Access RTMS**: Navigate to `http://localhost:5173`.
2. **Initiate SSO**: Click **"Sign in with Enterprise SSO"**.
3. **Keycloak Authentication (Factor 1)**:
   * Enter `testuser` and `Password123!`.
4. **MFA Verification (Factor 2)**:
   * **First Login**: Keycloak generates a TOTP QR code. Scan it with an authenticator app (*Google Authenticator*, *Microsoft Authenticator*, *FreeOTP*), then enter the 6-digit code.
   * **Subsequent Logins**: Simply enter the rotating 6-digit TOTP code.
5. **Redirection to RTMS**: The user is authenticated and redirected to their role-assigned dashboard.

---

## 7. Session Management & Break-Glass Recovery

### SSO Session Lifetimes
* **Idle Timeout**: 30 minutes default.
* **Max Session Length**: 10 hours.
* *(Configurable in Keycloak: Realm Settings > Sessions).*

### Forcing Re-authentication during Testing
* Use an **Incognito / Private Browsing** window.
* Or revoke active sessions from Keycloak: **Sessions** > **Revoke all active sessions**.

### Local Break-Glass Account (NIS 2 Requirement)
If the external SSO identity provider experiences an outage:
1. On the RTMS login screen, click **"🔒 Local Emergency Break-Glass Account"**.
2. Log in directly using the local root administrator account (`admin`).
