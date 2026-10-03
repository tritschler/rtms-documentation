# Guide d'Installation et de Durcissement PostgreSQL (VPS / Production)

Ce guide fournit une procédure pas-à-pas complète pour déployer, configurer et sécuriser l'infrastructure de base de données PostgreSQL de la plateforme RTMS sur un serveur VPS Linux (Ubuntu / Debian).

Ce déploiement met en œuvre une architecture **PoLP (*Principle of Least Privilege*)** stricte conforme aux exigences **NIS 2** et **ISO 27001**.

---

## 1. Prérequis Système

* **Système d'exploitation** : Ubuntu 22.04 LTS / 24.04 LTS ou Debian 12
* **Version PostgreSQL** : Version 16 ou supérieure
* **Extensions requises** : `uuid-ossp`, `pg_trgm`
* **Accès** : Privilèges `sudo` / `root`

---

## 2. Étape 1 : Installation de PostgreSQL

Sur le VPS, mettez à jour les dépôts et installez PostgreSQL ainsi que les extensions de contribution :

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib
```

Vérifiez que le service PostgreSQL est actif et s'exécute correctement :

```bash
sudo systemctl enable --now postgresql
sudo systemctl status postgresql --no-pager
```

---

## 3. Étape 2 : Initialisation de la Base et des Schémas

Connectez-vous en tant qu'utilisateur système `postgres` et créez la base `rtms_db` ainsi que l'utilisateur propriétaire maître (`rtms_user`) :

```bash
# Définir un mot de passe fort pour l'utilisateur propriétaire
RTMS_DB_PASS="VOTRE_MOT_DE_PASSE_TRES_FORT_POUR_RTMS_USER"

sudo -u postgres psql <<EOF
-- Création du propriétaire maître
CREATE USER rtms_user WITH PASSWORD '$RTMS_DB_PASS';

-- Création de la base de données
CREATE DATABASE rtms_db OWNER rtms_user;
EOF
```

Activez les extensions requises et créez les 3 schémas étanches :

```bash
sudo -u postgres psql -d rtms_db <<EOF
-- Extension UUID pour les identifiants uniques
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;

-- Extension pg_trgm pour la recherche plein texte et similitude trigramme
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA public;

-- Création des 3 schémas métier appartenant à rtms_user
CREATE SCHEMA IF NOT EXISTS admin AUTHORIZATION rtms_user;
CREATE SCHEMA IF NOT EXISTS nvd AUTHORIZATION rtms_user;
CREATE SCHEMA IF NOT EXISTS scanner AUTHORIZATION rtms_user;
EOF
```

---

## 4. Étape 3 : Application du Durcissement RBAC (Moindre Privilège)

Pour éviter qu'un composant compromis ne donne accès à toute la base de données, nous créons 3 comptes de service dédiés avec des droits cloisonnés :

1. **`rtms_nvd_user`** : Synchroniseur NVD (Lecture/Écriture sur `nvd`, configuration et heartbeat sur `admin`, **zéro accès** à `scanner`).
2. **`rtms_scanner_user`** : Moteur de scan (Lecture/Écriture sur `scanner`, injection d'actifs sur `admin`, **zéro accès** à `nvd`).
3. **`rtms_web_user`** : Backend Web / Dashboard (Lecture/Écriture sur `admin` et `scanner`, **lecture seule stricte** sur `nvd`).

### Exécution du script de sécurisation :

Définissez les mots de passe pour chaque service et exécutez le script SQL :

```bash
NVD_PASS="MOT_DE_PASSE_SECURISE_NVD"
SCANNER_PASS="MOT_DE_PASSE_SECURISE_SCANNER"
WEB_PASS="MOT_DE_PASSE_SECURISE_WEB"

