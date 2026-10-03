# Architecture & Capacités de la Sonde RTMS

Ce document présente l'architecture technique, les topologies de déploiement et les capacités opérationnelles du moteur de collecte et d'analyse **RTMS (Real-Time Monitoring & Security)** développé par **3TS Consulting**.

Conçu pour les environnements d'entreprise exigeants, RTMS combine une **détection passive continue à impact zéro** avec des **audits actifs granulaires**, garantissant une visibilité totale sur l'ensemble du parc informatique et industriel (IT / OT / IoT).

---

## 1. Vue d'Ensemble & Positionnement

Les solutions traditionnelles de sécurité réseau reposent généralement soit sur des agents lourds déployés sur chaque poste, soit sur des scanners de vulnérabilités intrusifs qui peuvent saturer la bande passante et déstabiliser les équipements sensibles (automates programmables, imprimantes, dispositifs médicaux).

**La sonde RTMS adopte une approche hybride non-disruptive :**

* **Visibilité en temps réel (Zero-Impact)** : Écoute passive permanente des trames réseau et des protocoles de découverte (ARP, DHCP, mDNS, LLMNR, SSDP, CDP/LLDP).
* **Détection précoce des menaces** : Identification instantanée des nouveaux équipements non autorisés (*rogue devices*), des conflits IP/MAC et des comportements anormaux.
* **Audits ciblés et contrôlés** : Découverte approfondie des services exposés (*Deep Scan*) et audits protocolaires de conformité, strictement encadrés par politique réseau.
* **Corrélation de vulnérabilités souveraine** : Enrichissement automatique des actifs avec la base mondiale NIST NVD via un microservice local, sans fuite de télémétrie vers l'extérieur.

```mermaid
graph TD
    subgraph "Infrastructure Client Surveillée"
        SW["Switch de Cœur / Distribution<br/>(Port Mirroring / SPAN / TAP)"]
        LAN["Postes de travail & Serveurs"]
        IOT["Équipements IoT & Imprimantes"]
        OT["Automates Industriels (OT)"]
        SW --- LAN
        SW --- IOT
        SW --- OT
    end

    subgraph "Appliance / Sonde RTMS"
        PROBE["Sonde RTMS Scanner"]
        PASSIVE["Moteur Passif<br/>(Zero-Impact Discovery)"]
        ACTIVE["Moteur d'Audit Actif<br/>(Deep Scan Ciblé)"]
        PROBE --> PASSIVE
        PROBE --> ACTIVE
    end

    SW -.->|Flux miroir| PROBE

    subgraph "Plateforme Centrale RTMS"
        WG["Tunnel Chiffré WireGuard"]
        API["Backend FastAPI & RBAC"]
        DB[("PostgreSQL Durci<br/>rtms_db")]
        NVD["Microservice NVD Local<br/>(CVE / CPE NIST)"]
        WEB["Console d'Exploitation Web<br/>(SOC & Conformité NIS2)"]

        WG --> API
        API --> DB
        API --> NVD
        API --> WEB
    end

    PROBE ==>|Télémétrie chiffrée (mTLS / WireGuard)| WG
```

---

## 2. Topologies de Déploiement Réseau

La sonde RTMS s'adapte à toute topologie d'infrastructure, des PME mono-site aux architectures distribuées multi-filiales.

### Mode 1 : Écoute Passive via Port Mirroring (SPAN / TAP)
* **Recommandé pour** : Les cœurs de réseau, centres de données et segments critiques.
* **Fonctionnement** : Le switch d'infrastructure copie l'intégralité du trafic broadcast/multicast ou des VLANs surveillés vers l'interface réseau dédiée de la sonde.
* **Avantage sécurité** : L'interface de capture de la sonde est **purement passive** (aucune adresse IP requise sur le segment surveillé, aucune émission de paquet, sonde totalement invisible et invulnérable depuis le réseau d'écoute).

