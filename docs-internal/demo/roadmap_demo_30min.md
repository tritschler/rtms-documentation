# 🧭 Roadmap de Démonstration RTMS (~30-35 min)

**Date :** Jeudi  
**Format :** Présentation dynamique & guidée de la plateforme RTMS  
**Objectif :** Démontrer la simplicité de déploiement, la visibilité en temps réel, la sécurité de l'accès et la conformité NIS2 sans surcharger l'audience.  
> *Note timing : Le découpage horaire ci-dessous est indicatif et sert de fil conducteur pour cadencer la démonstration sans obligation de blocage strict à 30 minutes pile.*

---

## ⏱️ Chronométrage Indicatif

* `[00:00 - 05:00]` — **1. Connexion & 3 Modes d'Authentification**
* `[05:00 - 09:00]` — **2. Présentation des 4 Rôles Utilisateurs (RBAC)**
* `[09:00 - 14:00]` — **3. Découverte de l'Interface, Barre Supérieure, Sidebar Dynamique & Dashboard**
* `[14:00 - 21:00]` — **4. Inventaire Réseau & Cartographie des Vulnérabilités**
* `[21:00 - 27:00]` — **5. Sécurité Avancée, Audits Intégrés & Conformité NIS2**
* `[27:00 - 32:00+]` — **6. Synthèse & Questions / Réponses**

---

## 1. Connexion & les 3 Modes d'Authentification (5 min)

> **Message clé :** RTMS s'adapte à n'importe quel environnement d'entreprise, du site isolé à la grande organisation avec annuaire centralisé.

- [ ] **Accès à la page de Login**
- [ ] **Présenter les 3 stratégies d'authentification disponibles :**
  1. **Locale (`local`) :**
     * Authentification directe en base de données sécurisée (chiffrement bcrypt).
     * Politique de sécurité NIS 2 intégrée : MFA (TOTP) obligatoire pour les administrateurs, rotation adaptative des mots de passe (90 jours sans MFA, exempté si MFA activé).
  2. **Annuaire d'Entreprise (`LDAP / Active Directory`) :**
     * Connexion aux annuaires d'entreprise existants avec provisioning Just-In-Time (JIT).
     * Résilience : cascade automatique sur les comptes locaux de secours en cas d'indisponibilité du serveur LDAP.
  3. **SSO Entreprise (`OIDC / Keycloak / Entra ID / Okta`) :**
     * Expérience Single Sign-On fluide avec délégation MFA.
     * Mode d'urgence *"Break-Glass"* local garanti pour les administrateurs.
- [ ] **Action :** Se connecter avec un compte Administrateur (avec validation TOTP / code MFA).

---

## 2. Présentation des 4 Rôles Utilisateurs (RBAC) (4 min)

> **Message clé :** Un modèle d'accès strict (Least Privilege) dès la connexion pour respecter les exigences de gouvernance et NIS2.

- [ ] **Exposer la matrice des 4 rôles natifs de RTMS :**
  1. **Admin (`admin`) :**
     * Contrôle intégral de la plateforme : gestion des sondes, politiques de scan, licences, tokens API, utilisateurs et configurations système.
  2. **Security Analyst (`analyst`) :**
     * Pilotage opérationnel de la sécurité : triage des vulnérabilités CVE, analyse du dashboard de menaces, acquittement d'alertes et corrélation SIEM/SOC.
  3. **Normal User (`user`) :**
     * Utilisation quotidienne réseau : consultation de l'inventaire en temps réel des actifs, recherche d'équipements et visualisation des alertes réseau.
  4. **Auditor (`auditor`) :**
     * Vue en lecture seule orientée conformité : consultation des journaux d'audit immutables, suivi des exigences réglementaires (NIS2 / Cyber Resilience Act CRA) et export de rapports opposables.
- [ ] **Transition vers l'interface :** Préciser que le rôle attribué modifie directement ce que l'utilisateur voit et peut faire à l'écran.

---

## 3. Interface, Navigation & Dashboard (5 min)

> **Message clé :** Une console épurée, réactive et contextuelle, dont l'affichage s'adapte automatiquement à la licence et aux droits de l'utilisateur.

