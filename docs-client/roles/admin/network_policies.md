# Politiques Réseau, Sous-Réseaux & Deep Scan

Ce module permet de définir les règles de sécurité opérationnelle pour chaque sous-réseau découvert par RTMS.

---

## 1. Nommage & Description des Sous-Réseaux

Chaque plage CIDR découverte automatiquement (ex: `10.20.0.0/24`) peut être qualifiée par l'administrateur :
* **Nom convivial** : Ex : *VLAN 20 - Serveurs Applicatifs*, *VLAN 50 - Wi-Fi Invités*, *VLAN 100 - Automates Industriels OT*.
* **Description & Site géographique** : Informations utiles pour la contextualisation des incidents par les analystes SOC.

---

## 2. Règle du Double Consentement Strict (Dual Opt-In) pour le Deep Scan

Afin d'éviter tout incident sur des équipements délicats (automates programmables PLC, matériel médical, robots de tri) :

```mermaid
flowchart TD
    A[Hôte découvert sur le réseau] --> B{1. Switch Global Deep Scan actif ?}
    B -- Non --> E[Découverte Douce Uniquement (ARP/ICMP/MAC)]
    B -- Oui --> C{2. Sous-réseau explicitement configuré en Deep Scan ?}
    C -- Non (par défaut) --> E
    C -- Oui --> D{3. Actif individuel exclu ?}
    D -- Oui --> E
    D -- Non --> F[Deep Scan Autorisé : Nmap + Plugins Sécurité]
```

* **Sécurité par Défaut (`deep_scan = false`)** : Tout nouveau sous-réseau découvert n'est **jamais audité en profondeur** tant que l'administrateur ne l'a pas expressément activé.
* **Exclusion par Équipement** : Même sur un sous-réseau où le Deep Scan est actif, un serveur critique ou un automate peut être protégé en cochant l'option *« Exclure du Deep Scan »* sur sa fiche.

---

## 3. Listes Blanches d'Adresses MAC (Whitelist)

Pour les réseaux à forte rotation d'équipements légitimes ou les environnements de test :
* L'administrateur peut enregistrer des adresses MAC reconnues pour chaque plage CIDR.
* Les équipements whitelistés n'émettent pas d'alerte `NEW_HOST`, permettant de focaliser l'attention de l'équipe sécurité sur les véritables anomalies.
