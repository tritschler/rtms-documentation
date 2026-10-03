# Modèle de Données RTMS-NVD

Ce document décrit les tables de la base de données utilisées par le service `rtms-nvd` pour stocker, synchroniser et gérer les données de vulnérabilité (CVE) en provenance du NVD (National Vulnerability Database).

## Schéma `nvd`

Ce schéma contient les données de sécurité et de vulnérabilités brutes.

### 1. `nvd.cve`
Table principale stockant les détails essentiels d'une vulnérabilité (Common Vulnerabilities and Exposures).
- **`cve_id`** (`VARCHAR(50)`, Clé Primaire) : L'identifiant unique de la CVE (ex: CVE-2021-44228).
- **`description`** (`TEXT`) : Description détaillée de la vulnérabilité.
- **`cvss_v3_score`** (`NUMERIC`) : Le score de base CVSS v3.
- **`cvss_v3_severity`** (`VARCHAR(50)`) : Le niveau de sévérité CVSS v3 (ex: LOW, MEDIUM, HIGH, CRITICAL).
- **`published_date`** (`TIMESTAMP WITH TIME ZONE`) : Date de publication initiale de la CVE.
- **`last_modified_date`** (`TIMESTAMP WITH TIME ZONE`) : Date de dernière modification de la CVE.

### 2. `nvd.cpe_match`
Stocke les critères CPE (Common Platform Enumeration) associés à une CVE, permettant d'identifier quelles versions de logiciels (produits et fournisseurs) sont vulnérables.
- **`id`** (`SERIAL`, Clé Primaire) : Identifiant unique du critère de correspondance.
- **`cve_id`** (`VARCHAR(50)`, Clé Étrangère vers `nvd.cve`) : L'identifiant de la CVE associée.
- **`vulnerable`** (`BOOLEAN`) : Indique si ce critère CPE correspond à une configuration vulnérable (`true`) ou non.
- **`criteria`** (`TEXT`) : La chaîne CPE complète ou partielle (ex: `cpe:2.3:a:apache:log4j:...`).
- **`version_start_including`** (`VARCHAR(100)`) : Borne de version minimale (incluse).
- **`version_start_excluding`** (`VARCHAR(100)`) : Borne de version minimale (exclue).
- **`version_end_including`** (`VARCHAR(100)`) : Borne de version maximale (incluse).
- **`version_end_excluding`** (`VARCHAR(100)`) : Borne de version maximale (exclue).

### 3. `nvd.cve_cache`
Table de cache optimisant les requêtes et l'accès aux données CVE, utilisée pour des processus de synchronisation.
- **`cpe_prefix`** (`VARCHAR(255)`, Clé Primaire) : Préfixe CPE mis en cache.
- **`cve_data`** (`JSONB`) : Les données JSON des CVEs correspondantes.
- **`last_sync`** (`TIMESTAMP WITH TIME ZONE`) : Date de la dernière synchronisation pour ce préfixe.
- **`last_modified_cve`** (`TIMESTAMP WITH TIME ZONE`) : Date de dernière modification de la CVE dans le cache.

### 4. `nvd.sync_history`
Historique d'audit et télémétrie opérationnelle de chaque cycle de synchronisation du flux NVD NIST.
- **`id`** (`SERIAL`, Clé Primaire) : Identifiant unique de l'exécution.
- **`tenant_id`** (`VARCHAR(50)`) : Identifiant du tenant (par défaut `3TS`).
- **`sync_start`** (`TIMESTAMP WITH TIME ZONE`) : Horodatage du début du cycle de synchronisation.
- **`sync_end`** (`TIMESTAMP WITH TIME ZONE`) : Horodatage de fin du cycle.
- **`duration_ms`** (`INTEGER`) : Durée d'exécution du cycle en millisecondes.
- **`cve_count`** (`INTEGER`) : Nombre de CVEs insérées ou mises à jour lors de ce cycle.
- **`cpe_count`** (`INTEGER`) : Nombre d'enregistrements CPE correspondants traités.
- **`status`** (`VARCHAR(20)`) : Statut d'exécution (`RUNNING`, `SUCCESS`, `FAILED`).
- **`error_message`** (`TEXT`) : Message d'erreur détaillé en cas d'échec d'ingestion.
- **`cve_ids`** (`TEXT[]`) : Tableau des identifiants CVE téléchargés lors du cycle (jusqu'à 1 000 identifiants pour inspection unitaire).
- **`impacted_inventory_count`** (`INTEGER`) : Nombre de vulnérabilités corrélées avec l'inventaire actif ou la Global Watchlist.
- *Index* : `idx_sync_history_start ON nvd.sync_history (sync_start DESC)`

---

## Schéma `admin`

Ce schéma contient la configuration et l'audit du processus de synchronisation NVD.

### 4. `admin.nvd_config`
Stocke la configuration opérationnelle dynamique pour la synchronisation NVD (fréquences, restrictions d'import, clés, etc.).
- **`tenant_id`** (`VARCHAR(50)`) : Identifiant du tenant (généralement `SYSTEM` pour les processus globaux).
- **`config_key`** (`VARCHAR(50)`) : Nom de la propriété de configuration (ex: `NVD_SYNC_INTERVAL_MINUTES`).
- **`config_value`** (`VARCHAR(255)`) : Valeur de la propriété.
- *Clé Primaire* : `(tenant_id, config_key)`

### 5. `admin.tenant_logs`
Système de journalisation en base de données permettant de tracer l'exécution des jobs de synchronisation NVD (démarrages, succès, erreurs).
- **`id`** (`SERIAL`, Clé Primaire) : Identifiant unique du log.
- **`tenant_id`** (`VARCHAR(50)`) : Identifiant du tenant concerné (ou `SYSTEM`).
- **`log_level`** (`VARCHAR`) : Sévérité du log (`INFO`, `ERROR`, etc.).
- **`message`** (`TEXT`) : Le contenu détaillé du log ou la trace d'erreur.
- **`created_at`** (`TIMESTAMP WITH TIME ZONE`) : Horodatage du log.

### 6. `admin.cve_alerts_config`
Le service NVD observe cette table pour recharger à chaud (hot-reload) la configuration des canaux d'alertes en cas d'identification de nouvelles CVEs nécessitant la génération d'alertes temps réel.
- **`id`** (`SERIAL`, Clé Primaire) : Identifiant de la configuration d'alerte.
- **`tenant_id`** (`VARCHAR(50)`, Clé Étrangère) : Identifiant du tenant.
- **`channel_type`** (`VARCHAR(20)`) : Type de canal (ex: `webhook`, `email`).
- **`channel_name`** (`VARCHAR(100)`) : Nom usuel du canal d'alerte.
- **`destination_url`** (`TEXT`) : L'URL du webhook de destination ou autre.
- **`trigger_threshold`** (`NUMERIC`) : Le score de criticité minimal requis pour déclencher l'alerte.
- **`is_active`** (`BOOLEAN`) : Statut d'activation de la règle d'alerte.
- **`created_at`** (`TIMESTAMP WITH TIME ZONE`) : Date de création de la règle.
