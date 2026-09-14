# RTMS Suite - Architecture & Spécifications des Plugins Externes (`plugin.md`)

Ce document constitue la documentation technique de référence pour la conception, la sécurisation, la validation et le cycle de vie des **plugins externes** dans la suite **Risk & Threat Management System (RTMS)**.

---

## 1. Vue d'Ensemble & Philosophie d'Architecture

Le moteur de découverte et d'audit **RTMS Scanner** utilise une architecture hybride :
1. **Plugins Internes** : intégrés et compilés directement dans le binaire natif Nuitka (`rtms-scanner`).
2. **Plugins Externes** : scripts Python (`.py`) autonomes chargés dynamiquement à chaud à chaque cycle de scan, sans nécessiter de recompilation du scanner.

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RTMS Web Dashboard (Admin)                            │
│           • Upload fichier .py  • Activation/Désactivation  • Suppression       │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND (/api/settings/plugins/upload)                   │
│  1. Vérification extension (.py strict)                                          │
│  2. Analyse statique AST (PluginCodeValidator de rtms_commons)                   │
│  3. Rejet immédiat si syntaxe invalide ou appels dangereux (os.system, etc.)     │
│  4. Extraction automatique des métadonnées (self.info)                          │
│  5. Stockage disque ($RTMS_PLUGINS_DIR) & Indexation en base admin.external_plugins│
│  6. Audit immuable en base de données (admin.system_audit)                      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             RTMS SCANNER ENGINE                                 │
│  1. Découverte des cibles & ports ouverts (Nmap / ARP / SYN)                    │
│  2. Re-validation statique AST des fichiers présents dans $RTMS_PLUGINS_DIR     │
│  3. Import dynamique sécurisé (importlib) & Instanciation                       │
│  4. Évaluation check_requirements(target_ip, target_services)                   │
│  5. Exécution isolée run_audit(...) sous Crash Guard (BasePlugin.execute)       │
│  6. Enregistrement des vulnérabilités dans le schéma scanner.cve / telemetry     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Politique de Sécurité & Cadre de Validation Statique (AST)

Afin d'éviter tout risque d'exécution de code arbitraire (*Remote Code Execution* - RCE) lors de l'upload de scripts Python personnalisés, le framework applique une validation statique rigoureuse via le module natif `ast` (**Abstract Syntax Tree**), exécutée par `rtms_commons.plugin_validator.PluginCodeValidator`.

### A. Règle d'or : Python uniquement (`.py`)
- Seuls les fichiers avec l'extension `.py` sont acceptés.
- Tout autre type de fichier (`.txt`, `.sh`, `.bin`, `.exe`, etc.) est **systématiquement rejeté** avec une erreur `400 Bad Request`.

### B. Contrôle d'intégrité et liste noire de sécurité
Le code source est inspecté **avant toute exécution ou importation en mémoire** :

| Type de contrôle | Éléments bloqués | Règle / Conséquence |
| :--- | :--- | :--- |
| **Modules interdits** | `subprocess`, `shutil`, `ctypes`, `pty`, `pickle`, `posix`, `winreg` | **Rejet immédiat** : interdiction d'invoquer des commandes système ou de manipuler la mémoire bas niveau. |
| **Fonctions dangereuses** | `eval()`, `exec()`, `compile()`, `__import__()` | **Rejet immédiat** : interdiction d'évaluation dynamique opaque. |
| **Méthodes système** | `.system()`, `.popen()`, `.spawn*()`, `.exec*()`, `.remove()`, `.unlink()`, `.rmdir()`, `.kill()` | **Rejet immédiat** : protection du système de fichiers et des processus hôtes. |
| **Syntaxe** | Fichier non compilable en Python 3 | Erreur avec indication précise de la ligne et de la colonne. |

### C. Validation du Contrat d'Interface (`BasePlugin`)
Tout plugin doit obligatoirement :
1. Déclarer une classe héritant de `BasePlugin` (`from base_plugin import BasePlugin`).
2. Implémenter la méthode `check_requirements(self, target_ip, target_services)`.
3. Implémenter la méthode `run_audit(self, target_ip, target_services, credentials=None)`.

### D. Confinement à l'Exécution (Crash Guard)
Dans `base_plugin.py`, la méthode `execute()` enveloppe chaque audit dans un bloc `try...except Exception` :
- Un plugin qui lève une exception (timeout réseau, socket fermé, etc.) **ne peut en aucun cas faire planter le daemon `rtms-scanner`**.
- L'erreur est capturée proprement et retournée avec le statut `"Error"`.

---

## 3. Guide de Développement d'un Plugin

### A. Squelette Minimal Conforme

