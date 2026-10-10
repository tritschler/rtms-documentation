# Audit de Sécurité Email & DNS (SPF, DKIM, DMARC, SMTP)

La suite **RTMS (Real-Time Monitoring System)** intègre une stratégie de vérification de la sécurité de la messagerie électronique et de la résolution DNS adaptée aussi bien aux environnements d'entreprise fermés (Zero Trust / intranet) qu'aux infrastructures exposées sur Internet.

---

## 1. Audit DNS & Protection contre l'Usurpation (SPF, DKIM, DMARC, DNSSEC, MTA-STS)

Le module `dns_audits/dns_integrity.py` effectue une analyse de l'intégrité de la résolution DNS et valide la conformité des politiques de sécurité e-mail du domaine.

### Fonctionnement en Réseau d'Entreprise Fermé

Dans un réseau d'entreprise isolé (sans accès direct aux DNS publics comme `1.1.1.1` ou `8.8.8.8`) :
* Le scanner interroge en priorité le **serveur DNS interne** spécifié dans la configuration ou le résolveur système (`/etc/resolv.conf` / Active Directory DNS).
* Il vérifie la présence et la syntaxe des enregistrements de sécurité :
  * **SPF (`v=spf1 ...`)** : autorisations d'adresses IP. Détecte la présence de la directive permissive ou dangereuse `+all` (alerte `CRITICAL`), les politiques neutres `?all` (`LOW`), et le dépassement de la limite RFC 7208 des 10 lookups DNS (`HIGH`).
  * **DMARC (`_dmarc.<domaine>`)** : politique d'alignement (`p=none`, `quarantine` ou `reject`). Signale le mode passif/surveillance seule (`p=none`) et l'absence de boîte de reporting d'agrégation `rua=`.
  * **DKIM (`<selector>._domainkey.<domaine>`)** : validation des clés publiques publiées. Supporte les sélecteurs courants et les sélecteurs personnalisés d'entreprise.
  * **DNSSEC** : vérifie la signature cryptographique de la zone (enregistrements `DS` et `DNSKEY`).
  * **MTA-STS (RFC 8461) & TLS-RPT (RFC 8460)** : vérifie la présence de politiques `_mta-sts` et de reporting TLS `_smtp._tls` pour contrer le déclassement STARTTLS en transit.
  * **FCrDNS (Forward-Confirmed Reverse DNS)** : vérifie la cohérence entre les serveurs MX, leurs adresses IP, leurs enregistrements PTR inverses et la résolution aller-retour.

### Paramètres de Configuration

Ces paramètres peuvent être définis dans `scanner.properties` ou injectés dynamiquement via la console Web :

| Clé de Configuration | Type | Défaut | Description |
| :--- | :--- | :--- | :--- |
| `dns.audit` | Booléen | `false` | Active ou désactive l'audit DNS lors des cycles de scan. |
| `dns.test.domain` | Chaîne | `example.com` | Nom de domaine cible à auditer (ex: `entreprise.local`). |
| `dns.server` | Chaîne (IP) | *(vide)* | IP du serveur DNS interne d'entreprise (ex: `10.0.0.53`). Si non renseigné, utilise le résolveur système. |
| `dns.dkim_selectors` | Liste CSV | *(défauts)* | Sélecteurs DKIM spécifiques à tester (ex: `s1,corp,exchange`). |

---

## 2. Plugin Interne : Sécurité des Serveurs SMTP (`smtp_security.py`)

Le plugin [`internal_plugins/smtp_security.py`](file:///Users/marctritschler/git_projects/rtms-scanner/internal_plugins/smtp_security.py) audite directement les serveurs de messagerie découverts sur le réseau local lors des scans approfondis.

### Règle d'Exécution : Deep Scan Strict

> [!IMPORTANT]
> Conformément à la politique d'audit non intrusif de RTMS, ce plugin **ne s'exécute JAMAIS en mode découverte simple (`CMD_DISCOVER`)**. Il est strictement exécuté lorsque le mode **Deep Scan (`CMD_DISCOVER_SCAN` / `scanner.deep_scan = true`)** est actif et que des ports de messagerie sont détectés ouverts.

### Ports Ciblés
* **Port 25 (SMTP standard / relais)**
* **Port 465 (SMTPS - SSL/TLS implicite)**
* **Port 587 (SMTP Submission)**

### Vérifications Réalisées

1. **Chiffrement en Transit (STARTTLS / SMTPS)** :
   * Vérifie si le serveur annonce l'extension `STARTTLS` ou propose SMTPS direct.
   * En cas d'absence, une vulnérabilité `MEDIUM` est signalée (transmission de mots de passe ou d'e-mails en clair sur le LAN).
2. **Contrôle des Protocoles Obsolètes** :
   * Détecte si le serveur accepte des négociations avec **TLS 1.0 ou TLS 1.1** (vulnérabilités aux attaques de downgrade / BEAST / POODLE - sévérité `HIGH`).
3. **Validité du Certificat TLS** :
   * Contrôle l'expiration imminente du certificat SSL/TLS (< 30 jours) ou les certificats déjà expirés.
4. **Vulnérabilité Open Mail Relay (RFC 5321)** :
   * Tente une transaction non authentifiée `MAIL FROM` vers une boîte externe via `RCPT TO:<untrusted-relay-test@example.org>`.
   * **Sécurité garantie :** Le scanner envoie immédiatement la commande `RSET` (Reset). **Aucun e-mail n'est jamais transmis**.
   * Si le serveur accepte le destinataire sans exiger d'authentification préalable, une alerte `CRITICAL` est levée.
5. **Énumération d'Utilisateurs (`VRFY` / `EXPN`)** :
   * Teste si les commandes de divulgation de comptes locaux sont actives (alerte `LOW`).

### Configuration du Plugin

* **Désactivation individuelle** : `scanner.plugin.smtp_security = false`
* **Désactivation globale des plugins internes** : `scanner.internal_plugins_enabled = false`

---

## 3. Outil Autonome Externe : `tools/public_smtp_auditor.py`

Pour auditer des serveurs SMTP publics exposés sur Internet en dehors du cycle de scan interne de RTMS, un outil en ligne de commande indépendant est fourni.

### Conception & Portabilité

* **Aucune dépendance interne :** Ce script ne dépend d'aucun module propriétaire de la suite RTMS.
* **Exportable :** Le fichier [`tools/public_smtp_auditor.py`](file:///Users/marctritschler/git_projects/rtms-scanner/tools/public_smtp_auditor.py) peut être directement copié ou déplacé dans un autre dépôt Git ou sur une machine d'administration distante.

### Exemples d'Utilisation

```bash
# Audit complet d'un domaine public (Enregistrements MX + DNS SPF/DMARC/DKIM + Ports SMTP)
python3 tools/public_smtp_auditor.py example.com

# Sortie au format JSON pour automatisation / pipelines CI-CD
python3 tools/public_smtp_auditor.py --domain example.com --json

# Test direct d'un serveur de messagerie précis (IP ou FQDN)
python3 tools/public_smtp_auditor.py --host mail.example.com --port 25

# Test sur le port sécurisé SMTPS (465)
python3 tools/public_smtp_auditor.py --host mail.example.com --port 465 --ssl
```
