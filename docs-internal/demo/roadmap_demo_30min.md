# 🧭 Roadmap de Démonstration RTMS (30 minutes)

**Date :** Jeudi  
**Format :** Présentation dynamique & guidée de la plateforme RTMS  
**Objectif :** Démontrer la simplicité de déploiement, la visibilité en temps réel, la sécurité de l'accès et la conformité NIS2 sans surcharger l'audience.

---

## ⏱️ Chronométrage Indicatif

* `[00:00 - 05:00]` — **1. Connexion & 3 Modes d'Authentification**
* `[05:00 - 10:00]` — **2. Tour d'horizon de la Home Page / Dashboard**
* `[10:00 - 15:00]` — **3. Rôles & Gestion des Utilisateurs (RBAC)**
* `[15:00 - 22:00]` — **4. Inventaire Réseau & Cartographie des Vulnérabilités**
* `[22:00 - 27:00]` — **5. Sécurité Avancée, Audits Intégrés & Conformité NIS2**
* `[27:00 - 30:00]` — **6. Conclusion & Questions / Réponses**

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

## 2. Découverte de la Home Page & Navigation Globale (5 min)

> **Message clé :** Ergonomie moderne pensée pour les exploitants et analystes, prise en main immédiate.

- [ ] **Structure de l'espace de travail :**
  * **Barre supérieure (Header) :**
    * Recherche globale instantanée (recherche par IP, Hostname, MAC, sous-réseau).
    * Sélecteur de thème : Mode Sombre (confort SOC) / Mode Clair.
    * Sélecteur de langue : Bascule instantanée FR / EN.
  * **Menu latéral gauche :** Vue d'ensemble des modules (Dashboard, Actifs, Alertes, Menaces, Conformité, Administration).
- [ ] **Dashboard Principal (KPIs & Métriques de haut niveau) :**
  * Compteur d'équipements en ligne / hors-ligne.
  * Répartition des vulnérabilités par criticité (Critique, Élevée, Moyenne, Faible).
  * État de santé des sondes de détection en temps réel.
  * Dernières alertes d'anomalies de sécurité détectées.

---

## 3. Rôles d'Accès & Gestion des Utilisateurs (RBAC) (5 min)

> **Message clé :** Cloisonnement strict des responsabilités pour respecter les exigences de gouvernance et NIS2.

- [ ] **Aller dans le menu *Administration > Utilisateurs & Rôles*** (`/admin/users`).
- [ ] **Présenter les 4 rôles standards :**
  1. **Administrateur (`admin`) :** Contrôle total (paramétrage sondes, politiques de scan, licences, utilisateurs).
  2. **Analyste SOC (`analyst`) :** Triage des vulnérabilités CVE, analyse des menaces, corrélation SIEM/SOC.
  3. **Auditeur (`auditor`) :** Consultation en lecture seule, accès aux journaux d'audit et exports de conformité réglementaire (NIS2/CRA).
  4. **Opérateur / Utilisateur (`user`) :** Suivi de l'inventaire quotidien des actifs et consultation des alertes réseau.
- [ ] **Montrer :**
  * La création / édition d'un utilisateur et l'attribution de son rôle.
  * L'application de la politique MFA / état d'enrôlement du compte.

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

## 5. Sécurité Réseau, Audits Intégrés & Conformité NIS2 (5 min)

> **Message clé :** RTMS n'est pas qu'un scanner passif, c'est un outil d'aide à la décision et à la mise en conformité.

- [ ] **Flux d'alertes & contrôles non intrusifs :**
  * Exemples concrets d'audits automatiques : serveurs SMTP ouverts / relais non sécurisés, conformité DNS (SPF, DKIM, DMARC), protocoles obsolètes (SMBv1), usurpation ARP.
- [ ] **Corrélation & Triage :**
  * Dashboard Menaces et contextualisation du risque (exploits actifs vs actifs isolés).
- [ ] **Aperçu Conformité & Rapports :**
  * Vue de conformité NIS2 (Article 21/23).
  * Génération/export d'un rapport opposable en 1 clic (PDF / CSV) pour les comités de direction ou auditeurs.

---

## 6. Synthèse & Clôture (3 min)

- [ ] **Récapitulatif des points forts à laisser à l'esprit :**
  * **Zéro agent** : Déploiement non invasif et immédiat.
  * **Souverain & Résilient** : Base de vulnérabilités locale, fonctionnement possible en environnement déconnecté (*air-gapped*).
  * **Conçu pour NIS2** : Traçabilité, audit trail, rôles stricts et rapports intégrés.
- [ ] **Ouverture aux Questions / Réponses.**
