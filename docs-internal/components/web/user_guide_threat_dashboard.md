# Guide Utilisateur & Mode d'Emploi : Dashboard Menaces & Intégration SOC / SIEM

Ce guide s'adresse aux **analystes en cybersécurité**, **administrateurs systèmes** et **responsables SOC** utilisant la plateforme RTMS. Il détaille le fonctionnement, la lecture opérationnelle et la configuration du **Dashboard d'Exposition aux Menaces & Corrélation SOC/SIEM**.

---

## 1. Vue d'Ensemble & Philosophie Opérationnelle

Dans la plupart des organisations, la gestion des vulnérabilités (scans statiques) et la détection d'intrusions (SOC / SIEM) opèrent en silos isolés. Un serveur présentant 20 vulnérabilités peut n'être soumis à aucune attaque, tandis qu'un serveur critique présentant une seule vulnérabilité modérée peut faire l'objet de tentatives d'exploitation actives en temps réel.

Le moteur de corrélation de RTMS fusionne ces deux dimensions en temps réel :
- **Inventaire Scanné & CVEs** : Découvertes par les scanners RTMS et locales agents.
- **Télémétrie d'Attaque Live** : Provenant de votre infrastructure de détection (**Splunk**, **Wazuh**, **Suricata**, **Microsoft Sentinel**, **CrowdStrike Falcon**).

### Bénéfices Clés :
1. **Élimination de la fatigue d'alerte** : Priorisation des correctifs sur les machines et ports réellement attaqués.
2. **Score de Risque Contextuel Dynamique ($CRS$)** : Le score d'une vulnérabilité s'ajuste dynamiquement en fonction de la pression d'attaque réelle.
3. **Réaction immédiate** : Détection des incidents `ACTIVELY_EXPLOITED` nécessitant une remédiation d'urgence.

---

## 2. Navigation dans le Dashboard d'Exposition (`/vulnerabilities?tab=threats`)

Pour accéder au dashboard :
1. Dans le menu latéral gauche, cliquez sur **Vulnérabilités** (ou accédez à `/vulnerabilities`).
2. Dans la barre d'onglets supérieure, sélectionnez l'onglet **Menaces & SIEM** (icône radar / flamme).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CENTRE DE VULNÉRABILITÉS                        │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│ Vue d'ensemble  │ Vulnérabilités  │  Menaces & SIEM  │  Historique NVD │
└─────────────────┴─────────────────┴────────┬─────────┴─────────────────┘
                                             │
                                  [ Vous êtes ici ]
