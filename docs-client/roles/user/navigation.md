# Prise en Main & Navigation dans l'Interface

Ce guide s'adresse aux utilisateurs et opérateurs réseau prenant en main la console web **RTMS**.

---

## 1. Organisation de l'Espace de Travail

La console RTMS est organisée en trois zones principales :

```
┌────────────────────────────────────────────────────────────────────────┐
│ [🏢 Tenant / Plan]    [🔍 Recherche Cmd+K]   [⚙️]  [🌐 FR]  [🌙]  [👤 Profil]│
├─────────────┬──────────────────────────────────────────────────────────┤
│ 📊 Dashboard│                                                          │
│ 🖥️ Actifs   │                                                          │
│ ⚠️ Alertes   │                    ZONE DE TRAVAIL                       │
│ 🛡️ Menaces   │                 (Tableaux, Graphiques,                   │
│ 📋 Conformité│                  Détails des Équipements)                │
│ ⚙️ Admin     │                                                          │
│ 📖 Docs      │                                                          │
└─────────────┴──────────────────────────────────────────────────────────┘
```

1. **Barre Supérieure (Header)** :
   * **Recherche Globale Magique (🔍)** :
     * **Comportement interactif** : Présente sous la forme d'une loupe discrète qui s'agrandit avec animation au clic ou via le raccourci global **`Cmd + K`** (macOS) / **`Ctrl + K`** (Windows/Linux).
     * **Recherche d'actifs** : Tapez une adresse IP (complète ou partielle), un nom d'hôte (*hostname*), une adresse MAC, un fabricant matériel (*Cisco*, *Dell*, *Apple*...) ou un système d'exploitation.
     * **Raccourcis de navigation instantanés** : Tapez un mot-clé pour être guidé directement vers un module (ex : *"alerte"* $\rightarrow$ Alertes, *"cve"* $\rightarrow$ Vulnérabilités, *"triage"* $\rightarrow$ Menaces, *"user"* $\rightarrow$ Utilisateurs, *"sonde"* $\rightarrow$ Configuration réseau).
     * **Validation par `Entrée`** : Redirige directement vers l'inventaire complet (`/assets`) avec le filtre de recherche pré-appliqué.
     * **Fermeture rapide** : Appuyez sur **`Échap`** ou cliquez en dehors du pop-up pour replier le champ.
   * **Raccourci Paramètres (⚙️)** : Permet d'accéder directement à la configuration des sondes réseau et de l'environnement RTMS.
   * **Organisation & Licence** : Rappel du tenant client actif et du niveau de plan souscrit.
   * **Sélecteur de Langue** : Bascule instantanée de l'interface et de la documentation (Français, Anglais, Néerlandais, Allemand).
   * **Sélecteur de Thème** : Bascule instantanée entre le **Mode Sombre** (recommandé pour les centres d'opérations SOC) et le **Mode Clair (Daylight)**.
   * **Menu Profil & Déconnexion** : Informations sur le compte connecté, gestion du mot de passe et du second facteur MFA (TOTP).

2. **Barre de Navigation Latérale (Sidebar Dynamique)** :
   * Le contenu de la barre latérale est **entièrement dynamique** et s'adapte en temps réel selon deux critères :
     1. Le **type de licence souscrite** (modules et options activés pour votre organisation).
     2. Votre **rôle RBAC** (`admin`, `analyst`, `auditor`, `user`), masquant automatiquement les fonctions non autorisées selon le principe du moindre privilège.

3. **Zone de Travail Principale** :
   * Affiche les listes interactives, les fiches techniques des actifs et les graphiques d'analyse de risque.

---

## 2. Tableaux Interactifs & Filtres

Tous les tableaux de la suite RTMS partagent des fonctionnalités avancées :
* **Tri Multi-Colonnes** : Cliquez sur les en-têtes de colonnes (ex : Dernière vue, Criticité, Adresse IP) pour ordonner les données.
* **Filtres Rapides par Statut** : Filtrez en un clic les équipements actifs (`En ligne`), hors-ligne, ou présentant des vulnérabilités critiques.
* **Pagination & Densité d'Affichage** : Choisissez d'afficher 10, 25, 50 ou 100 lignes par page pour un confort de lecture optimal.
