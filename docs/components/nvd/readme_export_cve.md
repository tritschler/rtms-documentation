# Procédure d'exportation des données CVE et CPE Match

Pour créer le fichier d'archive `rtms_nvd_vulnerabilities_data_sql.gz` requis par l'application pour l'importation initiale (bootstrap), il est **indispensable d'exporter les deux tables : `nvd.cve` et `nvd.cpe_match`**.

## Pourquoi les deux tables ?
Le script d'importation de l'application lit cette archive compressée et s'attend à y trouver les instructions `COPY` pour ces deux tables. L'importation s'effectue en deux passes séquentielles : la table parente (`nvd.cve`) est traitée en premier, suivie de la table enfant (`nvd.cpe_match`). Cela permet de garantir l'intégrité référentielle (les clés étrangères) de manière native au sein de la base de données.

## Commande d'exportation
Pour générer correctement le fichier avec les deux tables (en utilisant les instructions `COPY` par défaut), utilisez la commande `pg_dump` suivante :

```bash
pg_dump -U <votre_utilisateur> -h <votre_hote> -d <votre_base_de_donnees> -t nvd.cve -t nvd.cpe_match -a | gzip > rtms_nvd_vulnerabilities_data_sql.gz
```

### Notes importantes :
- L'option `-a` (ou `--data-only`) est utilisée pour n'exporter que les données. La structure des tables est gérée et initialisée séparément par l'application.
- Le fichier généré doit impérativement s'appeler **`rtms_nvd_vulnerabilities_data_sql.gz`** (avec le suffixe `_sql`) pour être détecté automatiquement par le système lors du démarrage.
