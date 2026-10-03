# Firewall Configuration for RTMS Local Agent

> [!NOTE]
> **In `push` mode (default and recommended): ZERO INBOUND PORTS ARE REQUIRED.**
> The agent communicates exclusively via outbound HTTPS requests to the central RTMS Web server (`POST /api/agent/telemetry`). You do not need to open any inbound firewall ports on monitored endpoints.
>
> The configuration instructions below apply exclusively to **`pull`** or **`hybrid`** modes, where the agent listens on port `12000` (TCP) for direct queries from the RTMS Scanner.

To allow inbound access to port `12000` (TCP) in Pull/Hybrid mode:

## 1. UFW (Uncomplicated Firewall)
Default firewall on Debian and Ubuntu distributions:

```bash
# Allow TCP port 12000
sudo ufw allow 12000/tcp

# Check firewall status
sudo ufw status
```

## 2. Firewalld
Standard on CentOS, RHEL, Fedora, and Rocky Linux:

```bash
# Allow TCP port 12000 permanently
sudo firewall-cmd --zone=public --add-port=12000/tcp --permanent

# Reload firewall configuration
sudo firewall-cmd --reload
```

## 3. iptables
Legacy netfilter firewall:

```bash
# Append rule accepting inbound TCP on port 12000
sudo iptables -A INPUT -p tcp --dport 12000 -j ACCEPT

# Persist rule across reboots
# Debian/Ubuntu with iptables-persistent:
sudo netfilter-persistent save

# RHEL/CentOS:
sudo service iptables save
```

## 4. nftables
Modern successor to iptables:

```bash
# Add rule to accept inbound traffic on port 12000
sudo nft add rule inet filter input tcp dport 12000 accept

# Save persistent configuration
sudo sh -c 'nft list ruleset > /etc/nftables.conf'
```
