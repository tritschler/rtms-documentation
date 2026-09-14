# RTMS Web - Guide des Environnements Frontend & NGINX

Ce document détaille les différentes manières d'exécuter et de tester le frontend RTMS Web :
1. **Mode Développement (React + Vite)** : pour le développement quotidien avec rechargement à chaud (HMR).
2. **Mode Test NGINX avec Docker (macOS)** : pour prévisualiser le comportement de production sans installer Nginx sur l'hôte.
3. **Mode NGINX Natif sans Docker (macOS via Homebrew)** : pour exécuter Nginx directement en local.
4. **Mode Déploiement Production (Linux / VPS OVH / On-Premise)** : pour l'hébergement serveur avec reverse proxy et SSL.

---

## 1. Vue d'Ensemble de l'Architecture

```
                                 ┌─────────────────────────────────────────────────────────┐
                                 │                 FASTAPI BACKEND (8000)                  │
                                 │  - Mode Dev : `uv run uvicorn main:app --reload`        │
                                 │  - Mode Prod : binaire autonome `./rtms-backend`        │
                                 └─────────────▲─────────────────────────────▲─────────────┘
                                               │ proxy /api                  │ proxy /api
                                               │                             │
                  ┌────────────────────────────┴────────┐       ┌────────────┴────────────────┐
                  │          SETUP 1 : DEV              │       │        SETUP 2 : PROD       │
                  │         (Vite Dev Server)           │       │        (Nginx + Dist)       │
                  ├─────────────────────────────────────┤       ├─────────────────────────────┤
                  │ • URL : http://localhost:5173       │       │ • URL : http://localhost:8080│
                  │ • Hot Reload instantané (HMR)       │       │ • Sert les fichiers `dist/` │
                  │ • Proxy Vite interne vers 8000      │       │ • Proxy Nginx vers 8000     │
                  │ • Aucune compilation requise        │       │ • Teste cache, gzip, SPA &  │
                  │                                     │       │   headers de sécurité prod  │
                  └─────────────────────────────────────┘       └─────────────────────────────┘
```

---

## 2. Mode 1 : Développement Local (React + Vite)

C'est le mode par défaut pour le développement quotidien.

### Démarrage

1. **Lancer le backend FastAPI (Terminal 1)** :
   ```bash
   cd rtms-web/backend
   uv run uvicorn main:app --reload --port 8000
   ```

2. **Lancer le serveur de développement Vite (Terminal 2)** :
   ```bash
   cd rtms-web/frontend
   npm run dev
   ```

- **URL** : `http://localhost:5173`
- **Fonctionnement** : Vite sert les fichiers TypeScript/TSX à la volée avec rafraîchissement instantané et relaie automatiquement les requêtes `/api/*` vers `http://127.0.0.1:8000`.

---

## 3. Mode 2 : Test NGINX sur Mac avec Docker (Recommandé)

Permet de tester le comportement exact de NGINX (cache, compression gzip, routage SPA) sur macOS sans devoir installer NGINX sur le système.

### Méthode Rapide (Script npm)

1. Assurez-vous que votre backend FastAPI tourne sur le port `8000`.
2. Dans le dossier `frontend` :
   ```bash
   cd rtms-web/frontend
   npm run preview:nginx
   ```

Ce script effectue automatiquement :
- La compilation de production (`tsc -b && vite build`) dans `frontend/dist/`.
- Le démarrage d'un conteneur NGINX éphémère montant `dist/` et `nginx.dev-preview.conf`.

- **URL** : `http://localhost:8080`
- **Arrêt** : `Ctrl + C` dans le terminal.

### Commande Docker Manuelle

Si vous souhaitez exécuter le conteneur en arrière-plan ou personnaliser la commande :

```bash
cd rtms-web/frontend
npm run build

docker run -d --name rtms-nginx-preview --rm \
  -p 8080:80 \
  --add-host=host.docker.internal:host-gateway \
  -v "$(pwd)/dist:/usr/share/nginx/html:ro" \
  -v "$(pwd)/nginx.dev-preview.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:alpine
```

Pour arrêter le conteneur :
```bash
docker stop rtms-nginx-preview
```

---

## 4. Mode 3 : NGINX Natif sur Mac sans Docker (via Homebrew)

Si vous préférez exécuter NGINX directement sur macOS sans conteneurisation :

### 1. Installation de NGINX via Homebrew
```bash
brew install nginx
```

