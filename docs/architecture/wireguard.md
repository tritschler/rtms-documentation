Voici le contenu complet et détaillé de ton fichier `WireGuard.md`. Tu peux le copier-coller directement dans ton système de documentation.

```markdown
# Infrastructure VPN Sécurisée WireGuard (Architecture Hub-and-Spoke)

Ce document détaille la configuration complète d'un réseau privé virtuel (VPN) WireGuard permettant d'interconnecter un Mac (Poste de travail) et un serveur Linux local (Maison/Client) via un VPS faisant office de point de rebond central (Bastion/Hub).

---

## 1. Architecture Réseau & Plan d'Adressage

L'architecture retenue est une topologie en étoile (**Hub-and-Spoke**). Le VPS possède une IP publique fixe et redirige les flux entre les différents clients cachés derrière des routeurs ou pare-feux NAT.

### Cartographie des adresses IP
* **VPS (Hub) :** * IP Publique : `135.125.102.194`
  * IP VPN Privée : `10.0.0.1`
* **Mac (Spoke 1) :** * IP VPN Privée : `10.0.0.2`
* **Linux Maison - EndeavourOS (Spoke 2) :** * IP VPN Privée : `10.0.0.3`

---

## 2. Configuration du Serveur (VPS - Ubuntu 26.04)

### 2.1. Installation et initialisation
Connecte-toi en SSH sur le VPS et bascule en mode superutilisateur (`sudo -i`).

```bash
# Update package list and install WireGuard tools
apt update && apt install -y wireguard

# Navigate to configuration directory and set strict permissions
cd /etc/wireguard
umask 077

# Generate server keys
wg genkey | tee server_private.key | wg pubkey > server_public.key

```

### 2.2. Activation du routage IP (IP Forwarding)

Le VPS doit être autorisé à transférer les paquets réseau d'une interface à l'autre.

```bash
# Enable IPv4 forwarding permanently
echo "net.ipv4.ip_forward=1" | tee -a /etc/sysctl.conf

# Apply changes immediately
sysctl -p

```

### 2.3. Fichier de configuration `/etc/wireguard/wg0.conf`

Crée le fichier contenant la définition de l'interface réseau du serveur et les déclarations des clients autorisés (*Peers*) :

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <CONTENU_DE_SERVER_PRIVATE_KEY>

# NAT and traffic forwarding routing rules
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ens3 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ens3 -j ACCEPT

### Peers Section ###

# Peer 1: Mac
[Peer]
PublicKey = <CONTENU_DE_MAC_PUBLIC_KEY>
AllowedIPs = 10.0.0.2/32

# Peer 2: Linux Home (EndeavourOS)
[Peer]
PublicKey = h80EvWfEpnEre4gfPL2tzDEMbc2oowCDxdX5SjkLeDE=
AllowedIPs = 10.0.0.3/32

```

### 2.4. Gestion du service

```bash
# Enable and start WireGuard on boot
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

```

---

## 3. Configuration du Client 1 (Mac - macOS)

### 3.1. Installation via la ligne de commande

```bash
# Install WireGuard CLI tools via Homebrew
brew install wireguard-tools

# Create configuration directory and restrict permissions
sudo mkdir -p /opt/homebrew/etc/wireguard
cd /opt/homebrew/etc/wireguard

```

### 3.2. Génération des clés locales

```bash
# Generate Mac keys
wg genkey | tee mac_private.key | wg pubkey > mac_public.key

```

### 3.3. Fichier de configuration `/opt/homebrew/etc/wireguard/wg0.conf`

```ini
[Interface]
Address = 10.0.0.2/24
PrivateKey = <CONTENU_DE_MAC_PRIVATE_KEY>

[Peer]
PublicKey = kuFPoygzjrLTWhTlWZSi+VlGiQdH6fMIHU/+ph4I/UA=
Endpoint = 135.125.102.194:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25

```

```bash
# Secure the configuration file permissions
sudo chmod 600 /opt/homebrew/etc/wireguard/wg0.conf

```

