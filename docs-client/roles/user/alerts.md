# Flux & Suivi des Alertes Réseau

Le module **Alertes** (`/alerts`) répertorie en temps réel tous les événements remarquables et anomalies détectés sur vos réseaux.

---

## 1. Types d'Alertes Courantes

| Type d'Alerte | Sévérité | Description | Action Recommandée |
| :--- | :---: | :--- | :--- |
| `NEW_HOST` | 🟡 Information | Un nouvel équipement inconnu vient d'apparaître sur le réseau. | Vérifier s'il s'agit d'un matériel légitime ou d'un branchement non autorisé (Shadow IT). |
| `IP_MAC_CONFLICT` | 🟠 Moyenne | Une adresse IP est revendiquée par une nouvelle adresse MAC. | Vérifier la présence d'un conflit d'IP statique ou d'un changement de carte réseau. |
| `HOST_DOWN` | 🔵 Faible | Un équipement précédemment actif ne répond plus aux sondes. | Contrôler si l'arrêt est planifié ou s'il s'agit d'une panne inopinée. |
| `ARP_SPOOFING_GATEWAY` | 🔴 Critique | Tentative d'usurpation de la passerelle par empoisonnement de table ARP (Attaque Man-in-the-Middle). | Isoler immédiatement le port réseau de l'équipement fautif et alerter l'équipe SOC. |

---

## 2. Acquittement et Filtrage des Alertes

* **Filtrage par Sévérité** : Isolez instantanément les alertes prioritaires (`Critique`, `Haute`) pour traiter les urgences de sécurité.
* **Acquittement** : Marquez les alertes légitimes ou traitées comme *Acquittées* pour conserver un journal clair des anomalies restant à résoudre.
* **Notification Multi-Canaux** : Selon les réglages effectués par votre administrateur, ces alertes peuvent également vous être relayées par email, Microsoft Teams ou Slack.
