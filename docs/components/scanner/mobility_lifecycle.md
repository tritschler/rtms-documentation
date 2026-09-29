# Mobilité du Scanner, Cycle de Vie & Gestion Multi-Réseaux

Ce document décrit le comportement architectural et opérationnel de la sonde `rtms-scanner` et de la plateforme RTMS lorsqu'une machine exécutant le scanner change d'environnement réseau (mobilité / roaming, ex: déplacement d'un ordinateur portable Mac ou PC d'un réseau d'entreprise vers un réseau domestique).

---

## 1. Contexte et Problématique de Mobilité

Dans de nombreux cas d'usage (postes d'analystes, audits itinérants, ordinateurs de travail hybrides), une machine hôte hébergeant le scanner RTMS peut être amenée à :
1. Fonctionner et découvrir des équipements sur un sous-réseau A (ex : `10.20.0.0/24` ou réseau d'un client / bureau).
2. Être éteinte ou déconnectée de ce réseau.
3. Être redémarrée sur un sous-réseau B complètement distinct (ex : réseau domestique `192.168.1.0/24`).

Ce document répond aux questions clés :
* **Que devient l'ancien scanner dans la vue des services ?**
* **L'ancien sous-réseau et ses équipements sont-ils effacés ?**
* **Comment le nouveau réseau est-il pris en compte ?**

---

## 2. Cycle de Vie dans le Registre des Services (`admin.service_registry`)

### A. Identification Unique Matérielle (`machine_id`)
Chaque instance de `rtms-scanner` détermine au démarrage un identifiant matériel persistant (`machine_id`) basé sur les caractéristiques physiques uniques de la machine hôte (UUID matériel DMI/Apple IORegistry, hachage d'adresses MAC principales).

Cet identifiant accompagne chaque paquet de battement de cœur (*heartbeat*) transmis au serveur central `rtms-web`.

### B. Détection d'Arrêt & Statut OFFLINE
* Lorsque le scanner quitte le réseau A ou est arrêté, l'envoi périodique des heartbeats cesse.
* Le mécanisme de surveillance du serveur RTMS (`services_health_monitor_worker` / balayage de statut) applique une fenêtre de tolérance :
  * Si un scanner n'a pas émis de heartbeat depuis plus de **30 secondes**, son statut passe automatiquement de `RUNNING` à **`OFFLINE`** (Arrêté).
  * L'entrée reste visible dans le tableau de bord des services pour avertir l'administrateur de l'arrêt du service.

### C. Réactivation sur le Nouveau Réseau
Dès que le scanner démarre sur le nouveau réseau (réseau B) :
1. **Récupération et Déduplication :** Le serveur reçoit le premier heartbeat contenant le `machine_id` et le nouveau nom d'hôte. La requête SQL recherche dans `admin.service_registry` l'enregistrement existant correspondant à cette machine :
   ```sql
   SELECT id, service_name, status, started_at
   FROM admin.service_registry
   WHERE (service_name = :s OR (machine_id = :mid AND service_name LIKE 'rtms-scanner%'))
   ORDER BY ... LIMIT 1;
   ```
2. **Mise à jour en place (In-Place Update) :** L'enregistrement existant est directement actualisé :
   * Le statut repasse à **`RUNNING`** (vert).
   * L'adresse IP de l'hôte (`host_ip`) est mise à jour avec la nouvelle adresse IP locale.
   * La colonne `subnet` est remplacée par le ou les nouveaux blocs CIDR découverts localement (ex : `192.168.1.0/24`).
   * Le champ `last_heartbeat` est réinitialisé à l'heure courante.
3. **Purge des entrées résiduelles :** Si une entrée orpheline marquée `OFFLINE` partageant le même `machine_id` subsiste, le système réattribue ses références de scans et d'actifs à l'entrée active, puis supprime proprement la ligne obsolète.
4. **Élection de leader (Redondance) :** Si un autre scanner actif surveillait déjà le réseau B, la sonde bascule intelligemment en mode **`STANDBY`** (redondance haute disponibilité). Si elle est la seule sonde sur ce réseau, elle prend immédiatement le rôle actif **`RUNNING`**.

---

## 3. Persistance des Réseaux et de l'Inventaire des Actifs

Une question fréquente est de savoir si le déplacement du scanner efface l'ancien sous-réseau ou ses équipements. **La réponse est NON.**

RTMS est conçu selon les principes de traçabilité et de conformité (directive NIS2, audit de parc, Cyber Resilience Act). L'inventaire fonctionne comme une base de connaissances historique (CMDB) :

### A. Conservation de l'Ancien Sous-Réseau (`scanner.networks`)
* L'ancien sous-réseau (ex : `10.20.0.0/24`) **reste conservé** dans la table `scanner.networks`.
* Dans l'interface d'inventaire :
  * Étant donné qu'aucune interface réseau du scanner local n'est actuellement liée à ce bloc, le sous-réseau est marqué comme **« Non connecté »** (`isSubnetConnected = false`).
  * Il est automatiquement **replié en une seule ligne compacte** pour ne pas encombrer l'écran tout en préservant son historique complet.

### B. Conservation des Actifs Découverts (`admin.assets`)
* Les ordinateurs, imprimantes et serveurs découverts sur l'ancien réseau **ne sont pas supprimés**.
* Ils conservent leur fiche détaillée : adresse IP, adresse MAC, fabricant, OS détecté, ports et services ouverts, ainsi que leur horodatage de dernière vue (`last_seen`).
* **Isolation du marquage hors ligne :** Lorsqu'un cycle de scan s'exécute sur le nouveau réseau B, l'invalidation des hôtes injoignables (`is_up = false`) est **strictement cantonnée au sous-réseau actuellement scanné** :
  ```sql
  UPDATE admin.assets
  SET is_up = false
  WHERE (network_id = :nid OR network_id IN (
      SELECT id FROM scanner.networks WHERE cidr = CAST(:cidr AS cidr)
  )) AND NOT (ip_address = ANY(:seen_ips));
  ```
  Les actifs de l'ancien réseau ne sont donc pas impactés par les résultats du scan du nouveau réseau.

### C. Création du Nouveau Réseau
* Dès la fin du premier scan sur le réseau B, `scanner.networks` crée automatiquement une nouvelle ligne de sous-réseau (ex : `Subnet 192.168.1.0/24`) si elle n'existait pas encore.
* Les nouveaux actifs découverts y sont enregistrés et rattachés.
* Les instantanés de scans (`scanner.scan_archives`) et historiques (`scanner.scans`) sont compartimentés par sous-réseau et horodatés.

---

## 4. Tableau Synthétique des Comportements

| Composant / Donnée | Avant le déplacement (Réseau A) | Scanner à l'arrêt | Après redémarrage (Réseau B) |
| :--- | :--- | :--- | :--- |
| **Statut du Service** | `RUNNING` | `OFFLINE` (après 30s) | `RUNNING` (ou `STANDBY` si doublon actif) |
| **Sous-réseau affiché du Service** | Subnet A (`10.20.0.0/24`) | Subnet A | Subnet B (`192.168.1.0/24`) |
| **L'ancien Subnet A en base** | Présent (`scanner.networks`) | Présent | **Préservé** (marqué *Non connecté*, replié) |
| **Actifs du Subnet A** | `is_up = true` | `is_up` inchangé | **Préservés** dans l'inventaire historique avec leur `last_seen` |
| **Nouveau Subnet B** | Inexistant ou inactif | Inexistant ou inactif | **Créé / Activé**, hôtes scannés et cartographiés |
| **Historique des Scans** | Scans du réseau A archivés | Archivés | Scans du réseau A toujours consultables dans *Scan Archives* |

---

## 5. Maintenance et Nettoyage Optionnel

Si le passage sur le réseau A était purement temporaire (ex : audit ponctuel, démonstration) et que l'administrateur souhaite nettoyer les données associées :

1. **Suppression manuelle d'actifs :**
   * Rendez-vous dans **Gestion des Actifs**, filtrez par le sous-réseau ou l'organisation souhaitée, et utilisez l'action de suppression d'équipements obsolètes.
2. **Purger les services hors ligne :**
   * Dans la page **Services**, le bouton **« Purger les services hors ligne »** permet de retirer d'un clic les sondes inactives depuis plus de 48 heures.
3. **Purge automatique en base de données :**
   * Une maintenance automatique planifiée (`automated_db_maintenance_worker`) purge périodiquement les scans et services temporaires inactifs depuis plus de 90 jours.
