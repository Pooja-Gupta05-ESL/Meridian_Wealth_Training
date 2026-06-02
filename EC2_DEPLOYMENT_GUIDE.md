# EC2 Ubuntu 24.04 LTS Deployment Guide
## Meridian Wealth Financial Analyst Agent

This guide provides step-by-step instructions to deploy the Financial Analyst Agent on AWS EC2 with Ubuntu 24.04 LTS.

---

## Table of Contents
1. [EC2 Instance Setup](#ec2-instance-setup)
2. [System Preparation](#system-preparation)
3. [Python 3.12 Installation](#python-312-installation)
4. [Dependencies Installation](#dependencies-installation)
5. [Project Setup](#project-setup)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/TLS with Certbot](#ssltls-with-certbot)
8. [Firewall (UFW) Setup](#firewall-ufw-setup)
9. [Running with Tmux](#running-with-tmux)
10. [Final Verification](#final-verification)

---

## EC2 Instance Setup

### Prerequisites
- AWS Account with EC2 access
- Ubuntu 24.04 LTS AMI
- Instance type: t3.medium or higher (recommended)
- Security Group rules configured for ports 22, 80, 443

### Instance Configuration
```
Instance Type: t3.medium (2 vCPU, 4 GB RAM)
Storage: 20 GB EBS (gp3)
OS: Ubuntu 24.04 LTS
Security: SSH (22), HTTP (80), HTTPS (443)
```

---

## System Preparation

Connect to your EC2 instance:
```bash
ssh -i your-key.pem ubuntu@your-instance-public-ip
```

### Step 1: Update Package Manager
```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install System Dependencies
```bash
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    vim \
    nano \
    htop \
    net-tools
```

### Step 3: Verify System
```bash
uname -a
lsb_release -a
python3 --version
```

Expected output for Python: `Python 3.12.x` (Ubuntu 24.04 comes with Python 3.12)

---

## Python 3.12 Installation

### Important: Ubuntu 24.04 LTS comes with Python 3.12 pre-installed

**Option 1: Use Default Python 3.12 (Recommended - FASTEST)**
```bash
# Ubuntu 24.04 comes with Python 3.12, verify it's installed
python3 --version
# Expected output: Python 3.12.x

# Verify pip is available
python3 -m pip --version

# You're ready to go! No additional installation needed.
# Just create your virtual environment with:
python3 -m venv venv
source venv/bin/activate
```

### Option 2: Install Python 3.12 Packages from Deadsnakes PPA
If you need the individual python3.12 packages:
```bash
# Add deadsnakes PPA
sudo add-apt-repository -y ppa:deadsnakes/ppa

# Update package manager
sudo apt update

# Install Python 3.12 packages
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Set Python 3.12 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Verify
python3.12 --version
python3.12 -m pip --version
```

### Option 3: Fallback - If Packages Not Found
If neither Option 1 nor Option 2 work, use system Python:
```bash
# Simply use system Python
python3 -m venv venv
source venv/bin/activate

# Verify pip
python3 -m pip --version

# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel
```

---

## Dependencies Installation

### Step 1: Install Tmux (Terminal Multiplexer)
```bash
sudo apt install -y tmux

# Verify installation
tmux -V

# Basic tmux commands:
# tmux new-session -d -s app_session          # Create session
# tmux send-keys -t app_session "command" Enter  # Send command
# tmux attach-session -t app_session          # Attach to session
```

### Step 2: Install Nginx (Web Server)
```bash
sudo apt install -y nginx

# Start and enable nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify status
sudo systemctl status nginx
```

### Step 3: Install Certbot (SSL/TLS Certificates)
```bash
sudo apt install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

### Step 4: Install UFW (Firewall)
```bash
sudo apt install -y ufw

# Enable UFW
sudo ufw enable

# Verify status
sudo ufw status
```

### Step 5: Install Additional Tools
```bash
# For application deployment
sudo apt install -y supervisor  # Process manager
sudo apt install -y redis-server  # Optional: for caching
```

---

## Project Setup

### Step 1: Create Application Directory
```bash
sudo mkdir -p /var/www/meridian-wealth
sudo chown -R ubuntu:ubuntu /var/www/meridian-wealth
cd /var/www/meridian-wealth
```

### Step 2: Clone Project from GitHub
```bash
git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git
cd Meridian_Wealth_Training/financial_analyst_app
```

### Step 3: Create Python Virtual Environment
```bash
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 4: Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install project requirements
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "fastapi|uvicorn|langchain|openai"
```

### Step 5: Configure Environment Variables
```bash
# Create .env file
nano .env
```

Add your configuration:
```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Tavily API (Web Search)
TAVILY_API_KEY=your-tavily-api-key-here

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Database
DATABASE_URL=sqlite:///./data/vector_db/meridian_wealth.db

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### Step 6: Test Application
```bash
# Quick test
python -m uvicorn app:app --host 127.0.0.1 --port 8000

# In another terminal, test endpoint
curl http://127.0.0.1:8000/health
```

---

## Nginx Configuration

### Step 1: Create Nginx Configuration File
```bash
sudo nano /etc/nginx/sites-available/meridian-wealth
```

Add the following configuration:
```nginx
upstream app_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (will be added by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/meridian-wealth-access.log;
    error_log /var/log/nginx/meridian-wealth-error.log;

    # Client upload limit
    client_max_body_size 10M;

    # Root location
    location / {
        proxy_pass http://app_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app/frontend/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (for monitoring)
    location /health {
        proxy_pass http://app_server;
        access_log off;
    }
}
```

### Step 2: Enable Nginx Configuration
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/meridian-wealth /etc/nginx/sites-enabled/

# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/TLS with Certbot

### Step 1: Obtain SSL Certificate
```bash
# Replace your-domain.com with your actual domain
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# For first-time setup, you'll be prompted for:
# - Email address
# - Agreement to terms
# - Newsletter subscription (optional)
```

### Step 2: Automatic Renewal
```bash
# Certbot automatically configures renewal
# Test renewal (dry run)
sudo certbot renew --dry-run

# Check renewal timer
sudo systemctl list-timers
```

### Step 3: Verify SSL Certificate
```bash
# Check certificate expiration
sudo certbot certificates

# Expected output shows certificate details and renewal date
```

---

## Firewall (UFW) Setup

### Step 1: Configure UFW Rules
```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical - do this first!)
sudo ufw allow 22/tcp
sudo ufw allow ssh

# Allow HTTP
sudo ufw allow 80/tcp
sudo ufw allow http

# Allow HTTPS
sudo ufw allow 443/tcp
sudo ufw allow https

# Enable UFW
sudo ufw enable

# Verify rules
sudo ufw status verbose
```

### Step 2: Additional UFW Rules (Optional)
```bash
# Limit SSH attempts (prevent brute force)
sudo ufw limit 22/tcp

# Allow specific IP to SSH
sudo ufw allow from 192.168.1.100 to any port 22

# Delete a rule
sudo ufw delete allow 8000/tcp

# View all rules
sudo ufw show added
```

---

## Running with Tmux

### Step 1: Create Tmux Session
```bash
# Create a new named session
tmux new-session -d -s meridian-app -c /var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app
```

### Step 2: Start Application in Tmux
```bash
# Activate venv and start app
tmux send-keys -t meridian-app "source venv/bin/activate && python -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4" Enter

# Verify the session is running
tmux list-sessions
```

### Step 3: Create Tmux Startup Script
```bash
# Create startup script
nano ~/start-meridian-app.sh
```

Add the following:
```bash
#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_DIR="/var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app"
SESSION_NAME="meridian-app"

echo -e "${YELLOW}Starting Meridian Wealth Application...${NC}"

# Check if session already exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo -e "${YELLOW}Session $SESSION_NAME already exists. Killing it...${NC}"
    tmux kill-session -t $SESSION_NAME
fi

# Create new session
tmux new-session -d -s $SESSION_NAME -c $APP_DIR

# Start application
tmux send-keys -t $SESSION_NAME "source venv/bin/activate" Enter
tmux send-keys -t $SESSION_NAME "python -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4 --log-level info" Enter

# Wait for startup
sleep 3

# Verify
if tmux list-sessions | grep -q $SESSION_NAME; then
    echo -e "${GREEN}✓ Application started successfully in tmux session '$SESSION_NAME'${NC}"
    echo -e "${GREEN}✓ Attach with: tmux attach-session -t $SESSION_NAME${NC}"
else
    echo -e "${RED}✗ Failed to start application${NC}"
    exit 1
fi
```

Make it executable:
```bash
chmod +x ~/start-meridian-app.sh
```

### Step 4: Tmux Commands Reference
```bash
# List all sessions
tmux list-sessions

# Attach to session
tmux attach-session -t meridian-app

# Detach from session (inside tmux: Ctrl+b, then d)

# Send command to session
tmux send-keys -t meridian-app "command" Enter

# Kill session
tmux kill-session -t meridian-app

# View session logs (inside tmux window, scroll with Ctrl+b, [)

# Kill all sessions
tmux kill-server
```

---

## Final Verification

### Step 1: Check All Services
```bash
# Check Nginx status
sudo systemctl status nginx

# Check application logs
tmux capture-pane -t meridian-app -p

# Check open ports
sudo netstat -tulpn | grep -E ":(22|80|443|8000)"
```

### Step 2: Test Application
```bash
# From your local machine
curl -H "Content-Type: application/json" https://your-domain.com/health

# Expected response:
# {"status":"ok"}

# Test API endpoint
curl -X POST https://your-domain.com/main/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show portfolio for CLT-001", "client_name": "Test"}'
```

### Step 3: Monitor Application
```bash
# View real-time logs
tmux capture-pane -t meridian-app -p -S -100

# Monitor system resources
htop

# Check nginx logs
sudo tail -f /var/log/nginx/meridian-wealth-error.log
sudo tail -f /var/log/nginx/meridian-wealth-access.log
```

### Step 4: Set Up Process Manager (Supervisor)
```bash
# Create supervisor config
sudo nano /etc/supervisor/conf.d/meridian-app.conf
```

Add configuration:
```ini
[program:meridian-app]
command=/var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app/venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4
directory=/var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/meridian-app.log
environment=PATH="/var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app/venv/bin"
```

Update supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start meridian-app
sudo supervisorctl status
```

---

## Troubleshooting

### Issue: Port 8000 Already in Use
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
kill -9 <PID>
```

### Issue: Permission Denied
```bash
# Fix directory permissions
sudo chown -R ubuntu:ubuntu /var/www/meridian-wealth
sudo chmod -R 755 /var/www/meridian-wealth
```

### Issue: Nginx 502 Bad Gateway
```bash
# Check if app is running
tmux list-sessions
tmux capture-pane -t meridian-app -p

# Check Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Issue: SSL Certificate Not Working
```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check certificate validity
ssl certificate check
```

### Issue: High Memory Usage
```bash
# Check memory usage
free -h

# Reduce worker count in app startup
# Change: --workers 4 to --workers 2
```

---

## Production Checklist

- [ ] Domain name pointing to EC2 instance
- [ ] SSL certificate installed and working
- [ ] Nginx reverse proxy configured
- [ ] UFW firewall configured with proper rules
- [ ] Environment variables (.env) properly set
- [ ] Application running in tmux or supervisor
- [ ] Database seeded with test data
- [ ] API keys (OpenAI, Tavily) configured
- [ ] Monitoring and logging set up
- [ ] Backup strategy in place
- [ ] Security groups configured in AWS
- [ ] Auto-scaling group configured (optional)

---

## Quick Start Script

Complete deployment in one go:

```bash
#!/bin/bash

# Save as deploy.sh and run: bash deploy.sh

set -e

echo "Starting Meridian Wealth Deployment..."

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
sudo apt install -y python3.12 python3.12-venv python3-pip git nginx tmux certbot python3-certbot-nginx ufw

# Clone project
echo "Cloning project..."
cd /var/www
sudo mkdir -p meridian-wealth
sudo chown -R ubuntu:ubuntu meridian-wealth
cd meridian-wealth
git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git
cd Meridian_Wealth_Training/financial_analyst_app

# Setup Python venv
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure firewall
echo "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

echo "✓ Deployment preparation complete!"
echo "Next steps:"
echo "1. Configure .env file with API keys"
echo "2. Set up Nginx config (replace your-domain.com)"
echo "3. Obtain SSL certificate: sudo certbot certonly --nginx -d your-domain.com"
echo "4. Start application: ./start-meridian-app.sh"
```

---

## Support & Resources

- **Nginx Documentation:** https://nginx.org/en/docs/
- **Certbot Documentation:** https://certbot.eff.org/docs/
- **UFW Documentation:** https://help.ubuntu.com/community/UFW
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Tmux Documentation:** https://github.com/tmux/tmux/wiki

---

**Last Updated:** June 2, 2026  
**Status:** Production Ready ✅