```python
"""
mon_plugin.py - Template de base pour un plugin RTMS
"""
from base_plugin import BasePlugin

class MonPluginAudit(BasePlugin):
    def __init__(self):
        super().__init__()
        # Métadonnées obligatoires (auto-extraites lors de l'upload)
        self.info = {
            "name": "Nom Explicite du Plugin",
            "description": "Description concise de la vérification de sécurité effectuée.",
            "severity": "Medium",  # Valeurs autorisées : 'Info', 'Low', 'Medium', 'High', 'Critical'
            "cve": None,           # Ex: 'CVE-2024-XXXX' ou None
            "version": "1.0.0"
        }

    def check_requirements(self, target_ip, target_services):
        """
        Détermine si le plugin doit s'exécuter sur cet hôte.
        target_services est soit un dictionnaire {port: "nom_service"}, soit une liste de ports [80, 443].
        Retourne True pour lancer l'audit, False pour l'ignorer.
        """
        # Exemple : cibler uniquement les hôtes ayant le port 6379 ouvert
        if isinstance(target_services, dict):
            return 6379 in target_services or 'redis' in str(target_services).lower()
        return 6379 in target_services

    def run_audit(self, target_ip, target_services, credentials=None):
        """
        Exécute la logique de détection réseau (non destructive).
        Doit retourner self.format_result(status, proof, details).
        """
        # Statuts reconnus : "OK", "Vulnerable", "Warning", "Skipped", "Error"
        return self.format_result(
            status="OK",
            proof="Port 6379 vérifié avec succès",
            details="Authentification requise et active sur le service."
        )
```

---

### B. Exemple Réel en Production : Plugin Audit SSL/TLS (`ssl_tls_audit.py`)

Fichier complet déployé dans `rtms-scanner/external_plugins/ssl_tls_audit.py` :

```python
import socket
import ssl
from datetime import datetime, timezone
from base_plugin import BasePlugin

class SslTlsAuditPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.info = {
            "name": "SSL/TLS Security & Certificate Audit",
            "description": "Audits HTTPS and SSL services for certificate expiration, self-signed certificates, and deprecated protocols (TLS 1.0/1.1).",
            "severity": "Medium",
            "cve": None,
            "version": "1.0.0"
        }
        self.ssl_ports = [443, 8443, 9443, 4433, 10443]
        self.discovered_ssl_ports = []

    def check_requirements(self, target_ip, target_services):
        self.discovered_ssl_ports = []
        if isinstance(target_services, dict):
            for port, s_name in target_services.items():
                s_name_lower = str(s_name).lower()
                if port in self.ssl_ports or "ssl" in s_name_lower or "https" in s_name_lower:
                    self.discovered_ssl_ports.append(port)
        elif isinstance(target_services, (list, set)):
            for port in self.ssl_ports:
                if port in target_services:
                    self.discovered_ssl_ports.append(port)

        return len(self.discovered_ssl_ports) > 0

    def run_audit(self, target_ip, target_services, credentials=None):
        findings = []
        is_vulnerable = False

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        for port in self.discovered_ssl_ports:
            try:
                with socket.create_connection((target_ip, port), timeout=5.0) as sock:
                    with ctx.wrap_socket(sock, server_hostname=target_ip) as ssock:
                        tls_version = ssock.version()
                        cert = ssock.getpeercert()

                        # Détection protocoles dépréciés
                        if tls_version in ("TLSv1", "TLSv1.1", "SSLv2", "SSLv3"):
                            is_vulnerable = True
                            findings.append(f"Port {port}: Protocole déprécié '{tls_version}' accepté (infraction NIS 2).")

                        # Vérification de l'expiration
                        if cert and "notAfter" in cert:
                            expire_str = cert["notAfter"]
                            expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                            days_left = (expire_dt - datetime.now(timezone.utc)).days

                            if days_left < 0:
                                is_vulnerable = True
                                findings.append(f"Port {port}: Certificat SSL EXPIRÉ depuis {abs(days_left)} jours.")
                            elif days_left < 15:
                                findings.append(f"Port {port}: Certificat SSL expirant sous peu ({days_left} jours).")
                            else:
                                findings.append(f"Port {port}: Certificat valide ({tls_version}), expire dans {days_left} jours.")
                        else:
                            findings.append(f"Port {port}: Connecté en {tls_version} (certificat auto-signé).")
            except Exception as e:
                findings.append(f"Port {port}: Erreur TLS : {str(e)}")

        status = "Vulnerable" if is_vulnerable else "OK"
        return self.format_result(status, proof=f"Ports audités : {self.discovered_ssl_ports}", details=" ; ".join(findings))
```

---

## 4. Idées & Catalogue de Plugins Recommandés

