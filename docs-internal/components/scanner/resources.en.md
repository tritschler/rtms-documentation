# HTTP Testing & Administrative Resources

## 1. Useful cURL Diagnostics

```bash
# Standard HTTP GET (fetches complete page content)
curl -L https://3tsconsulting.be

# Inspect response headers (checks HTTP 200 OK without downloading body)
curl -I -L https://3tsconsulting.be

# Verbose debug mode (TLS handshake, request/response headers)
curl -v -L https://3tsconsulting.be

# Test WordPress REST API reachability
curl -I -L https://3tsconsulting.be/wp-json/

# Retrieve raw REST API JSON payload
curl -L https://3tsconsulting.be/wp-json/
```

*Note: The `-L` flag ensures cURL follows redirects (HTTP to HTTPS, non-www to www).*

---

## 2. Direct URLs for WordPress Administration

Useful shortcuts bypassing third-party admin menu plugins:

### Priority & Recovery
* **Plugin Management:** `https://3ts-cybersecurity.be/wp-admin/plugins.php`
* **Core Updates:** `https://3ts-cybersecurity.be/wp-admin/update-core.php`

### Theme & Page Builders
* **Oshine Settings:** `https://3ts-cybersecurity.be/wp-admin/admin.php?page=oshine`
* **Theme Options:** `https://3ts-cybersecurity.be/wp-admin/admin.php?page=oshine_options`
* **Tatsu Dashboard:** `https://3ts-cybersecurity.be/wp-admin/admin.php?page=tatsu`

### General Settings
* **User Profile:** `https://3ts-cybersecurity.be/wp-admin/profile.php`
* **General Settings:** `https://3ts-cybersecurity.be/wp-admin/options-general.php`
* **Navigation Menus:** `https://3ts-cybersecurity.be/wp-admin/nav-menus.php`
* **Page Management:** `https://3ts-cybersecurity.be/wp-admin/edit.php?post_type=page`

### Security & Backup Extensions
* **Wordfence Security:** `https://3ts-cybersecurity.be/wp-admin/admin.php?page=Wordfence`
* **UpdraftPlus Backups:** `https://3ts-cybersecurity.be/wp-admin/options-general.php?page=updraftplus`
