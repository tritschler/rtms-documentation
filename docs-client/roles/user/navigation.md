# Prise en Main & Navigation dans l'Interface

Ce guide s'adresse aux utilisateurs et opérateurs réseau prenant en main la console web **RTMS**.

---

## 1. Organisation de l'Espace de Travail

La console RTMS est organisée en trois zones principales :

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Logo 3TS RTMS]       Recherche Globale (IP, Host, MAC...)     [Profil]│
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
   * **Recherche Globale Instantanée** : Filtrez à tout moment par adresse IP, nom d'hôte, constructeur ou adresse MAC.
   * **Sélecteur de Thème** : Basculez entre le mode sombre (recommandé pour les centres d'opérations SOC) et le mode clair.
   * **Sélecteur de Langue** : Basculez instantanément l'interface et la documentation entre le Français et l'Anglais.
   * **Menu Profil & Déconnexion** : Informations sur votre compte et rôle actif.

2. **Barre de Navigation Latérale** :
   * Permet d'accéder d'un clic aux modules d'inventaire, aux alertes de sécurité, aux tableaux de bord NIS2 et à la configuration.

3. **Zone de Travail Principale** :
   * Affiche les listes interactives, les fiches techniques des actifs et les graphiques d'analyse de risque.

---

## 2. Tableaux Interactifs & Filtres

Tous les tableaux de la suite RTMS partagent des fonctionnalités avancées :
* **Tri Multi-Colonnes** : Cliquez sur les en-têtes de colonnes (ex : Dernière vue, Criticité, Adresse IP) pour ordonner les données.
* **Filtres Rapides par Statut** : Filtrez en un clic les équipements actifs (`En ligne`), hors-ligne, ou présentant des vulnérabilités critiques.
* **Pagination & Densité d'Affichage** : Choisissez d'afficher 10, 25, 50 ou 100 lignes par page pour un confort de lecture optimal.
