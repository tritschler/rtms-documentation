# Audits de Sécurité Intégrés (Plugins Non Intrusifs)

Lors des scans approfondis (**Deep Scan**), RTMS exécute des modules d'audit de sécurité automatisés et non destructifs pour détecter des erreurs courantes de configuration réseau.

---

## 1. Audit de Sécurité Email & Messagerie (SMTP)

* **Détection de Relais Ouvert (Open Relay)** :  
  La sonde teste si le serveur SMTP accepte de relayer des emails vers un domaine externe sans authentification préalable (RFC 5321).
  > **Méthode sûre** : La sonde s'arrête immédiatement après la commande `RCPT TO` et réinitialise la session via `RSET`, évitant ainsi l'envoi effectif de tout message spam.
* **Énumération d'utilisateurs (`VRFY`)** :  
  Vérifie si le serveur permet à un attaquant de lister les comptes de messagerie valides de l'organisation.
* **Chiffrement STARTTLS & Certificats** :  
  Contrôle la présence du chiffrement obligatoire et la validité du certificat TLS présenté par le serveur de messagerie.

---

## 2. Intégrité DNS & Protection Anti-Usurpation

RTMS interroge les serveurs DNS d'entreprise configurés pour valider la robustesse de votre politique contre le phishing et l'usurpation d'identité :
* **SPF (Sender Policy Framework)** : Vérifie la syntaxe de l'enregistrement TXT SPF et le mécanisme de rejet (`-all` recommandé vs `~all`).
* **DKIM (DomainKeys Identified Mail)** : Contrôle la présence et la force cryptographique des clés publiques des sélecteurs DKIM.
* **DMARC (Domain-based Message Authentication)** : Analyse la politique d'alignement (`p=reject` vs `p=none`) et le paramétrage des rapports de conformité.

---

## 3. Détection de Protocoles Obsolètes & Bases Ouvertes

* **Partages Windows & Protocole SMBv1** :  
  Alerte immédiate en cas de détection du protocole vulnérable SMBv1 (vecteur d'attaques de type *WannaCry* / *EternalBlue*) ou d'absence de signature SMB obligatoire.
* **Bases de Données Non Authentifiées** :  
  Détecte les instances PostgreSQL, MySQL/MariaDB, Redis ou MongoDB exposées sur le réseau avec les comptes par défaut ou sans mot de passe d'administration.

---

## 4. Cyberhygiène & Sécurité des Échanges (Audit Continu NIS 2)

RTMS intègre un moteur d'évaluation continue de la posture de messagerie et de chiffrement des transports, directement visible sur le tableau de bord d'accueil (**Cyberhygiène & Sécurité des Échanges**).

### A. Les 5 Piliers Évalués
1. **🛡️ Anti-Spoofing (25 pts)** : Présence et fermeté de la politique SPF (`-all` ou `~all`), alignement DMARC (`p=reject` ou `quarantine`), et intégrité des sélecteurs DKIM.
2. **🔒 Transport & DANE (35 pts)** : Support obligatoire de STARTTLS avec chiffrement moderne (TLS 1.3), ciphers avec confidentialité persistante (PFS), et validation des certificats TLSA (DANE) ou MTA-STS.
3. **🔏 Zone DNSSEC (20 pts)** : Signature cryptographique de la zone DNS du domaine et des serveurs MX (chaîne de confiance DS/DNSKEY).
4. **🌐 IPv6 Dual-Stack (10 pts)** : Disponibilité et connectivité IPv6 sur les serveurs de messagerie.
5. **🛣️ Autorisations RPKI (10 pts)** : Validation des annonces de routage BGP (ROA) pour empêcher le détournement d'itinéraires réseau.

### B. Exécution Autonome par le Backend
* **Ordonnancement en tâche de fond** : Le backend RTMS exécute une réévaluation automatique **toutes les 12 heures** de manière autonome, garantissant la fraîcheur du score sans nécessiter d'intervention humaine ni dépendre de sondes locales.
* **Audit à la demande** : Les opérateurs peuvent forcer un recalcul instantané à tout moment via le bouton **« Audit Détaillé »** ou depuis la configuration du scanner.

### C. Attribution Automatique de Tâches de Remédiation
* **Génération de Finding** : Si le score de cyberhygiène est inférieur à **80%** ou présente des vulnérabilités critiques (ex. usurpation d'identité possible), le système génère automatiquement une tâche dans **Security Findings** (`/findings`), assignée à l'administrateur système ou au responsable sécurité.
* **Échéance et sévérité dynamiques** :
  * Score < 50% ou anti-spoofing défaillant : **CRITICAL** (échéance sous 7 jours).
  * Score entre 50% et 70% : **HIGH** (échéance sous 14 jours).
  * Score entre 70% et 80% : **MEDIUM** (échéance sous 30 jours).
* **Auto-Résolution** : Dès que les correctifs DNS ou serveurs sont appliqués et validés par le prochain audit (Score ≥ 80%), la tâche passe automatiquement au statut **`RESOLVED`**.