sudo -u postgres psql -d rtms_db <<EOF
-- 1. Création des rôles
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rtms_nvd_user') THEN
        CREATE ROLE rtms_nvd_user WITH LOGIN PASSWORD '$NVD_PASS';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rtms_scanner_user') THEN
        CREATE ROLE rtms_scanner_user WITH LOGIN PASSWORD '$SCANNER_PASS';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rtms_web_user') THEN
        CREATE ROLE rtms_web_user WITH LOGIN PASSWORD '$WEB_PASS';
    END IF;
END
\$\$;

-- 2. Connexion et search_paths
GRANT CONNECT ON DATABASE rtms_db TO rtms_nvd_user, rtms_scanner_user, rtms_web_user;

ALTER ROLE rtms_nvd_user SET search_path TO nvd, admin, public;
ALTER ROLE rtms_scanner_user SET search_path TO scanner, admin, public;
ALTER ROLE rtms_web_user SET search_path TO admin, scanner, nvd, public;

-- Sécurisation du schéma public par défaut
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM rtms_nvd_user, rtms_scanner_user, rtms_web_user;

-- 3. Droits RTMS-NVD (nvd_user)
REVOKE ALL ON SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA scanner FROM rtms_nvd_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA scanner FROM rtms_nvd_user;

GRANT USAGE ON SCHEMA nvd TO rtms_nvd_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nvd TO rtms_nvd_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA nvd TO rtms_nvd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_nvd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rtms_nvd_user;

GRANT USAGE ON SCHEMA admin TO rtms_nvd_user;
REVOKE ALL ON ALL TABLES IN SCHEMA admin FROM rtms_nvd_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA admin FROM rtms_nvd_user;

-- 4. Droits RTMS-SCANNER (scanner_user)
REVOKE ALL ON SCHEMA nvd FROM rtms_scanner_user;
REVOKE ALL ON ALL TABLES IN SCHEMA nvd FROM rtms_scanner_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA nvd FROM rtms_scanner_user;

GRANT USAGE ON SCHEMA scanner TO rtms_scanner_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA scanner TO rtms_scanner_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA scanner TO rtms_scanner_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA scanner GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_scanner_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA scanner GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rtms_scanner_user;

GRANT USAGE ON SCHEMA admin TO rtms_scanner_user;
REVOKE ALL ON ALL TABLES IN SCHEMA admin FROM rtms_scanner_user;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA admin FROM rtms_scanner_user;

-- 5. Droits RTMS-WEB (web_user)
GRANT USAGE ON SCHEMA admin, scanner, nvd TO rtms_web_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA admin TO rtms_web_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA scanner TO rtms_web_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA admin TO rtms_web_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA scanner TO rtms_web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA admin GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA scanner GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rtms_web_user;

-- NVD en LECTURE SEULE pour le web
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA nvd FROM rtms_web_user;
GRANT SELECT ON ALL TABLES IN SCHEMA nvd TO rtms_web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nvd GRANT SELECT ON TABLES TO rtms_web_user;
EOF
```

> **Astuce :** Vous pouvez également appliquer ou réappliquer ces privilèges à tout moment via l'utilitaire de l'installeur :
> ```bash
> python database/manage_schemas.py setup-rbac
> ```

---

## 5. Étape 4 : Durcissement du Serveur PostgreSQL au niveau Système

### A. Restriction de l'écoute réseau (`postgresql.conf`)

Par défaut sur un VPS hébergeant l'application en local ou via tunnel VPN WireGuard, PostgreSQL ne doit **jamais** écouter sur `0.0.0.0` sans restriction.

Éditez le fichier de configuration principal (ex: `/etc/postgresql/16/main/postgresql.conf`) :

```ini
# Écouter uniquement en local (si tous les services RTMS sont sur le même VPS)
listen_addresses = 'localhost'