### 2. Création d'une configuration locale
Créez un fichier `rtms-web/frontend/nginx.macos.conf` :
```nginx
events {
    worker_connections 1024;
}

http {
    include /opt/homebrew/etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;

    server {
        listen 8080;
        server_name localhost;

        # Remplacer par le chemin absolu vers votre dossier frontend/dist
        root /Users/marctritschler/git_projects/rtms-web/frontend/dist;
        index index.html;

        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

### 3. Commandes d'exécution
- **Compiler les assets** : `npm run build`
- **Démarrer NGINX** : `nginx -c /Users/marctritschler/git_projects/rtms-web/frontend/nginx.macos.conf`
- **Recharger la configuration** : `nginx -c /Users/marctritschler/git_projects/rtms-web/frontend/nginx.macos.conf -s reload`
- **Arrêter NGINX** : `nginx -s stop`

---

## 5. Mode 4 : Déploiement Production (Linux / VPS OVH / On-Premise)

Pour le déploiement sur un serveur Linux (ex: Debian/Ubuntu chez OVH) :

### 1. Build complet de la suite
Exécutez le script de compilation globale :
```bash
cd rtms-web
./build.sh
```
Ce script produit :
- L'exécutable autonome du backend : `rtms-backend`
- Le bundle SPA statique du frontend : `frontend/dist/`

### 2. Déploiement via `rtms-installer`
Le script d'installation configure automatiquement les services et NGINX :
```bash
cd rtms-installer
sudo ./install.sh
```

### 3. Configuration NGINX de Production (`/etc/nginx/sites-available/rtms.conf`)

```nginx
server {
    listen 80;
    server_name votre-domaine.com;  # Ou l'IP du VPS OVH

    root /opt/rtms/frontend;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript;
    gzip_disable "MSIE [1-6]\.";

    # Reverse Proxy API -> FastAPI Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Fallback React Router SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache des assets statiques
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000";
    }
}
```

### 4. Activation HTTPS & Chiffrement TLS en Production

En production, **le chiffrement HTTPS est impératif** pour protéger les tokens d'authentification (JWT) et les flux de télémétrie contre toute interception réseau.

> [!NOTE]
> **Aucune modification du code frontend ou backend n'est requise** :
> Le frontend React utilise des chemins relatifs (`/api/...`) et s'adapte automatiquement au protocole de la page (`https://`). Le backend FastAPI écoute sur `127.0.0.1:8000` et NGINX prend en charge toute la terminaison TLS (déchiffrement/chiffrement).

#### Option A : Certificat automatique Let's Encrypt (Certbot)
Sur votre serveur Linux :
```bash
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```
Certbot adaptera automatiquement la configuration NGINX pour installer le certificat et configurer la redirection 301 HTTP -> HTTPS.

#### Option B : Certificat d'Entreprise / PKI Interne (`.crt` / `.key`)
Remplacez `/etc/nginx/sites-available/rtms.conf` par une configuration complète avec redirection et TLS durci :

```nginx
# 1. Redirection HTTP vers HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name votre-domaine.com;
    return 301 https://$host$request_uri;
}

# 2. Virtualhost HTTPS sécurisé
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name votre-domaine.com;

    root /opt/rtms/frontend;
    index index.html;

    # Certificats SSL
    ssl_certificate /etc/ssl/certs/rtms.crt;
    ssl_certificate_key /etc/ssl/private/rtms.key;

    # Protocoles et ciphers modernes (NIS 2 / ANSSI)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # En-têtes de sécurité
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy API -> FastAPI Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Fallback SPA React
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache des assets statiques
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000";
    }
}
```

Activez et rechargez NGINX :
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. Synthèse des Ports et Accès

| Environnement | URL | Backend utilisé | Rôle principal |
|---|---|---|---|
| **Dev (Vite)** | `http://localhost:5173` | `http://127.0.0.1:8000` | Développement avec Hot Reload |
| **Test NGINX (Docker)** | `http://localhost:8080` | `http://host.docker.internal:8000` | Validation locale de la config Nginx et du bundle `dist/` |
| **Test NGINX (Homebrew)** | `http://localhost:8080` | `http://127.0.0.1:8000` | Test Nginx natif sans conteneurs |
| **Production (VPS/Linux)** | `http://<IP_OU_DOMAINE>` | `http://127.0.0.1:8000` (service systemd) | Déploiement client / hébergement final |
