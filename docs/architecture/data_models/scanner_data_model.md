# Modèle de Données : RTMS Scanner

Ce document présente une courte description des tables utilisées par `rtms-scanner` et son backend de gestion (`rtms-commons`), réparties dans les schémas `admin` et `scanner`.

## Schéma `admin`
Ce schéma gère le contexte global, le multi-tenant, les alertes CVE, l'inventaire consolidé et l'administration de la plateforme.

| Table | Description |
|---|---|
| **`admin.tenant_infra`** | Table maîtresse du multi-tenant. Identifie chaque client (tenant) de la plateforme pour isoler les données, les alertes et les configurations. |
| **`admin.assets`** | Inventaire consolidé et global de tous les appareils et hôtes (devices) découverts sur le réseau, rattaché à un tenant. |
| **`admin.asset_software`** | Liste des logiciels, applications et systèmes d'exploitation installés ou détectés sur chaque équipement (asset). |
| **`admin.asset_vulnerabilities`** | Association entre les assets et les vulnérabilités (CVE) détectées sur ces équipements. |
| **`admin.cve_alerts`** | Historique et journalisation des alertes de sécurité (CVE) qui ont été déclenchées et envoyées. |
| **`admin.cve_alerts_config`** | Configuration des règles d'alertes par tenant (ex: seuil de criticité, canal d'envoi comme email ou webhook). |
| **`admin.login_audit`** | Journal d'audit pour tracer les connexions et actions des utilisateurs sur la plateforme. |
| **`admin.nvd_config`** | Configuration de l'intégration avec la National Vulnerability Database (NVD) pour la mise à jour des CVEs par tenant. |
| **`admin.product_license`** | Gestion des licences du produit RTMS (expiration, périmètre de la licence). |
| **`admin.service_registry`** | Registre d'enregistrement et de supervision des microservices RTMS (scanners, agents, NVD). Contient la configuration locale des scanners : sous-réseaux, deep scan, exclusions, scan Wi-Fi (`scan_wifi`), scan Ethernet (`scan_ethernet`), options SNMP (`snmp_scan`, `snmp_target_ip`, `snmp_community`). |
| **`admin.subnet_names`** | Noms personnalisés et descriptions attribués aux sous-réseaux CIDR (ex: DMZ, Production, Wi-Fi Invités) gérés depuis le portail d'administration. |
| **`admin.subnet_mac_whitelist`** | Liste blanche des adresses MAC autorisées par sous-réseau (CIDR) permettant de supprimer les alertes de nouveaux appareils (`NEW_HOST`) et d'appareils non identifiés. |
| **`admin.system_config`** | Paramètres système globaux de la plateforme, incluant les commutateurs maîtres d'autorisation physique : scan Wi-Fi (`wifi_scan_enabled`) et scan Ethernet (`ethernet_scan_enabled`). |
| **`admin.tenant_assets`** | Table gérant le cycle de vie et l'intégration des assets spécifiques à l'inventaire d'un tenant. |
| **`admin.tenant_asset_software`** | Table gérant le cycle de vie et l'intégration des logiciels par tenant. |
| **`admin.users`** | Comptes des utilisateurs ayant accès au portail d'administration de la plateforme. |
| **`admin.vulnerability_view`** | (Vue) Console/Vue SQL simplifiant les requêtes pour les tableaux de bord relatifs aux vulnérabilités des équipements. |

## Schéma `scanner`
Ce schéma est dédié au fonctionnement technique et local du moteur de scan. Il gère la configuration des scans, l'historique d'exécution et les résultats bruts.

