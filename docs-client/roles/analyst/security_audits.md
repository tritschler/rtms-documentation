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