### 3.4. Stabilisation des sessions SSH (KeepAlive)

Pour éviter que les connexions SSH vers le tunnel ne se coupent par inactivité, configure le client SSH local du Mac :

```bash
nano ~/.ssh/config

```

Ajoute ces règles :

```text
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3

```

---

## 4. Configuration du Client 2 (Linux Maison - EndeavourOS)

### 4.1. Installation et gestion du Kernel

Sur une distribution de type Arch (EndeavourOS), une mise à jour système simultanée peut nécessiter un redémarrage pour charger correctement les modules du noyau.

```bash
# Switch to root session to prevent permission denied errors
sudo -i
cd /etc/wireguard
umask 077

# Update repositories and install wireguard tools
pacman -Syu wireguard-tools

# Generate keys
wg genkey | tee home_private.key | wg pubkey > home_public.key

```

*Note: Si l'erreur `Unknown device type` ou `Protocol not supported` apparaît, effectue un `reboot` pour initialiser le nouveau noyau.*

### 4.2. Fichier de configuration `/etc/wireguard/wg0.conf`

```ini
[Interface]
Address = 10.0.0.3/24
PrivateKey = <CONTENU_DE_HOME_PRIVATE_KEY>

[Peer]
PublicKey = kuFPoygzjrLTWhTlWZSi+VlGiQdH6fMIHU/+ph4I/UA=
Endpoint = 135.125.102.194:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25

```

### 4.3. Lancement et persistance

```bash
# Enable and start the service permanently
systemctl enable --now wg-quick@wg0

```

### 4.4. Configuration "Always-On" (Empêcher la mise en veille)

Pour garantir la disponibilité du serveur SSH sur cet ordinateur portable, les mécanismes de mise en sommeil par inactivité ou fermeture de l'écran doivent être désactivés.

1. **Ignorer la fermeture de l'écran :**
```bash
nano /etc/systemd/logind.conf

```


Décommenter et modifier les directives suivantes :
```text
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore

```


Appliquer le changement : `systemctl restart systemd-logind`
2. **Désactiver la mise en veille système :**
```bash
systemctl mask systemd-suspend.service systemd-hibernate.service systemd-hybrid-sleep.service systemd-suspend-then-hibernate.service

```



---

## 5. Sécurisation et Durcissement (Hardening du VPS)

Pour masquer complètement le serveur de l'Internet public, le pare-feu **UFW** bloque tout accès direct au port SSH (22) traditionnel et restreint l'écoute aux seules machines authentifiées au sein du VPN.

### 5.1. Configuration des règles UFW sur le VPS

```bash
# Reset UFW to default settings
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Open WireGuard communication port to the public Internet
ufw allow 51820/udp

# Strictly allow SSH traffic ONLY from the VPN internal subnet
ufw allow from 10.0.0.0/24 to any port 22 proto tcp

# Enable the firewall
ufw enable

```

### 5.2. Verrouillage du service SSH (`/etc/ssh/sshd_config.d/00-security.conf`)

Pour interdire l'usage des mots de passe au profit exclusif des clés SSH :

```text
PasswordAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
PermitRootLogin no

```

Appliquer les modifications : `sshd -t && systemctl restart ssh`

---

## 6. Commandes de Diagnostic et d'Exploitation

* **Vérifier l'état du tunnel (Clés, handshakes, transferts) :**
```bash
sudo wg show

```


* **Recharger la configuration du VPS à chaud (sans coupure) :**
```bash
sudo wg syncconf wg0 <(sudo wg-quick strip wg0)

```


* **Commandes d'arrêt/relance manuelles :**
```bash
sudo wg-quick up wg0
sudo wg-quick down wg0

```


* **Test de connectivité direct de bout en bout (depuis le Mac) :**
```bash
ping 10.0.0.1  # Ping vers le VPS
ping 10.0.0.3  # Ping vers le Linux Maison via le VPS
ssh utilisateur@10.0.0.3  # Connexion SSH sécurisée

```



```

```