| Table | Description |
|---|---|
| **`scanner.organizations`** | Regroupement logique et local (ex: site géographique, bureau, datacenter) permettant de segmenter les réseaux à scanner. |
| **`scanner.networks`** | Définition des sous-réseaux (en format CIDR) surveillés et scannés par le moteur de scan pour une organisation donnée. |
| **`scanner.network_mappings`** | Correspondances et routage des réseaux (ex: association entre un réseau et l'adresse MAC de sa passerelle) pour détecter les changements. |
| **`scanner.excluded_ips`** | Liste des adresses IP ou des plages d'IP à ignorer explicitement lors des cycles de scan. |
| **`scanner.scanner_config`** | Magasin de configuration (clé-valeur) dynamique pour le scanner (intervalles, commandes Nmap, drapeaux d'exécution, synchronisation des switches globaux `scanner.global_wifi_scan_enabled` et `scanner.global_ethernet_scan_enabled`). |
| **`scanner.scans`** | Historique de l'exécution des scans (date de début, fin, statut, et éventuellement un dump des résultats bruts JSON). |
| **`scanner.scan_archives`** | Instantanés et archives complètes des scans de réseau (snapshot JSONB consolidant hôtes, ports, services et logiciels pour un scanner et un sous-réseau, avec calcul de diff et export JSON). |
| **`scanner.services`** | Inventaire des ports ouverts et des services réseaux découverts sur les équipements scannés. |
| **`scanner.vulnerabilities`** | Vulnérabilités détectées *directement* (ex: scripts Nmap) lors du scan actif d'un équipement. |
| **`scanner.alerts`** | Alertes opérationnelles générées par le scanner (nouvel appareil, changement d'IP, usurpation ARP de passerelle, conflit d'adresse MAC). |
| **`scanner.host_tags`** | Étiquettes (tags) personnalisées associées aux hôtes découverts pour faciliter leur catégorisation. |
| **`scanner.itop_assets`** | Table de correspondance et de synchronisation des équipements avec une CMDB externe comme iTop. |

---

## Cycle de Vie et Détection de l'État des Sous-Réseaux

Le système évalue l'état opérationnel de chaque sous-réseau via deux niveaux complémentaires :

1. **Niveau 1 : Présence d'une interface réseau physique (« Non connecté »)**
   - Le moteur de scan interroge au démarrage et à chaque battement de cœur (`check_env()`) les interfaces réseau physiques locales de la machine hôte.
   - Les blocs CIDR associés aux interfaces actives sont enregistrés dans la colonne `subnet` de la table `admin.service_registry`.
   - Si un sous-réseau présent dans l'inventaire historique ne correspond à **aucune interface réseau physique active** sur la machine du scanner, le scanner ne peut pas émettre de trames (couche 2 / ARP).
   - Ce sous-réseau est alors considéré comme **Non connecté** (`isSubnetConnected = false`, `subnet_active = false`), ses hôtes sont marqués hors ligne, et son affichage dans l'interface web est **replié d'office sous forme d'une seule ligne**.

2. **Niveau 2 : Découverte et disponibilité des hôtes (« Inactif / Hors ligne »)**
   - Si le scanner possède bien une interface réseau active sur le sous-réseau (`isSubnetConnected = true`), il réalise des balayages périodiques (ARP sweep, ICMP ping, détection Nmap).
   - Si au moins un hôte répond, le sous-réseau est **En ligne (vert)** (`isSubnetOnline = true`).
   - Si le scan s'exécute mais qu'**aucun hôte ne répond** (ou que tous les hôtes connus sont éteints/injoignables), le compteur d'hôtes en ligne passe à 0.
   - Le sous-réseau est alors marqué **Inactif / Hors ligne** (`isSubnetOnline = false`) et est également **replié d'office sous forme d'une seule ligne** dans l'inventaire web.

---

## Liste Blanche d'Adresses MAC par Sous-Réseau (Suppression d'Alertes)

Afin d'éviter la fatigue d'alertes dans les environnements dynamiques ou lors de l'intégration d'équipements légitimes récurrents (ex : imprimantes, équipements IoT, bancs de test), RTMS permet de configurer une liste blanche d'adresses MAC par sous-réseau :

* **Table dédiée (`admin.subnet_mac_whitelist`) :**
  * `id` : Identifiant unique auto-incrémenté.
  * `subnet_cidr` : Bloc CIDR du sous-réseau cible (ex : `192.168.1.0/24`).
  * `mac_address` : Adresse MAC normalisée au format `XX:XX:XX:XX:XX:XX`.
  * `label` : Libellé ou motif de la mise en liste blanche.
  * `created_by` / `created_at` : Traçabilité de l'administrateur ayant autorisé l'équipement.
  * Contrainte unique sur le couple `(subnet_cidr, mac_address)`.

* **Comportement du Moteur de Scan (`rtms-scanner/main_scanner.py`) :**
  * À chaque cycle de scan, la liste blanche est chargée dynamiquement via `rtms_commons.db_client.load_subnet_mac_whitelist()`.
  * Lors de la découverte d'un équipement sur un sous-réseau donné (`ctx_target`), son adresse MAC est comparée à la liste blanche associée à ce bloc CIDR.
  * Si l'adresse MAC est présente dans la liste blanche :
    * La génération de l'alerte **`NEW_HOST`** (et les avertissements d'équipement inconnu / nom d'hôte manquant) est **automatiquement supprimée**.
    * L'appareil est enregistré dans l'inventaire `global_known_macs` avec le libellé de secours `"Whitelisted-Device"` s'il n'a pas encore de nom d'hôte résolu.
    * Un message de débogage explicite est consigné dans les journaux : `[MAC WHITELIST] Host <IP> (MAC: <MAC>) is whitelisted on subnet <SUBNET>. Suppressing unknown device and missing hostname alerts.`