### Mode 2 : Sonde Multi-Homed (Collecte & Management Séparés)
* **Recommandé pour** : Les déploiements physiques sur appliance 1U ou mini-PC durci.
* **Interface 1 (Surveillance)** : Connectée au réseau local ou aux VLANs à monitorer.
* **Interface 2 (Administration & Remontée)** : Connectée à un réseau d'administration dédié ou directement à un tunnel VPN WireGuard point-à-point vers la console centrale.
* **Avantage sécurité** : Cloisonnement strict des flux. Même en cas de compromission locale du réseau bureautique, la liaison de supervision reste isolée et chiffrée.

### Mode 3 : Haute Disponibilité (Actif / Standby Failover)
* Deux sondes RTMS sont déployées sur le même périmètre en configuration redondante.
* La sonde primaire collecte et transmet la télémétrie.
* La sonde secondaire surveille le heartbeat de la sonde primaire via la plateforme centrale ; en cas d'interruption ou de défaillance matérielle, la sonde secondaire bascule automatiquement en mode actif sans rupture d'historique.

### Mode 4 : Micro-Sondes & Agences Distantes (RTMS Local Agent)
* Pour les filiales distantes, le personnel en télétravail ou les environnements cloud privés (AWS, Azure, GCP).
* Un agent léger et autonome exécute la découverte locale et transmet ses métriques chiffrées vers la plateforme centrale via HTTPS/REST ou WireGuard.

---

## 3. Capacités du Moteur de Détection & d'Analyse

### A. Cartographie des Actifs & Empreinte Numérique (*Fingerprinting*)
Dès sa mise sous tension, la sonde RTMS dresse l'inventaire en temps réel de tous les équipements connectés :
* **Découverte immédiate des hôtes** : Détection des adresses MAC, IP attribuées, baux DHCP émis, noms d'hôtes NetBIOS / mDNS.
* **Identification du constructeur** : Résolution matérielle automatique via le registre officiel IEEE OUI (Apple, Cisco, Dell, HP, Fortinet, Schneider Electric, Siemens, etc.).
* **Fingerprinting d'OS & de firmware** : Analyse des signatures TCP/IP (tailles de fenêtres SYN, TTL par défaut), requêtes mDNS/Bonjour, user-agents et bannières protocolaires.
* **Catégorisation automatique** : Classification des équipements (Serveur, Poste de travail, Imprimante, Switch/Routeur, Caméra IP, Automate industriel, Smartphone/Tablette).

### B. Surveillance Continue de la Posture Réseau
La sonde analyse le trafic en permanence pour déceler toute anomalie de bas niveau :
* **Détection de Rogue Devices** : Alerte immédiate dès qu'un appareil inconnu se connecte pour la première fois sur un sous-réseau.
* **Détection d'usurpation d'adresse (ARP Spoofing)** : Détection des conflits IP (deux adresses MAC différentes réclamant la même IP) et des tentatives d'attaque Man-in-the-Middle (MitM).
* **Dérive des passerelles et serveurs DNS** : Signalement instantané si un serveur DHCP pirate ou une fausse passerelle réseau est annoncée.

### C. Deep Scan Granulaire & Audits Ciblés
Contrairement aux scanners aveugles, RTMS permet de définir des **politiques de scan ciblées par sous-réseau** :
* **Plages de ports configurables** : Ports essentiels, ports web, top 1000 ou personnalisé.
* **Scan TCP furtif (SYN Scan / Connect)** : Évaluation de l'exposition réelle des ports réseau avec un taux d'émission maîtrisé pour ne jamais saturer les commutateurs.
* **Exclusion stricte des segments sensibles** : Possibilité de déclarer des plages IP en mode « Passif strict » (ex: automates de production, dispositifs médicaux) pour interdire tout paquet de scan actif.

### D. Audits Spécialisés Intégrés
La sonde intègre des modules d'évaluation spécialisés :
* **Audit Mail & Relais Ouverts** : Vérification des serveurs SMTP locaux pour prévenir le risque de relais de spam et d'usurpation de domaine.
* **Détection des Protocoles Obsolètes** : Audit des partages SMBv1 (vecteur majeur des ransomwares type WannaCry), des services telnet en clair, et des serveurs web utilisant des versions non sécurisées de SSL/TLS.
* **Audit de l'exposition des accès distants** : Détection des interfaces RDP, VNC, SSH exposées de manière anormale.

---

## 4. Corrélation Locale des Vulnérabilités (Microservice NVD)

