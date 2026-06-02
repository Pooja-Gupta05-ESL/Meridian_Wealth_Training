# EC2 Deployment - Quick Reference Commands

## Pre-Deployment

### Connect to EC2 Instance
```bash
ssh -i your-key.pem ubuntu@your-instance-public-ip
```

---

## STEP 1: System Update & Upgrade

```bash
# Update package manager
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Remove unnecessary packages
sudo apt autoremove -y
```

---

## STEP 2: Python 3.12 Installation

```bash
# Install Python 3.12 (comes with Ubuntu 24.04)
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Verify Python version
python3 --version

# Verify pip
python3 -m pip --version

# Set Python 3.12 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

---

## STEP 3: Install Required Dependencies

### Install All Dependencies at Once
```bash
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    wget \
    curl \
    vim \
    nano \
    htop \
    net-tools \
    tmux \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw
```

### Or Install Individually

**Tmux (Terminal Multiplexer)**
```bash
sudo apt install -y tmux
tmux -V  # Verify
```

**Nginx (Web Server)**
```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

**Certbot (SSL/TLS)**
```bash
sudo apt install -y certbot python3-certbot-nginx
certbot --version  # Verify
```

**UFW (Firewall)**
```bash
sudo apt install -y ufw
ufw --version  # Verify
```

---

## STEP 4: Clone & Setup Project

```bash
# Create application directory
sudo mkdir -p /var/www/meridian-wealth
sudo chown -R ubuntu:ubuntu /var/www/meridian-wealth
cd /var/www/meridian-wealth

# Clone repository
git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git
cd Meridian_Wealth_Training/financial_analyst_app

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep -E "fastapi|uvicorn|langchain"
```

---

## STEP 5: Environment Configuration

```bash
# Create .env file
nano .env

# Add the following:
OPENAI_API_KEY=your-api-key-here
TAVILY_API_KEY=your-api-key-here
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

---

## STEP 6: UFW Firewall Configuration

```bash
# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical - do this first!)
sudo ufw allow 22/tcp
sudo ufw allow ssh

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Enable UFW
sudo ufw enable

# Check status
sudo ufw status
sudo ufw status verbose

# Show detailed rules
sudo ufw show added

# Limit SSH attempts (prevent brute force)
sudo ufw limit 22/tcp

# Delete a rule (example)
sudo ufw delete allow 8000/tcp

# Reload firewall
sudo ufw reload

# Disable UFW (if needed)
sudo ufw disable
```

---

## STEP 7: Nginx Configuration

```bash
# Create Nginx config file
sudo nano /etc/nginx/sites-available/meridian-wealth

# Enable the configuration
sudo ln -s /etc/nginx/sites-available/meridian-wealth /etc/nginx/sites-enabled/

# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View specific site logs
sudo tail -f /var/log/nginx/meridian-wealth-error.log
sudo tail -f /var/log/nginx/meridian-wealth-access.log
```

---

## STEP 8: SSL/TLS Certificate with Certbot

```bash
# Obtain SSL certificate
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Interactive setup (first time)
# Follow prompts for:
# - Email address
# - Terms agreement
# - Newsletter subscription

# List all certificates
sudo certbot certificates

# Renew certificate (test)
sudo certbot renew --dry-run

# Renew certificate (actual)
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Revoke certificate
sudo certbot revoke --cert-path /etc/letsencrypt/live/your-domain.com/fullchain.pem

# Delete certificate
sudo certbot delete --cert-name your-domain.com

# Check certificate expiration date
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## STEP 9: Tmux - Running Application

```bash
# Activate virtual environment (if not already done)
source venv/bin/activate

# Create new tmux session
tmux new-session -d -s meridian-app -c /var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app

# Start application
tmux send-keys -t meridian-app "source venv/bin/activate" Enter
tmux send-keys -t meridian-app "python -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4" Enter

# List all sessions
tmux list-sessions

# Attach to session
tmux attach-session -t meridian-app

# Detach from session (inside tmux: Ctrl+b, then d)

# Send command to session
tmux send-keys -t meridian-app "command" Enter

# View session output
tmux capture-pane -t meridian-app -p

# View more lines
tmux capture-pane -t meridian-app -p -S -100

# Kill session
tmux kill-session -t meridian-app

# Kill all sessions
tmux kill-server

# Create startup script
bash start-app.sh
```

---

## STEP 10: Application Testing

```bash
# Test health endpoint (locally on instance)
curl http://127.0.0.1:8000/health

# Test with HTTPS (from remote)
curl https://your-domain.com/health

# Test API endpoint
curl -X POST https://your-domain.com/main/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show portfolio for CLT-001", "client_name": "Test"}'

# Verbose output
curl -v https://your-domain.com/health

# Include headers
curl -i https://your-domain.com/health
```

---

## Monitoring & Troubleshooting

