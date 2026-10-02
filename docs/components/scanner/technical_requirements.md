# RTMS (Real-Time Monitoring System) - Technical Requirements

Ce document détaille les prérequis matériels, logiciels et réseaux nécessaires pour le déploiement de la solution logicielle RTMS (Real-Time Monitoring System) par 3TS Consulting. 

RTMS est une solution 100% logicielle. Elle est conçue pour s'adapter à l'infrastructure existante du client, offrant deux modes de déploiement principaux : une installation conteneurisée (Docker) ou une installation native (Bare-Metal/VM) compatible avec Windows, macOS et Linux.

---

## 1. Prérequis Matériels (Toutes installations)

Les performances de RTMS dépendent de la taille du réseau à auditer et de la fréquence des synchronisations de la base de données de menaces (NVD).

*   **Processeur (CPU) :** Architecture x86_64 (AMD64) ou ARM64 (Apple Silicon, Raspberry Pi 5/6). Minimum 4 cœurs. 8 cœurs recommandés pour les environnements de taille moyenne à grande.
*   **Mémoire Vive (RAM) :** 
    *   Minimum : 4 Go (petits réseaux, environnement de test).
    *   Recommandé : 8 Go ou plus (pour supporter l'analyse de gros volumes de données Nmap et PostgreSQL en mémoire).
*   **Stockage (Disque) :**
    *   Minimum 50 Go d'espace libre.
    *   **Important :** Un disque SSD (ou NVMe) est **strictement recommandé**. Le système effectue des écritures fréquentes liées à l'ingestion des CVEs et aux logs des scans réseau. L'utilisation de cartes SD classiques (sur micro-ordinateurs) ou de disques durs mécaniques (HDD) entraînera des goulots d'étranglement sévères.
*   **Réseau :** Interface réseau Gigabit Ethernet (1 Gbps).

---

## 2. Options de Déploiement Logiciel

### Option A : Déploiement Conteneurisé (Recommandé)

C'est la méthode privilégiée pour un déploiement rapide, garantissant l'isolation des dépendances (PostgreSQL, Dashboard, Moteur de scan).

*   **Systèmes d'exploitation supportés :**
    *   Linux (Ubuntu 22.04/24.04, Debian 12, RHEL 9).
    *   Windows 10/11 ou Windows Server (via WSL2).
    *   macOS 12+ (Intel ou Apple Silicon).
*   **Dépendances requises :**
    *   Docker Engine (version 24.0.0 ou supérieure).
    *   Docker Compose (version V2).

### Option B : Déploiement Natif (Bare-Metal / VM)

Pour les environnements où la conteneurisation n'est pas possible ou souhaitée.

*   **Systèmes d'exploitation supportés :** Windows, macOS, Linux (Debian/Ubuntu/RHEL).
*   **Dépendances requises :**
    *   **Python :** Version 3.13 ou 3.14.
    *   **Nmap :** Version 7.90 ou supérieure (nécessaire pour la découverte réseau et l'identification des services).
    *   **PostgreSQL :** Version 15 ou supérieure (pour la base de données centrale).
    *   **Privilèges :** L'exécution du moteur RTMS nécessite des droits d'administration (`root` sur Linux/macOS, `Administrateur` sur Windows) pour permettre à Nmap de forger des paquets bruts (scans SYN, détection d'OS).

---

## 3. Prérequis Réseau et Pare-feu

Pour que RTMS puisse fonctionner et générer ses rapports de conformité NIS2, des flux réseaux spécifiques doivent être autorisés.

### Flux sortants (Outbound - Internet)
Le serveur hébergeant RTMS Web et les microservices doit pouvoir joindre internet (directement ou via un proxy d'entreprise) pour les services suivants :
*   `TCP/443` vers `services.nvd.nist.gov` : Synchronisation incrémentale de la base de données des vulnérabilités NIST NVD (microservice `rtms-nvd`).
*   `TCP/443` vers `vps-054fcfa2.vps.ovh.net` : Hub central de support technique et de télé-assistance (3TS Assistance).
*   `TCP/443` vers le serveur iTop (si le module CMDB est activé).
*   `TCP/587` (ou 465) vers le serveur SMTP défini par le client : Envoi des alertes critiques et des rapports PDF d'audit.

### Flux internes (Inbound/Outbound - LAN & Architecture Découplée)
*   **Sondes de scan distribuées (`rtms-scanner`)** :
    *   Les sondes distantes communiquent **exclusivement en HTTPS (`TCP/443` ou `TCP/8000`)** avec le serveur RTMS Web via l'API REST sécurisée par jeton Bearer (`RTMS_SERVER_URL` + `RTMS_SCANNER_TOKEN`).
    *   **Aucun flux PostgreSQL (`TCP/5432`) n'est requis ni recommandé** entre les sondes et la base de données centrale.
*   **Microservice NVD & Base de Données (`TCP/5432`)** :
    *   Le flux PostgreSQL direct est strictement réservé au réseau interne/local hébergeant `rtms-nvd` (pour le streaming de 250k+ CVEs et la corrélation CPE), sécurisé par le rôle à moindres privilèges `rtms_nvd_user` (restreint au schéma `nvd`).
*   **Périmètre de scan LAN :** Le serveur ou la sonde RTMS doit disposer d'interfaces ou de routes réseau actives vers tous les sous-réseaux (VLANs) à inventorier (ARP, ICMP, Nmap).
*   **Filtrage interne :** Il est recommandé de créer une exception dans les pare-feux internes (IDS/IPS) pour l'adresse IP du scanner RTMS, afin d'éviter les faux positifs.
*   **Accès Dashboard Console :** Ouverture du port `TCP/443` (ou `TCP/8080` / `TCP/80`) vers le serveur RTMS Web pour l'accès des administrateurs à la console React.

---

## 4. Notes pour la Conformité NIS2

Dans le cadre d'une démarche de mise en conformité continue, il est fortement conseillé de dédier une machine virtuelle (VM) ou un micro-serveur matériel exclusif à RTMS. La cohabitation de l'outil avec d'autres services métiers sur un même système d'exploitation n'est pas recommandée pour des raisons d'isolation de sécurité et de prévisibilité des performances.