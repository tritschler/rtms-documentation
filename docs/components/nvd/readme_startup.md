# Séquence de Démarrage de RTMS-NVD

Ce document décrit en détail le processus d'initialisation et de démarrage du composant `rtms-nvd`, point d'entrée principal (`main_rtms_nvd.py`).

## 1. Chargement de la Configuration et Validation
Au lancement, le programme tente de lire le fichier de configuration `rtms-nvd.properties` situé à la racine.

- **Fichier manquant & Fallback ENV :** Si le fichier est absent, le système initialise un dictionnaire vide et s'appuie sur les variables d'environnement (`RTMS_DB_HOST`, `RTMS_DB_PORT`, `RTMS_DB_USER`, `RTMS_DB_NAME`). Si une de ces 4 variables manque, le démarrage s'arrête (`sys.exit(1)`).
- **Validation (Liste Blanche) :** Une fois la configuration chargée, le programme vérifie les clés présentes contre une liste blanche stricte (`VALID_PROPERTIES`). Toute clé inconnue (ex: erreur de frappe ou injection) génère un `WARNING` dans les logs et sera ignorée pour protéger la base de données.
- **Override par Variables d'Environnement :** Même si le fichier `.properties` est présent, les variables d'environnement `RTMS_DB_*` sont lues. Si elles existent, elles écrasent (*override*) les valeurs du fichier avec un avertissement (priorité au Cloud-Native / Docker).

## 2. Validation de la Licence
Avant d'autoriser l'accès à la base de données, l'application appelle `license_validator.enforce_license_state`.
Cette fonction vérifie en priorité le fichier `license.key` local. En cas d'absence ou d'échec de lecture, elle tente de récupérer la dernière licence valide synchronisée en base de données (`admin.product_license`).
Elle valide ensuite la signature cryptographique (RSA), vérifie l'expiration et compare les empreintes matérielles (DMI/Hardware footprint).
Si aucune licence n'est trouvée (ni en fichier, ni en base), ou en cas de licence invalide/expirée, l'application bascule automatiquement en **mode DEMO** au lieu de s'arrêter brusquement. Ce mode applique des restrictions sévères sur les capacités du système (par exemple, un maximum de 5 hôtes traités).

## 3. Configuration des Logs et Contexte d'Exécution
- Le système de logs est initialisé avec la rotation configurée (`log.max_mb` et `log.backups`).
- Le mode d'exécution est déterminé : `saas` (exécution centralisée VPS) ou `onprem` (exécution locale chez le client). Le `tenant_context` est ajusté en conséquence. Si la licence détecte le mode `DEMO`, des avertissements de restrictions sont émis.

## 4. Initialisation de la Base de Données
Le programme appelle `db.init_db` pour s'assurer que les schémas SQL (`nvd`, `admin`, `scanner`) existent.
Il effectue ensuite une vérification des migrations via `nvd_db_upgrades.verify_and_upgrade_schema` pour créer ou mettre à jour les tables (ex: ajout de colonnes manquantes dans `admin.assets`).
Si ces vérifications échouent (ex: base inaccessible, erreur de syntaxe SQL), le programme s'arrête.

## 5. Bootstrap de la Base de Vulnérabilités (NVD)
L'application cherche d'abord le fichier `rtms_nvd_vulnerabilities_data_sql.gz` en local pour effectuer une importation rapide (initiale ou incrémentale).
- **Import du Snapshot Local :** S'il est présent, elle utilise une stratégie d'importation incrémentale (Staging & Upsert) via des tables temporaires. La commande native `COPY` de PostgreSQL injecte les données dans une zone de transit en mémoire (`temp_cve`, `temp_cpe_match`), puis un `INSERT ... ON CONFLICT DO NOTHING` fusionne silencieusement les nouvelles données avec celles déjà présentes dans la base.
  - À la fin du succès de l'import, le fichier est renommé avec l'extension `.processed` pour éviter d'être réimporté au redémarrage suivant.
- **Mode API (Fallback) :** Ensuite, une vérification de l'état réel de la base de données est effectuée. L'application compte les lignes de `nvd.cve`. Si la table contient **0 ligne** (parce qu'aucun fichier n'était présent), un bootstrap complet via l'API REST NVD est déclenché de manière asynchrone (avec gestion des quotas et du backoff). Dès que la table contient des données, l'application passe en mode synchronisation incrémentale classique.

## 6. Configuration Dynamique (Seed-and-Override / Auto-Healing)
Le programme charge sa configuration opérationnelle (fréquences de requêtes, URL API, etc.) depuis la table `admin.nvd_config` via la fonction `get_dynamic_config`.
- **Auto-Healing :** Si certains paramètres (ex: `nvd.fetch.minutes`) manquent dans la base, le programme les crée (`INSERT`) en base en utilisant les valeurs par défaut issues du fichier `rtms-nvd.properties`.
- **Override :** Les valeurs lues en base de données écrasent ensuite les valeurs statiques en mémoire (`config_db.update(dynamic_config)`). Cela permet aux administrateurs de modifier le comportement du moteur depuis l'interface web (donc via modification SQL) sans jamais avoir à redémarrer le service backend.

## 7. Planification des Tâches (Scheduler)
Le programme utilise `BackgroundScheduler` pour instancier ses boucles d'exécution asynchrones :
1. **Vérification de licence :** Tâche quotidienne vérifiant que la licence reste valide.
2. **Rechargement des configurations :** Tâche vérifiant l'apparition de nouveaux canaux d'alertes dans `admin.cve_alerts_config` et le changement des paramètres dynamiques de scan.
3. **Synchronisation NVD :** Tâche principale exécutant `incremental_sync` à la fréquence demandée (`nvd.fetch.minutes`). À chaque fin de cycle de synchronisation incrémentale, l'application exécute la **corrélation d'inventaire** (`correlate_cpes`) puis distribue les alertes ciblées (`dispatch_inventory_alerts`) sur l'infrastructure physique du client.

Le fil d'exécution principal entre ensuite dans une boucle infinie (`while True: time.sleep(1)`) pour maintenir le scheduler en vie.