```

### A. Indicateurs Clés d'En-tête (KPIs)

En haut du dashboard, 4 cartes de synthèse synthétisent la posture globale :

* **Activité d'Attaque Active** : Nombre total d'événements de menaces ingérés sur la fenêtre glissante (dernières 24h à 48h).
* **CVEs Actuellement Exploitées (`ACTIVELY_EXPLOITED`)** : Nombre de vulnérabilités pour lesquelles une correspondance stricte d'IP et de port est activement ciblée.
* **Actifs Ciblés** : Nombre de serveurs ou hôtes internes ayant reçu du trafic malveillant identifié.
* **Fournisseur Télémétrie Actif** : Badge indiquant la source active (ex. *Wazuh*, *Splunk*, *Suricata*, *Sentinel*, *CrowdStrike*).

### B. Graphiques de Répartition & Télémétrie

1. **Top Services & Ports Ciblés** :
   - Présente les 10 ports les plus attaqués sur votre réseau (ex. `Port 443 HTTPS`, `Port 22 SSH`, `Port 3389 RDP`).
   - Affiche le volume de frappes (hits), les attaques actives et le niveau de criticité.
2. **Chronologie d'Activité sur 48h** :
   - Histogramme temporel découpé par tranches de 4 heures.
   - Permet de repérer les pics d'attaque, les scans automatisés ou le déclenchement d'une campagne malveillante ciblée.

### C. Tableau des Vulnérabilités Corrélées

Le tableau principal liste l'ensemble des vulnérabilités en les croisant avec la télémétrie :

| Colonne | Description |
| :--- | :--- |
| **CVE ID & Sévérité** | Identifiant CVE avec lien NIST et sévérité nominale (CRITICAL, HIGH, etc.). |
| **Actif / Hôte** | Nom d'hôte et adresse IP ciblée. |
| **Port / Service** | Port applicatif concerné (avec indicateur de correspondance avec l'attaque). |
| **Score Contextuel** | Note dynamique sur 10.0 calculée par le moteur RTMS. |
| **Statut de Menace** | Badge d'état opérationnel (`ACTIVELY_EXPLOITED`, `ATTACK_DETECTED`, etc.). |
| **Signatures & Télémétrie** | Règles SIEM / IDS déclenchées et nombre de frappes enregistrées. |
| **Actions** | Création d'incident de sécurité, analyse détaillée ou filtrage. |

---

## 3. Comprendre les Statuts de Menace & le Score de Risque

### Les 5 Niveaux de Menace

| Statut | Badge Visuel | Signification Opérationnelle | Action Requise |
| :--- | :--- | :--- | :--- |
| **`ACTIVELY_EXPLOITED`** | Rouge écarlate pulsant | **Urgence Absolue**. L'IP et le port précis de ce service vulnérable font l'objet d'attaques actives récentes (< 24h). | Confinement immédiat, isolation réseau ou application du patch d'urgence. |
| **`ATTACK_DETECTED`** | Ambre / Orange | L'adresse IP hôte est ciblée par des attaques, mais le port exact n'est pas ciblé ou il s'agit d'un balayage général. | Surveillance renforcée et vérification des règles de filtrage pare-feu. |
| **`TARGETED`** | Violet / Indigo | L'IP a fait l'objet de scans ou d'attaques dans les dernières 48h (reconnaissance / probing). | Planification de la remédiation lors du cycle standard. |
| **`POTENTIAL`** | Bleu | Vulnérabilité existante avec un score CVSS élevé, mais aucune attaque détectée sur cette IP. | Traitement préventif normal. |
| **`DORMANT`** | Gris | Vulnérabilité mineure sans activité hostile observée. | Surveillance de routine. |

### Calcul du Score de Risque Contextuel ($CRS$)

Le score contextuel démarre du score de base CVSS v3 et y ajoute des pénalités contextuelles :
- **Volume d'attaques** : Augmentation logarithmique en fonction du nombre de requêtes suspectes (jusqu'à $+2.0$).
- **Correspondance de Port** : $+1.5$ point si l'attaque vise précisément le port sur lequel tourne le logiciel vulnérable.
- **Sévérité de l'alerte SIEM** : Jusqu'à $+1.5$ point si le SIEM classe l'alerte en CRITICAL.
- **Récence de l'attaque** : $+1.0$ point si l'attaque a été vue dans les 24 dernières heures.
- **Plafond** : Le score total est strictement borné à **10.0**.

> **Exemple concret** : Une vulnérabilité OpenSSL avec un CVSS de base de **7.5 (HIGH)** sur un serveur web (port 443). Le SIEM détecte 450 requêtes malveillantes sur le port 443 dans les 6 dernières heures. Le score est recalculé à **10.0 (CRITICAL - ACTIVELY EXPLOITED)**.

---

## 4. Mode d'Emploi : Configuration des Fournisseurs SOC / SIEM

Pour configurer votre connexion SOC/SIEM :
1. Dans le menu latéral, cliquez sur **Configuration Scanner / Paramètres** (`/settings`).
2. Faites défiler jusqu'à la section **Intégration SOC & Télémétrie d'Attaque**.
3. Cochez la case **Activer la corrélation SOC / SIEM**.
4. Sélectionnez votre solution dans le menu déroulant.

---

### Option 1 : Splunk Enterprise / Splunk Cloud

Splunk interroge les journaux de sécurité et d'intrusion via l'API REST de recherche.

1. **Type de Fournisseur** : Sélectionnez `Splunk Enterprise / Cloud`.
2. **URL de l'API Splunk** : Saisissez l'URL d'accès HTTPS avec le port de gestion (par défaut `8089` pour Splunk Enterprise on-premise, ou le sous-domaine de recherche pour Splunk Cloud) :
   - Exemple : `https://splunk.corp.local:8089`
