# Export Procedure for CVE & CPE Match Tables

To generate the `rtms_nvd_vulnerabilities_data_sql.gz` seed archive required for rapid initial bootstrapping, **both `nvd.cve` and `nvd.cpe_match` must be exported together**.

---

## Why Both Tables?
The fast bootstrap import engine parses this compressed archive expecting native PostgreSQL `COPY` statements for both entities. The import runs in two sequential passes: parent records (`nvd.cve`) first, followed by child records (`nvd.cpe_match`), preserving relational foreign key integrity.

---

## Export Command

Execute the following `pg_dump` command:

```bash
pg_dump -U <db_user> -h <db_host> -d <db_name> -t nvd.cve -t nvd.cpe_match -a | gzip > rtms_nvd_vulnerabilities_data_sql.gz
```

### Important Notes:
- The `-a` (or `--data-only`) flag exports table rows exclusively without DDL, as schemas are managed independently by the application.
- The output archive must strictly be named **`rtms_nvd_vulnerabilities_data_sql.gz`** (including the `_sql` suffix) for auto-detection during daemon startup.
