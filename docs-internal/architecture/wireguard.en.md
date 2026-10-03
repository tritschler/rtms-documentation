# Secure WireGuard VPN Infrastructure (Hub-and-Spoke Architecture)

This document details the complete configuration of a WireGuard Virtual Private Network (VPN) interconnecting a Mac workstation and a local Linux server (Home/Client) via a VPS acting as a central relay point (Bastion/Hub).

---

## 1. Network Architecture & Addressing Plan

The selected architecture follows a star topology (**Hub-and-Spoke**). The VPS has a static public IP address and forwards traffic between clients behind NAT routers or firewalls.

### IP Address Mapping
* **VPS (Hub):**
  * Public IP: `135.125.102.194`
  * VPN Private IP: `10.0.0.1`
* **Mac (Spoke 1):**
  * VPN Private IP: `10.0.0.2`
* **Linux Home - EndeavourOS (Spoke 2):**
  * VPN Private IP: `10.0.0.3`

---

## 2. Server Configuration (VPS - Ubuntu 24.04 / 26.04)

### 2.1. Installation and Initialization
Connect via SSH to the VPS and elevate to root (`sudo -i`).

```bash
# Update package list and install WireGuard tools
apt update && apt install -y wireguard

# Navigate to configuration directory and set strict permissions
cd /etc/wireguard
umask 077

# Generate server keys
wg genkey | tee server_private.key | wg pubkey > server_public.key
```

### 2.2. Enable IP Forwarding

The VPS must be permitted to route packets between network interfaces:

```bash
# Enable IPv4 forwarding permanently
echo "net.ipv4.ip_forward=1" | tee -a /etc/sysctl.conf

# Apply changes immediately
sysctl -p
```

### 2.3. Configuration File `/etc/wireguard/wg0.conf`

Create the server interface definition and authorized peer declarations:

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY_CONTENT>

# NAT and traffic forwarding routing rules
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ens3 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ens3 -j ACCEPT

### Peers Section ###

# Peer 1: Mac
[Peer]
PublicKey = <MAC_PUBLIC_KEY_CONTENT>
AllowedIPs = 10.0.0.2/32

# Peer 2: Linux Home (EndeavourOS)
[Peer]
PublicKey = h80EvWfEpnEre4gfPL2tzDEMbc2oowCDxdX5SjkLeDE=
AllowedIPs = 10.0.0.3/32
```

### 2.4. Service Management

```bash
# Enable and start WireGuard on boot
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
```

---

## 3. Client 1 Configuration (Mac - macOS)

### 3.1. Installation via CLI

```bash
# Install WireGuard CLI tools via Homebrew
brew install wireguard-tools

# Create configuration directory and restrict permissions
sudo mkdir -p /opt/homebrew/etc/wireguard
cd /opt/homebrew/etc/wireguard
```

### 3.2. Local Key Generation

```bash
# Generate Mac keys
wg genkey | tee mac_private.key | wg pubkey > mac_public.key
```

### 3.3. Configuration File `/opt/homebrew/etc/wireguard/wg0.conf`

```ini
[Interface]
Address = 10.0.0.2/24
PrivateKey = <MAC_PRIVATE_KEY_CONTENT>

[Peer]
PublicKey = kuFPoygzjrLTWhTlWZSi+VlGiQdH6fMIHU/+ph4I/UA=
Endpoint = 135.125.102.194:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```

```bash
# Secure configuration file permissions
sudo chmod 600 /opt/homebrew/etc/wireguard/wg0.conf
```

### 3.4. SSH Session Stabilization (KeepAlive)

To prevent idle SSH sessions over the tunnel from disconnecting, configure the local SSH client:

```bash
nano ~/.ssh/config
```

Add the following rules:

```text
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

---

## 4. Client 2 Configuration (Linux Home - EndeavourOS)

### 4.1. Installation and Kernel Management

On an Arch-based distribution (EndeavourOS), system updates may require a reboot to load updated kernel modules:

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

*Note: If `Unknown device type` or `Protocol not supported` appears, reboot to initialize the new kernel.*

### 4.2. Configuration File `/etc/wireguard/wg0.conf`

```ini
[Interface]
Address = 10.0.0.3/24
PrivateKey = <HOME_PRIVATE_KEY_CONTENT>

[Peer]
PublicKey = kuFPoygzjrLTWhTlWZSi+VlGiQdH6fMIHU/+ph4I/UA=
Endpoint = 135.125.102.194:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```

### 4.3. Startup and Persistence

```bash
# Enable and start the service permanently
systemctl enable --now wg-quick@wg0
```

### 4.4. Always-On Configuration (Disable Sleep & Suspend)

To maintain SSH server availability on a laptop, disable sleep triggers:

1. **Ignore laptop lid closure:**
```bash
nano /etc/systemd/logind.conf
```

Uncomment and set:
```text
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
```

Apply changes: `systemctl restart systemd-logind`

2. **Disable system sleep modes:**
```bash
systemctl mask systemd-suspend.service systemd-hibernate.service systemd-hybrid-sleep.service systemd-suspend-then-hibernate.service
```

---

## 5. Security & Hardening (VPS)

To hide the server from the public Internet, the **UFW** firewall denies public SSH (port 22) and restricts access strictly to authenticated machines inside the VPN tunnel.

### 5.1. UFW Rules on VPS

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

### 5.2. SSH Service Hardening (`/etc/ssh/sshd_config.d/00-security.conf`)

Enforce public key authentication and disable password logins:

```text
PasswordAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
```

Apply configuration: `sshd -t && systemctl restart ssh`

---

## 6. Diagnostic & Operational Commands

* **Check tunnel status (keys, handshakes, bytes transferred):**
```bash
sudo wg show
```

* **Hot-reload VPS configuration (without dropping sessions):**
```bash
sudo wg syncconf wg0 <(sudo wg-quick strip wg0)
```

* **Manual start/stop commands:**
```bash
sudo wg-quick up wg0
sudo wg-quick down wg0
```

* **End-to-end connectivity test (from Mac):**
```bash
ping 10.0.0.1          # Ping VPS
ping 10.0.0.3          # Ping Linux Home via VPS
ssh user@10.0.0.3      # Secure SSH connection
```