3. **Jeton d'Authentification (REST / HEC Token)** : Collez votre Bearer Token Splunk généré dans Splunk (*Settings > Tokens*).
4. **Vérification SSL** : Cochez cette case en production pour valider le certificat TLS de votre instance Splunk.
5. Cliquez sur **Tester la connexion Splunk**.
   - Si la connexion est réussie, un badge vert s'affiche avec la confirmation de communication.

---

### Option 2 : Wazuh / Elasticsearch / OpenSearch

Wazuh stocke ses alertes dans un cluster Elasticsearch ou OpenSearch (index `wazuh-alerts-*`).

1. **Type de Fournisseur** : Sélectionnez `Wazuh / Elasticsearch`.
2. **Hôte Wazuh / Elasticsearch** : Nom d'hôte ou adresse IP du nœud d'indexation (ex. `10.0.0.50` ou `wazuh-indexer.corp.local`).
3. **Port** : Port de l'API REST Elasticsearch (par défaut `9200`).
4. **Modèle d'Index** : Nom ou motif des index d'alertes (par défaut `wazuh-alerts-*`).
5. **Authentification** :
   - **Nom d'utilisateur & Mot de passe** (ex. `admin` / mot de passe wazuh indexer).
   - *OU* **Clé d'API Elasticsearch** si vous utilisez l'authentification par API Key.
6. **Activer SSL/TLS** : Cochez si votre cluster utilise HTTPS.
7. Cliquez sur **Tester la connexion Wazuh**.

---

### Option 3 : Suricata Local (Journal d'Alertes EVE JSON)

Idéal pour les déploiements souverains ou les sondes autonomes où Suricata est installé localement sur la même appliance ou partage un volume monté.

1. **Type de Fournisseur** : Sélectionnez `Suricata (Local EVE Log)`.
2. **Chemin du fichier EVE JSON** : Saisissez le chemin absolu vers le journal JSON d'alertes :
   - Chemin par défaut sous Linux : `/var/log/suricata/eve.json`
3. **Permissions requises** : L'utilisateur exécutant le service RTMS Web (`rtms` ou `www-data`) doit disposer des droits de lecture sur le fichier (`chmod 644 /var/log/suricata/eve.json` ou appartenance au groupe `suricata`).
4. Cliquez sur **Tester la connexion Suricata**.
   - Le système valide immédiatement l'existence du fichier, ses droits d'accès et sa taille.

---

### Option 4 : Microsoft Sentinel (Azure Log Analytics)

Microsoft Sentinel interroge les tables de sécurité cloud Azure via l'API REST Log Analytics et une authentification Entra ID (ex-Azure AD).

1. **Type de Fournisseur** : Sélectionnez `Microsoft Sentinel`.
2. **Workspace ID** : L'identifiant GUID de votre espace de travail Log Analytics (trouvable dans le portail Azure sous *Log Analytics workspaces > Overview*).
3. **Tenant ID (Directory ID)** : L'identifiant de votre tenant Azure Entra ID.
4. **Application (Client) ID** : L'ID de l'application inscrite (App Registration) dans Azure Entra ID.
5. **Client Secret** : La valeur du secret généré pour cette application.
6. **Table Cible** : Sélectionnez la table contenant vos alertes (par défaut `CommonSecurityLog`, ou `SecurityAlert`).
7. **Permissions Azure requises** : L'application doit posséder le rôle **Log Analytics Reader** sur le workspace ciblé.
8. Cliquez sur **Tester la connexion Sentinel**.
   - RTMS effectue une négociation de jeton OAuth2 avec `login.microsoftonline.com` puis exécute une requête KQL de test.

---

### Option 5 : CrowdStrike Falcon

CrowdStrike Falcon interroge le cloud Falcon via l'API OAuth2 pour récupérer les détections d'attaques et de comportements hostiles.

1. **Type de Fournisseur** : Sélectionnez `CrowdStrike Falcon`.
2. **Falcon API Client ID** : L'identifiant Client ID créé dans la console Falcon (*Support and resources > API clients and keys*).
3. **Falcon API Client Secret** : Le secret associé à la clé d'API.
4. **Falcon Cloud Base URL** : Sélectionnez la région correspondant à votre souscription CrowdStrike :
   - `api.crowdstrike.com` : Cloud US-1
   - `api.us-2.crowdstrike.com` : Cloud US-2
   - `api.eu-1.crowdstrike.com` : Cloud EU-1 (Francfort - Recommandé en Europe)
   - `api.laggar.gcw.crowdstrike.com` : GovCloud
