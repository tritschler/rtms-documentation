# Configuration du Pare-feu (Firewall) pour l'Agent Local

> [!NOTE]
> **En mode `push` (mode par défaut et recommandé) : AUCUN PORT ENTRANT N'EST REQUIS.**
> L'agent communique exclusivement par requêtes sortantes vers le serveur central RTMS (`POST /api/agent/telemetry`). Vous n'avez pas besoin d'ouvrir de port entrant sur vos endpoints.
>
> Les instructions ci-dessous concernent uniquement le mode **`pull`** ou **`hybrid`**, dans lequel l'agent écoute sur le port `12000` (TCP) pour être interrogé directement par le Scanner RTMS.

Pour permettre l'accès au port `12000` (TCP) en mode Pull/Hybrid, voici les commandes pour les 4 principaux outils de gestion de pare-feu sous Linux :

## 1. UFW (Uncomplicated Firewall)
UFW est le pare-feu par défaut sur de nombreuses distributions basées sur Debian (comme Ubuntu).

```bash
# Ouvrir le port 12000
sudo ufw allow 12000/tcp

# Vérifier le statut
sudo ufw status
```

## 2. Firewalld
Firewalld est souvent utilisé sur CentOS, RHEL, Fedora, et Rocky Linux.

```bash
# Ouvrir le port 12000 de manière permanente
sudo firewall-cmd --zone=public --add-port=12000/tcp --permanent

# Recharger la configuration pour appliquer les changements
sudo firewall-cmd --reload
```

## 3. iptables
L'outil de pare-feu traditionnel, encore présent ou utilisé en sous-couche sur beaucoup de systèmes.

```bash
# Ajouter une règle pour accepter les connexions entrantes sur le port 12000
sudo iptables -A INPUT -p tcp --dport 12000 -j ACCEPT

# Sauvegarder la règle (la commande dépend de votre distribution)
# Sur Debian/Ubuntu avec iptables-persistent :
sudo netfilter-persistent save

# Sur RHEL/CentOS :
sudo service iptables save
```

## 4. nftables
Le successeur moderne d'iptables.

```bash
# Ajouter la règle pour accepter le port 12000 
# (Suppose que vous avez une table 'inet filter' et une chaîne 'input')
sudo nft add rule inet filter input tcp dport 12000 accept

# Sauvegarder la configuration de manière permanente
sudo sh -c 'nft list ruleset > /etc/nftables.conf'
```