- [ ] **Structure de l'espace de travail :**
  * **Barre supérieure (Header) :**
    * **Recherche Globale Magique (🔍) :** Petite loupe discrète dans la barre du haut qui s'agrandit avec animation au clic (ou via `Cmd+K` / `Ctrl+K`) pour rechercher instantanément un équipement (IP, nom d'hôte, MAC, constructeur) ou naviguer directement vers n'importe quel module de l'application.
    * **Raccourci vers les Paramètres (Settings ⚙️) :** Accès direct aux réglages rapides de l'application et de la console.
    * **Sélecteur de Thème :** Bascule instantanée entre le Mode Sombre (confort SOC) et le Mode Clair.
    * **Sélecteur de Langue :** Bascule à chaud FR / EN.
    * **Menu Profil :** Rappel du compte connecté et du rôle actif.
  * **Barre latérale gauche (Sidebar) :**
    * ⚠️ **Point fondamental à expliquer :** Le contenu de la barre latérale est **entièrement dynamique** ; il dépend directement de deux facteurs :
      1. Du **type de licence** souscrite (modules et fonctionnalités activés pour le client).
      2. Du **rôle de l'utilisateur** (filtrage strict RBAC : un *Normal User* ne verra pas l'administration, un *Auditor* verra la conformité sans les actions d'écriture).
- [ ] **Dashboard Principal (KPIs & Métriques de haut niveau) :**
  * Compteur d'équipements en ligne / hors-ligne.
  * Répartition des vulnérabilités par criticité (Critique, Élevée, Moyenne, Faible).
  * État de santé des sondes de détection en temps réel.
  * Flux des dernières anomalies et alertes de sécurité détectées.

---

## 4. Inventaire Réseau & Cartographie des Vulnérabilités (7 min)

> **Message clé :** Découverte 100 % automatisée et continue, sans aucun agent logiciel à déployer.

- [ ] **Accéder à la vue *Actifs*** (`/assets`).
- [ ] **Montrer les fonctionnalités de liste :**
  * Filtres par sous-réseau, tri par dernière détection, recherche instantanée.
  * Reconnaissance automatique : IP, MAC, constructeur matériel (OUI), OS déduit, nom d'hôte (DHCP snooping/DNS).
- [ ] **Ouvrir la Fiche Détail d'un équipement :**
  * Ports et services ouverts identifiés avec leurs versions logicielles exactes.
  * Rapprochement automatique avec la base locale **NVD (CVE)** et scores de sévérité CVSS.
  * **Notion clé à mentionner :** Ciblage granulaire **Deep Scan avec Double Consentement (*Dual Opt-In*)** pour protéger les équipements sensibles ou automates industriels (OT/SCADA).

---

## 5. Sécurité Réseau, Audits Intégrés & Conformité NIS2 (6 min)

> **Message clé :** RTMS n'est pas qu'un scanner passif, c'est un outil d'aide à la décision et à la mise en conformité.

- [ ] **Flux d'alertes & contrôles non intrusifs :**
  * Exemples concrets d'audits automatiques : serveurs SMTP ouverts / relais non sécurisés, conformité DNS (SPF, DKIM, DMARC), protocoles obsolètes (SMBv1), usurpation ARP.
- [ ] **Corrélation & Triage :**
  * Dashboard Menaces et contextualisation du risque (exploits actifs vs actifs isolés).
- [ ] **Aperçu Conformité & Rapports :**
  * Vue de conformité NIS2 (Article 21/23).
  * Génération/export d'un rapport opposable en 1 clic (PDF / CSV) pour les comités de direction ou auditeurs.

---

## 6. Synthèse & Clôture (~5 min)

- [ ] **Récapitulatif des points forts à laisser à l'esprit :**
  * **Zéro agent** : Déploiement non invasif et immédiat.
  * **Souverain & Résilient** : Base de vulnérabilités locale, fonctionnement possible en environnement déconnecté (*air-gapped*).
  * **Conçu pour NIS2** : Traçabilité, audit trail, rôles stricts et rapports intégrés.
- [ ] **Ouverture aux Questions / Réponses.**
