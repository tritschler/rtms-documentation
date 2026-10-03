# Documentation du Cycle d'Exécution et Interactions de Base de Données de RTMS NVD

Ce document décrit de manière exhaustive la liste des actions effectuées par le moteur de synchronisation RTMS NVD, depuis son démarrage jusqu'à l'exécution complète de sa boucle de synchronisation, ainsi que ses interactions (lecture/écriture) avec les tables des schémas `nvd` et `admin`.

---

## 1. Liste des actions effectuées (Du démarrage à la première boucle complète)

Le processus de démarrage de `rtms-nvd` (via `main_rtms_nvd.py`) exécute séquentiellement les étapes suivantes :

1. **Initialisation et Configuration de Base**
   - Résolution du répertoire d'exécution et chargement du fichier de configuration (`rtms-nvd.properties`).
   - Surcharge éventuelle par les variables d'environnement (`RTMS_DB_HOST`, etc.).
   
2. **Validation de Licence**
   - Vérification cryptographique des droits d'exécution via le module `license_validator`. Le plan de licence ("PROD" ou "DEMO") est injecté en mémoire.

3. **Mise en place de la journalisation (Logging)**
   - Configuration du système de logs avec rotation (limite de Mo et nombre de backups).

4. **Vérification et Migration des Schémas de Base de Données (`check_and_bootstrap`)**
   - Initialisation des structures principales via `db.init_db()`.
   - Exécution de `verify_and_upgrade_schema` :
     - Application des DDLs unifiés.
     - Migration éventuelle d'anciennes tables NVD (ex: `nvd.alerts_config` vers `admin.cve_alerts_config`) et ajout de colonnes manquantes (CPEs).
   - Création de la table de cache `nvd.cve_cache`.

5. **Séquence d'Amorçage NVD (Bootstrap)**
   - Vérification de l'état de la table `nvd.cve`. Si elle n'existe pas ou est vide, un amorçage est déclenché.
   - **Tentative 1 (Locale)** : Importation en flux d'une archive compressée SQL (`rtms_nvd_vulnerabilities_data_sql.gz`) via la commande `COPY`.
   - **Tentative 2 (Distant)** : En cas d'échec de la méthode locale ou d'absence du fichier d'archive SQL, un `WARNING` est inséré dans les logs indiquant que l'archive n'a pas été trouvée, et le système bascule sur un téléchargement massif paginé depuis l'API REST de NIST.

6. **Chargement de la Configuration Dynamique (`get_dynamic_config`)**
   - Récupération des paramètres en base (fréquence de synchronisation, UUID, URL NVD). Auto-réparation si des valeurs sont absentes, avec écriture dans la base.

7. **Démarrage du Planificateur de Tâches (Scheduler)**
   - Programmation de la vérification de licence quotidienne.
   - Chargement des canaux d'alertes configurés (`db.load_alerts_configuration`).
   - Lancement de la première tâche de synchronisation incrémentale (`incremental_sync`).

8. **Exécution de la Synchronisation Incrémentale (`incremental_sync`)**
   - Calcul de la plage de temps nécessaire via la date de la dernière CVE modifiée.
   - Interrogation de l'API NIST pour rapatrier uniquement les nouvelles données ou celles mises à jour.
   - Mise à jour (Upsert) des CVEs et suppression/recréation des critères CPE associés.
   - Corrélation avec l'inventaire IT (`correlate_cpes`) pour identifier les actifs internes et logiciels de la Global Watchlist menacés.
   - Dispatch des alertes d'inventaire : Si de nouveaux assets sont menacés par des CVE critiques, des alertes sont émises sur les canaux webhooks après vérification anti-doublons.
   - **Enregistrement de la télémétrie d'audit (`nvd.sync_history`)** : Horodatage précis, durée d'exécution (`duration_ms`), compteurs de CVEs et CPEs ingérées, tableau des CVE IDs traités et résultat de corrélation inventaire.

