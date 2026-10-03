# RTMS Web - Frontend & NGINX Environments Guide

This document details the different deployment and testing configurations for the RTMS Web frontend:
1. **Development Mode (React + Vite)**: Day-to-day workflow with Hot Module Replacement (HMR).
2. **NGINX Preview with Docker (macOS)**: Simulates production behavior locally without installing NGINX on the host OS.
3. **Native NGINX Mode (macOS via Homebrew)**: Runs NGINX directly on macOS.
4. **Production Deployment (Linux / OVH VPS / On-Premise)**: Production hosting with reverse proxy and TLS encryption.

---

## 1. Architectural Overview

```
                                 ┌─────────────────────────────────────────────────────────┐
                                 │                 FASTAPI BACKEND (8000)                  │
                                 │  - Dev Mode: `uv run uvicorn main:app --reload`         │
                                 │  - Prod Mode: standalone binary `./rtms-backend`        │
                                 └─────────────▲─────────────────────────────▲─────────────┘
                                               │ proxy /api                  │ proxy /api
                                               │                             │
                  ┌────────────────────────────┴────────┐       ┌────────────┴────────────────┐
                  │          SETUP 1: DEV               │       │        SETUP 2: PROD        │
                  │         (Vite Dev Server)           │       │        (Nginx + Dist)       │
                  ├─────────────────────────────────────┤       ├─────────────────────────────┤
                  │ • URL: http://localhost:5173        │       │ • URL: http://localhost:8080│
                  │ • Instant Hot Reload (HMR)          │       │ • Serves `dist/` bundle     │
                  │ • Internal Vite proxy to 8000       │       │ • Nginx proxy to 8000       │
                  │ • No build step required            │       │ • Tests cache, gzip, SPA &  │
                  │                                     │       │   security headers          │
                  └─────────────────────────────────────┘       └─────────────────────────────┘
```

---

## 2. Mode 1: Local Development (React + Vite)

The standard mode for engineering and feature development.

### Startup Procedure

1. **Launch FastAPI Backend (Terminal 1)**:
   ```bash
   cd rtms-web/backend
   uv run uvicorn main:app --reload --port 8000
   ```

2. **Launch Vite Dev Server (Terminal 2)**:
   ```bash
   cd rtms-web/frontend
   npm run dev
   ```

- **URL**: `http://localhost:5173`
- **Operation**: Vite serves TypeScript/TSX on the fly with instantaneous refresh and relays `/api/*` requests automatically to `http://127.0.0.1:8000`.

---

## 3. Mode 2: NGINX Preview on macOS with Docker (Recommended)

Validates NGINX behaviors (client caching, gzip compression, SPA history fallback) locally without modifying host system packages.

### Quick Method (npm script)

1. Ensure the FastAPI backend is running on port `8000`.
2. Inside `rtms-web/frontend`:
   ```bash
   cd rtms-web/frontend
   npm run preview:nginx
   ```

This script automatically executes:
- Production bundle compilation (`tsc -b && vite build`) into `frontend/dist/`.
- Starts an ephemeral NGINX Alpine container mounting `dist/` and `nginx.dev-preview.conf`.

- **URL**: `http://localhost:8080`
- **Stop**: `Ctrl + C` in terminal.

### Manual Docker Command

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

To stop:
```bash
docker stop rtms-nginx-preview
```

---

## 4. Mode 3: Native NGINX on macOS (via Homebrew)

If containerization is not preferred:

### 1. Install NGINX
```bash
brew install nginx
```

### 2. Create Configuration File
Create `rtms-web/frontend/nginx.macos.conf`:
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

        # Replace with absolute path to your frontend/dist
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

### 3. Execution Commands
- **Build assets**: `npm run build`
- **Start NGINX**: `nginx -c /Users/marctritschler/git_projects/rtms-web/frontend/nginx.macos.conf`
- **Reload**: `nginx -c /Users/marctritschler/git_projects/rtms-web/frontend/nginx.macos.conf -s reload`
- **Stop**: `nginx -s stop`

---

## 5. Mode 4: Production Deployment (Linux / OVH VPS / On-Premise)

For servers running Ubuntu or Debian:

### 1. Build Production Binaries & Bundle
```bash
cd rtms-web
./build.sh
```
Outputs:
- Self-contained backend binary: `rtms-backend`
- Static SPA production bundle: `frontend/dist/`

### 2. Automated Provisioning via `rtms-installer`
```bash
cd rtms-installer
sudo ./install.sh
```

### 3. Hardened Production NGINX Config (`/etc/nginx/sites-available/rtms.conf`)

```nginx
# 1. HTTP to HTTPS Redirection
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

# 2. Hardened HTTPS Virtualhost
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;

    root /opt/rtms/frontend;
    index index.html;

    # TLS Certificates
    ssl_certificate /etc/ssl/certs/rtms.crt;
    ssl_certificate_key /etc/ssl/private/rtms.key;

    # ANSSI / NIS2 Compliant Modern Ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API Reverse Proxy -> FastAPI Backend
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

    # SPA Router Fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Long-term Asset Caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000";
    }
}
```

Reload NGINX:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. Port & Environment Matrix

| Environment | URL | Backend Target | Purpose |
|---|---|---|---|
| **Dev (Vite)** | `http://localhost:5173` | `http://127.0.0.1:8000` | Local feature engineering with Hot Reload |
| **Test NGINX (Docker)** | `http://localhost:8080` | `http://host.docker.internal:8000` | Local NGINX parity and SPA routing validation |
| **Test NGINX (Homebrew)** | `http://localhost:8080` | `http://127.0.0.1:8000` | Native host NGINX evaluation |
| **Production (VPS/Linux)** | `https://<DOMAIN>` | `http://127.0.0.1:8000` (systemd) | Production deployment / client appliance |
