# Gestion du Parc de Sondes (Scanners)

Le panneau **Statut des Services & Sondes** (`/admin/services` ou modale **Services Status**) centralise le pilotage de l'ensemble de vos sondes de détection réseau réparties sur vos différents sites.

---

## 1. Vue d'Ensemble & Battement de Cœur (Heartbeat)

Chaque sonde RTMS déployée dans votre infrastructure transmet périodiquement un battement de cœur chiffré vers le serveur web :
* **Identifiant & Nom de Sonde** : Nom attribué à la sonde (ex: `rtms-scanner-hq`, `rtms-scanner-branch01`).
* **Adresse IP & Sous-réseaux Audités** : Interfaces réseau actives surveillées par la sonde.
* **Version Logicielle** : Permet de vérifier l'homogénéité du parc et les mises à jour nécessaires.
* **État de Santé** : `ACTIF`, `STANDBY` (haute disponibilité / leader élection), ou `INJOIGNABLE`.

---

## 2. Gestion des Jetons d'Accès (Scanner Tokens)

Pour s'authentifier auprès de l'API RTMS en toute sécurité sans mot de passe en clair :
* **Génération de Tokens Bearer** : Création de clés d'API dédiées pour chaque sonde.
* **Sécurité & Hachage** : Les tokens sont stockés sous forme d'empreinte SHA-256 dans la base de données.
* **Durée de Validité Stricte** : Validité maximale de **365 jours (1 an)**.
* **Révocation Instantanée** : En cas de compromission suspectée ou de retrait d'une sonde physique, l'administrateur peut révoquer son token en un clic.

---

## 3. Politiques Réseau par Sonde (Wi-Fi vs Ethernet)

Pour chaque sonde, l'administrateur peut affiner les médias réseau autorisés :
* **Interdiction du Wi-Fi** : La sonde n'audite que les interfaces câblées Ethernet (idéal pour les serveurs en baie informatique).
* **Mode Sonde Nomade Wi-Fi** : Désactivation d'Ethernet et activation exclusive du Wi-Fi pour auditer la couverture sans-fil de bureaux.
* **Priorité Stricte Ethernet** : En cas de présence conjointe sur un même sous-réseau, Ethernet prévaut systématiquement pour éviter toute saturation radio inutile.