```bash
# Check system resource usage
htop

# Monitor memory usage
free -h

# Monitor disk usage
df -h

# Find process using specific port
sudo lsof -i :8000
sudo lsof -i :80
sudo lsof -i :443

# Kill process by PID
kill -9 <PID>

# Find process by name
ps aux | grep uvicorn
ps aux | grep python

# Check open ports
sudo netstat -tulpn
sudo ss -tulpn

# Monitor network
nethogs

# Check system logs
sudo journalctl -f

# Check Nginx process
ps aux | grep nginx

# Test if port is listening
nc -zv 127.0.0.1 8000
```

---

## File Management

```bash
# Change file permissions
sudo chmod 755 /var/www/meridian-wealth
sudo chmod 644 /var/www/meridian-wealth/file.txt

# Change file ownership
sudo chown -R ubuntu:ubuntu /var/www/meridian-wealth

# View file size
du -sh /var/www/meridian-wealth

# List files recursively
ls -lah /var/www/meridian-wealth

# Find large files
find /var/www/meridian-wealth -type f -size +10M

# Delete files
rm -rf /path/to/file
```

---

## Database Management

```bash
# Check database file
ls -lh data/vector_db/meridian_wealth.db

# Seed database (if needed)
python seed_db.py

# Query database with SQLite
sqlite3 data/vector_db/meridian_wealth.db
# Inside sqlite3:
# .tables                    # List tables
# SELECT COUNT(*) FROM clients;  # Count records
# .quit                      # Exit
```

---

## Systemctl Commands

```bash
# General commands
sudo systemctl start <service>
sudo systemctl stop <service>
sudo systemctl restart <service>
sudo systemctl reload <service>
sudo systemctl status <service>
sudo systemctl enable <service>  # Auto-start on boot
sudo systemctl disable <service>

# Specific services
sudo systemctl restart nginx
sudo systemctl restart supervisor
sudo systemctl status nginx
```

---

## Git Commands

```bash
# Clone repository
git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git

# Pull latest changes
cd /var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app
git pull origin main

# Check git status
git status

# View commit history
git log --oneline

# Check current branch
git branch
```

---

## Emergency Commands

```bash
# Stop all processes
sudo systemctl stop nginx
tmux kill-server

# Emergency restart
sudo reboot

# Force stop process
pkill -9 -f uvicorn

# Clear system cache
sudo sync; sudo echo 3 > /proc/sys/vm/drop_caches

# Check system uptime
uptime

# View system log in real-time
sudo tail -f /var/log/syslog
```

---

## Performance Optimization

```bash
# Increase file descriptors
ulimit -n

# Set higher limit
sudo nano /etc/security/limits.conf
# Add: * soft nofile 65535
# Add: * hard nofile 65535

# Check current settings
ulimit -a

# Optimize Nginx worker connections
sudo nano /etc/nginx/nginx.conf
# Change: worker_connections 768 to 2048

# Reload Nginx
sudo systemctl reload nginx
```

---

## Backup & Restore

```bash
# Backup application directory
tar -czf meridian-backup-$(date +%Y%m%d).tar.gz /var/www/meridian-wealth

# Backup database only
cp data/vector_db/meridian_wealth.db data/vector_db/meridian_wealth.db.backup

# Restore from backup
tar -xzf meridian-backup-20260602.tar.gz -C /

# List backup contents
tar -tzf meridian-backup-20260602.tar.gz
```

---

## Quick Deploy (All-in-One)

```bash
# Run the automated deployment script
bash deploy.sh your-domain.com

# Or manual quick setup
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv git nginx tmux certbot python3-certbot-nginx ufw

mkdir -p /var/www/meridian-wealth && cd /var/www/meridian-wealth
git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git
cd Meridian_Wealth_Training/financial_analyst_app

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Start application
bash start-app.sh
```

---

## Useful Aliases (Optional)

Add to `~/.bashrc`:

```bash
alias app-start='cd /var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app && bash start-app.sh'
alias app-logs='tmux capture-pane -t meridian-app -p'
alias app-attach='tmux attach-session -t meridian-app'
alias nginx-log='sudo tail -f /var/log/nginx/meridian-wealth-error.log'
alias nginx-access='sudo tail -f /var/log/nginx/meridian-wealth-access.log'
alias app-status='tmux list-sessions'
alias app-stop='tmux kill-session -t meridian-app'
```

Reload bashrc:
```bash
source ~/.bashrc
```

---

## Support

- **Issues?** Check logs: `sudo tail -f /var/log/nginx/meridian-wealth-error.log`
- **App down?** Check: `tmux list-sessions` and restart with `bash start-app.sh`
- **Firewall blocking?** Check: `sudo ufw status`
- **Port in use?** Find: `sudo lsof -i :8000`

---

**Last Updated:** June 2, 2026  
**Status:** Ready for Deployment ✅
