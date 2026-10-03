# Journal d'Audit & Exportation des Rapports

Le module d'audit de RTMS garantit une traçabilité immuable de l'ensemble des activités système et offre des capacités d'exportation conformes aux exigences des régulateurs.

---

## 1. Registre d'Audit Immuable

Toutes les actions sensibles réalisées sur la plateforme sont consignées dans un journal d'audit append-only :
* **Authentification & Connexions** : Tentatives réussies et échouées, adresse IP source, mécanisme utilisé (Local, LDAP, SSO Keycloak) et horodatage UTC précis.
* **Modifications d'Actifs & Triage** : Tout changement de statut d'une vulnérabilité (ex: passage en faux-positif ou risque accepté) enregistre l'auteur, l'heure et la justification fournie.
* **Changements de Configuration** : Ajout ou suppression de sous-réseaux, modification de politiques de scan, création ou révocation de tokens de sondes.

---

## 2. Génération & Exportation de Rapports

Les auditeurs peuvent exporter à tout moment les éléments de preuve nécessaires à leurs revues :
* **Rapport Global d'Inventaire (CSV / Excel)** : Cartographie complète des actifs, adresses MAC, constructeurs, OS et services exposés.
* **Synthèse des Vulnérabilités & État du Parc (PDF)** : Document exécutif synthétisant les niveaux de risque, la répartition CVSS et les actions de remédiation en cours.
* **Rapport de Conformité NIS2** : Bilan officiel de conformité point par point avec les exigences des articles 21 et 23 de la directive européenne.
