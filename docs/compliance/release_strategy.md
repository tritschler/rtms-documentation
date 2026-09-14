# Stratégie de Release et de Maintenance - Suite RTMS

**Projet :** Scanner de vulnérabilités et suite d'analyse réseau (RTMS)
**Organisation :** 3TS Cybersecurity
**Stack Technologique Principale :** Python, React, Nginx

---

## 1. Philosophie et Principes Fondamentaux

L'objectif de cette stratégie est de garantir la stabilité et la sécurité du scanner réseau RTMS tout en intégrant de nouvelles fonctionnalités de manière prévisible. 

Étant donné que les composants du stack (Python, React, Nginx) ont des cycles de vie asynchrones, les releases de RTMS sont volontairement **désynchronisées des sorties officielles** de ces technologies pour privilégier l'intégration de versions matures.

*   **Python :** Sortie majeure annuelle en octobre. Intégration dans RTMS différée à la version patch `.1` ou `.2` (généralement au premier trimestre de l'année suivante) pour éviter les instabilités initiales.
*   **Nginx :** Mise à jour de la branche stable au printemps.
*   **React :** Mises à jour mineures intégrées en continu (rétrocompatibles).

---

## 2. Calendrier de Déploiement Annuel

Le cycle de vie de la suite RTMS est rythmé par deux fenêtres de release majeures par an, complétées par des correctifs asynchrones.

### Release de Printemps (Mars / Avril) : "Tech & Features"
Cette release est axée sur la mise à niveau du socle technologique et les refontes structurelles.

*   **Actions clés :**
    *   Adoption de la dernière version majeure de Python (sortie en octobre de l'année précédente, désormais stabilisée).
    *   Mise à jour vers la dernière branche stable de Nginx.
    *   Mises à jour majeures des dépendances React.
    *   Déploiement de nouvelles fonctionnalités d'analyse réseau.
*   **Impact :** Peut inclure des changements cassants (Breaking Changes) nécessitant une version majeure.

### Release d'Automne (Octobre / Novembre) : "Features & Consolidation"
Cette release est axée sur la valeur métier et l'optimisation, ignorant volontairement la toute nouvelle version majeure de Python qui vient de sortir.

*   **Actions clés :**
    *   Déploiement des nouvelles fonctionnalités métier de l'interface React et des scripts Python.
    *   Amélioration des performances de scan et d'analyse.
    *   Stabilisation globale du code.
*   **Impact :** Release mineure, rétrocompatible.

---

## 3. Gestion des Hotfixes (Asynchrone)

La sécurité et la stabilité du scanner ne peuvent pas attendre les fenêtres de release biannuelles. Les hotfixes sont déployés de manière asynchrone via des pipelines CI/CD.

*   **Bugs applicatifs :** Création d'une branche `hotfix/*` depuis la branche de production. Correction, tests isolés, et déploiement immédiat.
*   **Vulnérabilités de sécurité (CVE) :** 
    *   Surveillance automatisée des librairies Python et Node.js.
    *   En cas de faille critique dans une dépendance, une mise à jour de sécurité est forcée et déployée sous forme de patch de version, sans aucune modification fonctionnelle.

---

## 4. Convention de Versioning (Semantic Versioning)

Le projet RTMS adopte le format `Majeure.Mineure.Patch` (ex: `2.1.3`).

*   **Majeure (ex: 2.0.0) :** Modification du socle technologique (changement de version Python) ou changements cassants dans l'API. Généralement associée à la release de Printemps.
*   **Mineure (ex: 1.3.0) :** Ajout de nouvelles fonctionnalités au scanner, de manière rétrocompatible. Généralement associée à la release d'Automne.
*   **Patch (ex: 1.2.4) :** Réservé exclusivement aux hotfixes et aux correctifs de sécurité (CVE). Zéro nouvelle fonctionnalité.