5. **Permissions Falcon requises** : Portée (Scope) **Alerts** en lecture (`Alerts: Read`).
6. Cliquez sur **Tester la connexion CrowdStrike Falcon**.

---

## 5. Synchronisation de la Télémétrie

### Synchronisation Automatique
Lorsque l'intégration SOC est activée, RTMS synchronise la télémétrie en arrière-plan à intervalles réguliers (toutes les 15 minutes) et rafraîchit la table `admin.threat_telemetry_cache`.

### Synchronisation Manuelle à la Demande
Vous pouvez forcer une synchronisation immédiate à tout moment depuis le dashboard :
1. Rendez-vous sur `/vulnerabilities?tab=threats`.
2. En haut à droite du tableau, cliquez sur le bouton **Synchroniser la télémétrie** (icône de synchronisation).
3. Une notification vous confirme le nombre d'événements et de cibles d'attaques synchronisés dans le cache.

---

## 6. Playbook Opérationnel pour Analystes Sécurité

Lorsqu'une alerte ou un incident de type `ACTIVELY_EXPLOITED` apparaît dans le dashboard :

```
[ Détection ACTIVELY_EXPLOITED ]
               │
               ▼
   1. Vérifier l'Actif & le Port concerné
               │
               ▼
   2. Isoler le flux réseau suspect au pare-feu
               │
               ▼
   3. Créer un Incident dans RTMS ("Créer Incident")
               │
               ▼
   4. Appliquer le correctif de sécurité (Patch / Update)
               │
               ▼
   5. Déclencher un rescan RTMS & valider la résolution
```

1. **Vérification immédiate** :
   - Cliquez sur la ligne de la vulnérabilité pour consulter les signatures d'attaque et les adresses IP sources d'où proviennent les tentatives.
2. **Mesure d'endiguement rapide** :
   - Si le service n'a pas besoin d'être exposé publiquement, restreignez le port au pare-feu ou sur le groupe de sécurité.
3. **Création d'un Incident de Sécurité** :
   - Cliquez sur le bouton d'action **Créer Incident** sur la ligne correspondante. Un ticket est automatiquement ouvert dans le module de remédiation RTMS avec les détails de la CVE et de l'attaque.
4. **Vérification post-correctif** :
   - Après application du patch, lancez un scan ciblé depuis le menu **Scanneur**. Le statut basculera automatiquement à résolu.

---

## 7. Dépannage & FAQ

### Le test de connexion échoue avec "Connection refused"
- **Cause** : L'hôte ou le port spécifié n'est pas joignable depuis le serveur RTMS Web.
- **Résolution** :
  - Vérifiez les règles de pare-feu entre RTMS Web et votre serveur SOC.
  - Pour Wazuh, vérifiez que Elasticsearch écoute bien sur `0.0.0.0` ou l'IP du réseau interne et non uniquement sur `127.0.0.1`.

### Le test de connexion affiche "HTTP Error 401: Unauthorized"
- **Splunk** : Le jeton HEC / REST a expiré ou ne dispose pas du rôle `search`.
- **Wazuh** : Le mot de passe ou la clé d'API est incorrecte.
- **CrowdStrike** : Le Client ID ou Secret est erroné, ou la région cloud sélectionnée ne correspond pas à votre tenant.

### Le fichier Suricata `eve.json` indique "File does not exist or is not readable"
- **Cause** : Le chemin saisi est incorrect ou le serveur RTMS n'a pas les droits de lecture sur le journal.
- **Résolution** :
  - Exécutez sur le serveur : `ls -l /var/log/suricata/eve.json`.
  - Accordez les droits nécessaires : `chmod 644 /var/log/suricata/eve.json` ou ajoutez l'utilisateur au groupe `suricata`.

### Aucune attaque n'apparaît dans le dashboard alors que le test est réussi
- **Cause** : La fenêtre temporelle d'interrogation (48h par défaut) ne contient aucun événement ciblant les adresses IP présentes dans l'inventaire de vos actifs scannés.
- **Vérification** : Assurez-vous que vos sous-réseaux et machines sont bien scannés et enregistrés dans la section **Gestion des Actifs**.