9. **Boucle de Maintien en Condition Opérationnelle (Main Loop)**
   - Le programme entre dans une boucle infinie (`while True`), se mettant en pause pendant 60 secondes.
   - À chaque réveil, il effectue un *Hot Reload* : rechargement transparent de la configuration dynamique (intervalles, URL) et des canaux d'alertes sans redémarrage, ajustant le planificateur si l'intervalle a été modifié.

---

## 2. Informations reprises (Retrieved) et stockées (Stored) par Table

### Schéma `nvd`

| Table | Information Reprise (Retrieve) | Information Stockée (Store) |
| :--- | :--- | :--- |
| **`nvd.cve`** | - Vérification de son existence et comptage (`COUNT`) au démarrage pour déclencher ou non l'amorçage.<br>- Récupération de `MAX(last_modified_date)` pour déterminer le point de départ de la synchronisation incrémentale à chaque boucle. | - Insertion ou mise à jour (Upsert) des métadonnées de base d'une vulnérabilité : `cve_id`, `description`, `cvss_v3_score`, `cvss_v3_severity`, `published_date`, `last_modified_date`. |
| **`nvd.cpe_match`** | - Utilisée indirectement par la vue `admin.vulnerability_view` lors du processus de corrélation (`correlate_cpes`) pour identifier si des équipements/logiciels correspondent aux critères d'une CVE. | - Stockage des critères CPE (produits et versions) : `cve_id`, `vulnerable`, `criteria`, `version_start_including/excluding`, `version_end_including/excluding`.<br>- *Note:* Lors d'une mise à jour de CVE, toutes les anciennes lignes CPE associées sont supprimées (`DELETE`) avant réinsertion. |
| **`nvd.cve_cache`** | - N/A (Non lue directement par la boucle `rtms-nvd`, réservée pour d'autres usages ou micro-services de l'écosystème). | - Création structurelle de la table et de son index si elle n'existe pas via `db.create_cve_cache_table()`. |
| **`nvd.sync_history`** | - Consultée par le backend web (`/api/nvd/sync-history`) pour afficher les métriques et auditer l'activité de synchronisation dans l'interface UI (modal d'inspection et badges télémétriques). | - Écriture systématique à la fin de chaque cycle de synchronisation incrémentale : `tenant_id`, `sync_start`, `sync_end`, `duration_ms`, `cve_count`, `cpe_count`, `status`, `cve_ids`, `impacted_inventory_count`. En cas d'échec, enregistrement d'un statut `FAILED` et de l'`error_message`. |

### Schéma `admin`

| Table | Information Reprise (Retrieve) | Information Stockée (Store) |
| :--- | :--- | :--- |
| **`admin.tenant_infra`** | - Lecture de la clé d'API NIST (`nist_api_key`) spécifique au tenant lors des requêtes vers NIST. | - Création du tenant par défaut (`3TS`) ou insertion de tenants récupérés depuis les anciennes configurations lors de la migration. |
| **`admin.nvd_config`** | - Lecture à chaque boucle (hot-reload) des paramètres dynamiques **spécifiques au tenant_id** (`WHERE tenant_id = %s`) : `nist.cve.enabled`, `nvd.uuid`, `nvd.fetch.minutes`, `nvd.api.url`.<br>- Lecture de la colonne **`is_mandatory`** (booléen) pour vérifier si le paramètre est strictement obligatoire ; si tel est le cas et que la valeur manque, le moteur force l'arrêt. | - "Auto-guérison" : Si les clés manquent pour ce tenant, le moteur écrit automatiquement les valeurs par défaut depuis les propriétés dans la base de données. Ajout structurel des colonnes `tenant_id` et `is_mandatory` (par défaut `FALSE`) lors de l'initialisation. |
| **`admin.cve_alerts_config`** | - Lecture de l'ensemble des webhooks ou alertes actives du tenant, avec la destination (`destination_url`) et le seuil critique (`trigger_threshold`). Rechargé toutes les minutes. | - Alimentée automatiquement lors de la migration, en importent les données de la table obsolète `nvd.alerts_config`. |
| **`admin.cve_alerts`** | - Lecture servant de "dédoublonneur" : vérifie si un `channel_config_id` donné a déjà été notifié pour une `cve_id` précise. | - Stockage d'une trace d'audit pour chaque alerte émise : `cve_id`, `channel_config_id`, `cve_score`, `trigger_threshold` et `sent_at`. Cela évite le spam sur les réseaux internes. |
| **`admin.tenant_logs`** | - N/A | - En cas de configuration `nvd_config` introuvable ou totalement corrompue, un log d'alerte métier (niveau WARNING) est écrit dans cette table pour affichage dans l'interface UI de l'administrateur. |
| **`admin.product_license`** | - Validation régulière de la cryptographie de la licence active (`raw_payload`, `cryptographic_signature`, date d'expiration). | - Insertion initiale ou mise à jour des paramètres de la licence. |
| **`admin.assets`** | - Indirectement relue (via les vues associées) pour croiser le parc inventorié avec les vulnérabilités NVD. | - Modification structurelle au démarrage : ajout de colonnes d'empreintes OS/CPE (ex: `os_cpe`, `os_flavor`, `os_version`) si absentes de la base de données lors de la vérification de schéma. |
| **`admin.asset_vulnerabilities`** | - N/A | - Lors de la fonction `correlate_cpes()`, si un équipement local correspond aux critères NVD, un enregistrement l'associant à la CVE est inséré (`tenant_id`, `asset_id`, `software_id`, `cve_id`). |

> [!NOTE]
> Les tables de l'inventaire (`admin.tenant_assets`, `admin.tenant_asset_software`) sont requêtées à l'aide de vues complexes (telles que `admin.vulnerability_view`) afin d'établir un lien mathématique exact (CPE Matching) avec les tables NVD nouvellement peuplées lors de l'exécution de la méthode `correlate_cpes`.

---

## 3. Sécurité et Durcissement PostgreSQL (Principe du Moindre Privilège)

### Justification de l'Accès Direct à la Base de Données
Contrairement aux sondes distantes `rtms-scanner` qui sont découplées et dialoguent exclusivement via l'API REST HTTPS, le microservice `rtms-nvd` conserve une connexion SQL directe vers PostgreSQL. Ce choix d'ingénierie repose sur des impératifs stricts de volumétrie et de performance :
1. **Volumétrie Massive** : La base NVD comporte plus de **250 000 vulnérabilités CVE** et plusieurs millions de critères CPE.
2. **Streaming Haute Performance (Bulk COPY)** : L'amorçage initial injecte des archives compressées en flux continu (`COPY`) directement dans le moteur relationnel.
3. **Corrélation Relationnelle Complexe (CPE Matching)** : Le croisement entre les critères CPE et les logiciels inventoriés sollicite les index GiST/GIN et les jointures SQL natives. Faire transiter ces données par des API REST intermédiaires introduirait une surcharge mémoire et une latence réseau inacceptables.

### Script de Durcissement : `harden_nvd_user.sql`
Afin d'appliquer le principe de moindre privilège (*Least Privilege*) et d'empêcher tout risque de compromission latérale, `rtms-nvd` utilise un utilisateur de base de données dédié : **`rtms_nvd_user`**.

Le script `harden_nvd_user.sql` applique les règles de sécurité suivantes :

```sql
-- 1. Droits complets UNIQUEMENT sur le schéma nvd
GRANT USAGE ON SCHEMA nvd TO rtms_nvd_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nvd TO rtms_nvd_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA nvd TO rtms_nvd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_nvd_user;

-- 2. Confinement du Search Path
ALTER ROLE rtms_nvd_user SET search_path TO nvd;

-- 3. Révocation STRICTE sur les schémas sensibles
REVOKE ALL ON SCHEMA admin FROM rtms_nvd_user;
REVOKE ALL ON SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON SCHEMA public FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA admin FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM rtms_nvd_user;
```

Grâce à ce durcissement :
- `rtms_nvd_user` ne peut ni lire ni modifier les tables sensibles d'authentification (`admin.users`, hashs bcrypt, secrets MFA), ni la topologie des scans (`scanner.*`).
- Même en cas de vulnérabilité applicative dans le traitement des flux NIST, la surface d'attaque reste strictement cantonnée aux tables publiques de vulnérabilités CVE du schéma `nvd`.