# Paramètres de performance et de sécurité recommandés
password_encryption = scram-sha-256
ssl = on
log_connections = on
log_disconnections = on
log_line_prefix = '%m [%p] %q%u@%d '
```

### B. Contrôle d'authentification (`pg_hba.conf`)

Éditez `/etc/postgresql/16/main/pg_hba.conf` pour exiger l'authentification sécurisée `scram-sha-256` :

```text
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     scram-sha-256
host    rtms_db         rtms_web_user   127.0.0.1/32            scram-sha-256
host    rtms_db         rtms_nvd_user   127.0.0.1/32            scram-sha-256
host    rtms_db         rtms_scanner_user 127.0.0.1/32          scram-sha-256
host    rtms_db         rtms_user       127.0.0.1/32            scram-sha-256
```

Rechargez ensuite la configuration :

```bash
sudo systemctl restart postgresql
```

---

## 6. Étape 5 : Configuration des Services RTMS

Dans le répertoire `/opt/rtms/config/` :

### 1. Backend Web (`.env`)
```ini
DATABASE_URL=postgresql+psycopg://rtms_web_user:VOTRE_MOT_DE_PASSE@localhost:5432/rtms_db
RTMS_DB_HOST=localhost
RTMS_DB_PORT=5432
RTMS_DB_NAME=rtms_db
RTMS_DB_USER=rtms_web_user
RTMS_POSTGRES_PASSWORD=VOTRE_MOT_DE_PASSE
```

### 2. Service NVD (`scanner.properties` ou environnement système)
```ini
db.host=localhost
db.port=5432
db.name=rtms_db
db.user=rtms_nvd_user
db.password=VOTRE_MOT_DE_PASSE
```

### 3. Service Scanner
* **Mode REST API (recommandé en production)** : Le scanner communique via HTTPS avec le backend via `RTMS_SERVER_URL` et `RTMS_SCANNER_TOKEN`.
* **Mode Connexion Directe DB (si activé)** : Utilise `db.user=rtms_scanner_user`.

---

## 7. Étape 6 : Tests de Validation de la Sécurité

Pour vérifier que le cloisonnement est opérationnel sur votre VPS, exécutez ces tests de vérification :

### Test 1 : Vérifier que `rtms-scanner` ne peut pas accéder à `nvd`
```bash
PGPASSWORD="$SCANNER_PASS" psql -h localhost -U rtms_scanner_user -d rtms_db -c "SELECT COUNT(*) FROM nvd.cve;"
```
> **Résultat attendu :** `ERROR: permission denied for schema nvd` ✅

### Test 2 : Vérifier que `rtms-web` ne peut pas modifier la base NVD (Lecture Seule)
```bash
PGPASSWORD="$WEB_PASS" psql -h localhost -U rtms_web_user -d rtms_db -c "DELETE FROM nvd.cve;"
```
> **Résultat attendu :** `ERROR: permission denied for table cve` ✅

### Test 3 : Vérifier que `rtms-nvd` ne peut pas accéder aux utilisateurs administrateurs
```bash
PGPASSWORD="$NVD_PASS" psql -h localhost -U rtms_nvd_user -d rtms_db -c "SELECT * FROM admin.users;"
```
> **Résultat attendu :** `ERROR: permission denied for table users` ✅

### Test 4 : Vérifier que `rtms-web` peut lire les CVEs
```bash
PGPASSWORD="$WEB_PASS" psql -h localhost -U rtms_web_user -d rtms_db -c "SELECT COUNT(*) FROM nvd.cve;"
```
> **Résultat attendu :** Succès (renvoie le nombre d'enregistrements) ✅

---

## 8. Sauvegarde et Restauration

Grâce au découpage des schémas, les sauvegardes peuvent être effectuées de manière modulaire :

```bash
# Sauvegarde des données applicatives et des scans (légère)
pg_dump -U rtms_user -d rtms_db -n admin -n scanner -F c -b -v -f rtms_app_backup.dump

# Sauvegarde du référentiel NVD (plus volumineuse, ~1.5 Go)
pg_dump -U rtms_user -d rtms_db -n nvd -F c -b -v -f rtms_nvd_backup.dump
```
