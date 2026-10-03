# CURL commands

# send standard HTTP GET
curl -L https://3tsconsulting.be          # renvoie le contenu complet de la page
curl -I -L https://3tsconsulting.be

### 2. Inspection des en-têtes (Headers)

Pour vérifier les codes d'état (comme le 200 OK) sans télécharger tout le contenu :
curl -I -L https://3tsconsulting.be

### 3. Mode verbeux (Debug)
curl -v -L https://3tsconsulting.be

### 4. Test de l'API REST WordPress

Pour vérifier si l'API JSON de votre site est active et accessible :
curl -I -L https://3tsconsulting.be/wp-json/

### 5. Affichage du contenu JSON de l'API
Pour récupérer et afficher les données JSON brutes de WordPress :
curl -L https://3tsconsulting.be/wp-json/

*Note : L'option `-L` a été systématiquement recommandée pour s'assurer que curl suive les redirections (par exemple de HTTP vers HTTPS ou de non-www vers www).*


###### -------- Direct URLs for PHP WP admin

https://3ts-cybersecurity.be/wp-admin/profile.php

Voici une compilation des liens directs (URLs) pour administrer votre site **3ts-cybersecurity.be**.

Ces liens sont des "raccourcis" qui contournent les menus masqués par le plugin *WP Clean Admin Menu*.
**Note :** Vous devez être déjà connecté à votre site pour que ces liens fonctionnent.

### Urgence & Déblocage (Prioritaire)

C'est ici que vous pouvez désactiver les plugins qui vous cachent la vue.

* **Gestion des Plugins (Pour désactiver "WP Clean Admin Menu") :**
`https://3ts-cybersecurity.be/wp-admin/plugins.php`
* **Mises à jour (Vérifier l'état de santé réel) :**
`https://3ts-cybersecurity.be/wp-admin/update-core.php`

### Oshine & Tatsu (Licences & Options)

Si le menu est caché, ces liens devraient vous amener directement dans les entrailles du thème.

* **Accueil Oshine (Souvent là où est la licence) :**
`https://3ts-cybersecurity.be/wp-admin/admin.php?page=oshine`
* **Options du Thème (Couleurs, logos, header) :**
`https://3ts-cybersecurity.be/wp-admin/admin.php?page=oshine_options`
* **Tableau de bord Tatsu :**
`https://3ts-cybersecurity.be/wp-admin/admin.php?page=tatsu`

### Votre Compte

* **Changer votre mot de passe / Email :**
`https://3ts-cybersecurity.be/wp-admin/profile.php`

### Réglages Généraux WordPress

* **Réglages Généraux (Titre du site, URL) :**
`https://3ts-cybersecurity.be/wp-admin/options-general.php`
* **Gestion des Menus (Barre de navigation) :**
`https://3ts-cybersecurity.be/wp-admin/nav-menus.php`
* **Gestion des Pages (Toutes vos pages) :**
`https://3ts-cybersecurity.be/wp-admin/edit.php?post_type=page`

### Plugins Spécifiques (vus dans votre liste)

* **Réglages Wordfence (Sécurité) :**
`https://3ts-cybersecurity.be/wp-admin/admin.php?page=Wordfence`
* **Sauvegardes UpdraftPlus :**
`https://3ts-cybersecurity.be/wp-admin/options-general.php?page=updraftplus`

**Astuce :** Je vous conseille de garder cette liste ou de mettre en favori le lien **Plugins** (`.../plugins.php`) car c'est la clé pour reprendre le contrôle si un prestataire vous masque à nouveau les menus.