| Nom du Plugin | Ports Cibles | Vulnérabilité / Risque Détecté | Sévérité | Statut / Type |
| :--- | :--- | :--- | :--- | :--- |
| **Audit Bases de données sans mot de passe** | 6379, 27017, 9200, 11211 | Redis, MongoDB, Elasticsearch, Memcached exposés sans authentification | **Critical** | **✅ INTERNE (`unauth_database.py`)** |
| **Audit Accès FTP Anonyme** | 21 | Serveurs FTP autorisant la connexion invité `anonymous` | **Medium** | **✅ INTERNE (`ftp_anonymous.py`)** |
| **Audit Certificats SSL/TLS** | 443, 8443, 9443 | Certificats expirés, TLS 1.0/1.1 obsolète, ciphers faibles | **Medium** | **✅ EXTERNE Exemple (`ssl_tls_audit.py`)** |
| **Audit SMB & Signature Message** | 445, 139 | SMBv1 actif (MS17-010 / EternalBlue / WannaCry), signature SMB non obligatoire (relais NTLM) | **Critical / High** | **✅ INTERNE (`smb_security.py`)** |
| **Durcissement Serveur SSH** | 22 | Échange KEX avec ciphers faibles (3DES, RC4, CBC), KEX SHA-1, bannières vulnérables (regreSSHion CVE-2024-6387, SSHv1) | **Critical / High / Medium** | **✅ INTERNE (`ssh_hardening.py`)** |
| **Identifiants par défaut (IoT / Réseau)** | 80, 443, 8080, 23 | Switches, caméras, imprimantes, routeurs configurés avec des identifiants d'usine (`admin:admin`, `admin:password`, etc.) | **High** | **✅ INTERNE (`default_credentials.py`)** |
| **Détection SNMP Community Strings** | 161 UDP | Community strings triviales par défaut (`public`, `private`, `community`, etc.) autorisant la lecture de topologie ou l'écriture MIB | **Critical / High** | **✅ INTERNE (`snmp_community.py`)** |

---

## 5. Déploiement, Traçabilité & Audit en Base de Données

### A. Emplacement des Fichiers (`RTMS_PLUGINS_DIR`)
Par défaut, les plugins externes sont stockés dans :
- **Mode Production** : `/opt/rtms/plugins/` (configuré via la variable d'environnement `RTMS_PLUGINS_DIR`).
- **Mode Développement** : `rtms-scanner/external_plugins/` ou `rtms-web/backend/data/plugins/`.

Le backend Web et le daemon Scanner partagent ce même répertoire pour une synchronisation instantanée.

### B. Indexation en Base de Données (`admin.external_plugins`)
Chaque plugin installé est persisté avec ses métadonnées :
```sql
CREATE TABLE IF NOT EXISTS admin.external_plugins (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,       -- 'python'
    file_size_bytes BIGINT DEFAULT 0,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    author VARCHAR(255) DEFAULT 'Custom',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### C. Journal d'Audit Immuable (`admin.system_audit`)
Toute action d'administration sur les plugins est consignée de manière inaltérable :

| Action | Déclencheur | Informations Tracées |
| :--- | :--- | :--- |
| **`EXTERNAL_PLUGIN_UPLOADED`** | Upload d'un script `.py` | Horodatage, utilisateur, IP source, nom du plugin, fichier, version, ID unique |
| **`EXTERNAL_PLUGIN_TOGGLED`** | Clic sur l'interrupteur Activer/Désactiver | Horodatage, utilisateur, IP source, ID du plugin, nouvel état (`enabled=true/false`) |
| **`EXTERNAL_PLUGIN_DELETED`** | Clic sur le bouton Supprimer | Horodatage, utilisateur, IP source, nom du plugin, fichier supprimé, version, ID |

### D. Consultation dans l'Interface Web
Dans le tableau de bord RTMS :
- **Configuration des plugins** : Menu **Paramètres ➔ Plugins**, permettant d'uploader, d'activer, de désactiver ou de supprimer un plugin externe.
- **Journal d'audit** : Menu **Audit ➔ Onglet "System Logs"**, affichant des badges visuels dédiés :
  - 🧩 **Plugin Uploaded** (badge vert émeraude)
  - 🗑️ **Plugin Deleted** (badge rouge)
  - 🔁 **Plugin Toggled** (badge bleu)

---

## 6. Tests & Validation Automatisée

Le framework dispose d'une suite de tests unitaires dédiée :
```bash
# Exécution des tests du validateur de plugins
cd rtms-commons
uv run python -m unittest tests/test_plugin_validator.py
```
Cette suite valide :
- L'acceptation d'un plugin valide avec extraction correcte des métadonnées.
- Le rejet des erreurs de syntaxe Python avec numéro de ligne.
- Le blocage des imports malveillants (`subprocess`, `shutil`, `ctypes`, etc.).
- Le blocage des appels système (`os.system`, `eval`, `exec`).
- Le rejet des fichiers ne respectant pas l'héritage de `BasePlugin` ou ses méthodes requises.