La plateforme RTMS intègre en local le catalogue officiel des vulnérabilités de l'institut américain des normes et de la technologie (**NIST NVD - National Vulnerability Database**) :

* **Zéro fuite d'information** : L'inventaire de vos actifs et de vos logiciels ne quitte jamais votre périmètre. La sonde corrèle les CPE (*Common Platform Enumeration*) découverts avec la base locale NVD hébergée sur votre serveur RTMS.
* **Mise à jour incrémentale continue** : Synchronisation périodique avec l'API NIST pour ingérer les nouveaux bulletins CVE, scores CVSS v3.1 et vecteurs d'attaque.
* **Priorisation par gravité** : Triage automatique des vulnérabilités critiques (CVSS ≥ 9.0) ayant un impact direct sur les actifs de votre inventaire.

---

## 5. Sécurité, Durcissement & Souveraineté de la Sonde

La sonde RTMS est conçue selon le principe de **défense en profondeur** :

| Domaine de Sécurité | Mesure Mise en Œuvre |
| :--- | :--- |
| **Surface d'écoute externe** | Aucun port d'administration ouvert sur les interfaces de capture réseau. |
| **Authentification sonde-serveur** | Jetons cryptographiques uniques révocables (*Bearer Token*) associés à un identifiant matériel unique (*Machine ID*). |
| **Chiffrement des transmissions** | Télémétrie encapsulée dans un tunnel WireGuard chiffré (ChaCha20-Poly1305) ou HTTPS/TLS 1.3. |
| **Résilience hors-ligne** | Tampon de télémétrie local en cas de coupure de liaison : aucune perte de données, synchronisation automatique dès reconnexion. |
| **Cloisonnement RBAC** | Ségrégation stricte des rôles (Opérateur, Analyste SOC, Auditeur, Admin) conforme aux exigences de moindre privilège. |

---

## 6. Alignement Réglementaire & Intégration Entreprise

### Conformité Directive Européenne NIS2
RTMS répond directement aux obligations des entités essentielles et importantes :
* **Article 21 (Mesures de gestion des risques)** : Tenue à jour automatique de la cartographie des actifs et détection continue des vulnérabilités critiques.
* **Article 23 (Notification des incidents)** : Détection temps réel des équipements suspects et traçabilité pour alimenter la notification sous 24 heures.

### Intégration SIEM & CMDB
* **Synchronisation CMDB iTop** : Rapprochement automatique entre les équipements découverts sur le terrain et la base d'actifs déclarée de l'organisation.
* **Export SOC / SIEM** : Envoi des alertes et journaux d'événements au format standardisé Syslog RFC 5424 vers vos plateformes centralisées (Wazuh, Splunk, Elastic, Microsoft Sentinel).

---

## 7. Spécifications Techniques Résumées

| Caractéristique | Spécification |
| :--- | :--- |
| **Modes de capture** | Passif (libpcap / socket brut), Actif ciblé (TCP SYN/Connect, ICMP, DNS, SMB, SMTP) |
| **Protocoles passifs analysés** | ARP, DHCP, mDNS, LLMNR, SSDP, CDP, LLDP, NetBIOS, IPv4, IPv6 |
| **Fréquence de collecte** | Détection passive continue en temps réel ; cycles d'audit actifs programmables (ex: 2h, 6h, 24h) |
| **Empreinte matérielle sonde** | Appliance physique x86_64 / ARM (Raspberry Pi 4/5, mini-PC durci) ou machine virtuelle (VMware, Proxmox, Hyper-V, KVM) |
| **Systèmes d'exploitation supportés** | Linux durci (Debian 12, Ubuntu 22.04/24.04 LTS, Rocky Linux, Alpine) |
| **Besoins bande passante sonde-serveur** | Moins de 50 Ko/s en régime nominal (métadonnées et événements compressés) |
| **Base de vulnérabilités** | NIST NVD (CVE, CPE, CVSS v2 / v3.1) répliquée localement |

---

*Pour toute demande de démonstration ou d'évaluation technique dans votre infrastructure, contactez **3TS Consulting** sur [https://3ts.ai](https://3ts.ai) ou par email à `contact@3ts.ai`.*
