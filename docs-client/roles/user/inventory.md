# Inventaire Dynamique des Actifs Réseau

Le module **Actifs** (`/assets`) constitue la base d'inventaire en temps réel de votre infrastructure.

---

## 1. Découverte Automatique

Chaque équipement présent sur votre réseau est automatiquement identifié par les sondes RTMS :
* **Adresse IP & Sous-réseau CIDR** : Positionnement logique de l'équipement.
* **Adresse MAC & Constructeur (OUI)** : Identification matérielle du fabricant (ex: *Cisco*, *Dell*, *Apple*, *Schneider Electric*).
* **Nom d'hôte (Hostname)** : Résolu via requêtes DNS inverses, bannières NetBIOS/mDNS, ou interception passive des requêtes DHCP (**DHCP Snooping**).
* **Système d'Exploitation (OS)** : Empreinte TCP/IP déduite par Nmap.
* **Statut de Présence** : Indique si l'équipement a été vu lors du dernier cycle de scan (`En ligne`) ou son temps d'absence.

---

## 2. Fiche Détail d'un Actif

En cliquant sur n'importe quel équipement dans la liste, vous ouvrez sa fiche technique complète :

* **Services & Ports Ouverts** : Liste exhaustive des ports TCP/UDP ouverts, protocoles associés, logiciels identifiés et versions exactes.
* **Vulnérabilités Associées (CVE)** : Liste des failles de sécurité connues affectant les versions logicielles de cet équipement, enrichies des scores CVSS v3.
* **Historique des Détections** : Horodatage précis de la première découverte et de la dernière activité constatée.
* **Statut Deep Scan** : Indique si l'équipement fait l'objet d'audits de vulnérabilités approfondis ou s'il est exempté (ex: automate industriel ou équipement fragile).

---

## 3. Recherche et Exportation

* **Recherche textuelle** : Tapez une fraction d'adresse IP (ex: `192.168.1.`) ou un nom de serveur pour filtrer instantanément la vue.
* **Exportation** : Téléchargez l'état actuel de votre parc informatique au format **CSV** ou **JSON** pour alimenter vos outils bureautiques ou vos réunions d'exploitation.
