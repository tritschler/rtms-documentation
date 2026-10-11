# Guide Utilisateur : Thèmes & Personnalisation CSS (Style Entreprise)

Ce guide s'adresse aux **administrateurs** et **utilisateurs** de la plateforme RTMS souhaitant adapter l'apparence visuelle, les couleurs et la charte graphique de la console web aux couleurs de leur entreprise.

---

## 1. Accéder aux paramètres du thème

1. Connectez-vous à la console RTMS avec un compte possédant le rôle **Administrateur** (`admin` ou `superadmin`).
2. Dans le menu de navigation latéral gauche, cliquez sur **Configuration** (ou accédez à l'URL `/scanner`).
3. Faites défiler la page vers le bas jusqu'au bloc :
   > 🎨 **Style CSS & Thème Entreprise**
4. Cliquez sur l'en-tête du bloc pour dérouler les options de personnalisation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎨 Style CSS & Thème Entreprise                         [ Thème Actif ] ▾ │
│    Personnalisez l'apparence visuelle, les couleurs et la feuille de style  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Méthode 1 : Appliquer un thème pré-configuré en 1 clic (Recommandé)

Pour tester ou adopter immédiatement une ambiance visuelle différente du thème standard RTMS, 3 thèmes exclusifs à fort contraste sont directement intégrés :

| Thème | Bouton | Ambiance Visuelle |
| :--- | :---: | :--- |
| **Emerald Cyber** | 🟢 | Vert émeraude électrique (`#10b981`), surfaces sombre forêt/obsidienne (`#06120e`), boutons en dégradé émeraude et barres de défilement stylisées. |
| **Royal Purple** | 🟣 | Violet SOC high-tech (`#8b5cf6`), noir violacé profond (`#0c0a17`) et reflets lilas pour une ambiance salle de contrôle. |
| **Cyber Gold** | 🟡 | Or ambré chaleureux (`#f59e0b`), surfaces carbone (`#120e06`) et bordures dorées pour une esthétique executive. |

### Comment l'appliquer :
1. Cliquez simplement sur l'un des boutons (ex. **🟢 Emerald Cyber**).
2. L'aperçu s'applique **instantanément à tout votre écran** en temps réel.
3. Si le résultat vous plaît, cliquez sur le bouton bleu **"Enregistrer le thème"** en bas à droite pour le déployer à tous les utilisateurs.
4. Si vous souhaitez annuler, cliquez sur **"Annuler aperçu"**.

---

## 3. Méthode 2 : Personnalisation rapide (Palette & Typographie)

Vous pouvez ajuster rapidement vos couleurs sans taper une seule ligne de code :

1. **Couleur d'accentuation principale (`--accent-primary`)** :
   - Cliquez sur la vignette de couleur pour ouvrir le nuancier, ou saisissez directement votre code hexadécimal (ex: `#10b981`).
   - Cette couleur colore les boutons principaux, les onglets actifs et les indicateurs clés.
2. **Couleur d'accentuation secondaire (`--accent-secondary`)** :
   - Détermine la teinte des badges discrets et des effets de survol.
3. **Famille de police** :
   - Sélectionnez votre police dans le menu déroulant :
     - *Par défaut (Inter / Outfit)*
     - *Système moderne (Apple / Windows)*
     - *Inter (Moderne & Lisible)*
     - *Outfit (Design Épuré)*
     - *Roboto*
     - *JetBrains Mono (Console / Tech)*

Cliquez sur **"Tester / Prévisualiser en direct"** pour observer le rendu, puis sur **"Enregistrer le thème"**.

---

## 4. Méthode 3 : Import ou Écriture de CSS Personnalisé (Avancé)

Pour les équipes souhaitant une intégration sur mesure (white-labeling complet, polices d'entreprise, redéfinition des cartes) :

### Importer un fichier `.css`
1. Cliquez sur le bouton **"Importer .css"** (icône upload).
2. Sélectionnez votre fichier de style (par exemple le fichier fourni `example-corporate-theme.css`).
3. Le contenu est instantanément chargé dans l'éditeur.
4. Activez l'interrupteur **"Activer le style CSS personnalisé"**.

### Variables CSS courantes :
Vous pouvez surcharger ces variables dans votre bloc `:root` :

```css
:root {
  --accent-primary: #10b981 !important;    /* Couleur d'action principale */
  --accent-secondary: #34d399 !important;  /* Nuance secondaire */
  --bg-primary: #06120e !important;        /* Fond général de la page */
  --bg-secondary: #0b1e17 !important;      /* Fond des panneaux et cartes */
  --glass-bg: rgba(11, 30, 23, 0.85) !important; /* Fond semi-transparent */
  --border-color: rgba(52, 211, 153, 0.22) !important; /* Bordures */
  --radius-md: 10px !important;            /* Arrondi des angles */
}
```

Cliquez sur **"Tester / Prévisualiser en direct"** pour tester vos règles, puis sur **"Enregistrer le thème"**.

---

## 5. Rétablir le style RTMS par défaut

Si vous souhaitez revenir au style d'origine de RTMS (bleu roi et slate sombre) :
1. Dans la section **Style CSS & Thème Entreprise**, cliquez sur le bouton rouge **"Rétablir par défaut"**.
2. Confirmez la boîte de dialogue.
3. L'ensemble des styles personnalisés est supprimé et l'apparence standard est immédiatement restaurée.

---

## 6. Mode Sans Échec de Secours (Bypass d'Urgence)

> [!WARNING]
> **Que faire si une règle CSS personnalisée masque les boutons ou rend la navigation impossible ?**

Un **Mode Sans Échec** d'urgence est nativement prévu pour vous permettre de reprendre le contrôle à tout moment :

1. Dans la barre d'adresse de votre navigateur, ajoutez simplement `?safe_mode=true` à la fin de l'URL de RTMS.  
   *Exemple :* `http://rtms.local:8000/scanner?safe_mode=true`
2. Appuyez sur **Entrée**.
3. Tout le CSS personnalisé est immédiatement désactivé pour votre session, et un bandeau d'alerte jaune apparaît en haut à droite.
4. Rendez-vous dans la section de configuration pour corriger votre feuille de style ou cliquer sur **"Rétablir par défaut"**.
