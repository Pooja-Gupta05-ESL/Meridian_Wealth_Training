#!/bin/bash

# ============================================================================
# MERIDIAN WEALTH - EC2 UBUNTU 24.04 LTS DEPLOYMENT SCRIPT
# ============================================================================
# This script automates the deployment process
# Usage: bash deploy.sh [domain_name]
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN_NAME="${1:-your-domain.com}"
APP_DIR="/var/www/meridian-wealth"
APP_NAME="financial_analyst_app"
REPO_URL="https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git"
PYTHON_VERSION="3.12"

# Functions
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ ${GREEN}$1${BLUE}${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 not found"
        return 1
    fi
    return 0
}

# ============================================================================
# DEPLOYMENT START
# ============================================================================

print_header "MERIDIAN WEALTH EC2 DEPLOYMENT"

# Pre-flight checks
print_step "Pre-flight checks..."
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root (use sudo when needed)"
    exit 1
fi
print_success "Not running as root"

# ============================================================================
# STEP 1: SYSTEM UPDATE
# ============================================================================

print_header "STEP 1: SYSTEM UPDATE & UPGRADE"

print_step "Updating package manager..."
sudo apt update
print_success "Package manager updated"

print_step "Upgrading packages..."
sudo apt upgrade -y
print_success "Packages upgraded"

print_step "Removing unnecessary packages..."
sudo apt autoremove -y
print_success "Cleanup complete"

# ============================================================================
# STEP 2: PYTHON 3.12 INSTALLATION
# ============================================================================

print_header "STEP 2: PYTHON 3.12 INSTALLATION"

print_step "Installing Python 3.12 and dependencies..."
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip

print_success "Python 3.12 installed"

# Set Python 3.12 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 2>/dev/null || true

# Verify Python
PYTHON_CHECK=$(python3 --version)
print_success "Python version: $PYTHON_CHECK"

# Verify pip
PIP_CHECK=$(python3 -m pip --version)
print_success "Pip version: $PIP_CHECK"

# ============================================================================
# STEP 3: SYSTEM DEPENDENCIES
# ============================================================================

print_header "STEP 3: INSTALLING SYSTEM DEPENDENCIES"

print_step "Installing build tools and libraries..."
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
    jq

print_success "System dependencies installed"

# ============================================================================
# STEP 4: TMUX INSTALLATION
# ============================================================================

print_header "STEP 4: TMUX INSTALLATION"

print_step "Installing Tmux..."
sudo apt install -y tmux

TMUX_VERSION=$(tmux -V)
print_success "Tmux installed: $TMUX_VERSION"

# ============================================================================
# STEP 5: NGINX INSTALLATION
# ============================================================================

print_header "STEP 5: NGINX INSTALLATION"

print_step "Installing Nginx..."
sudo apt install -y nginx

print_success "Nginx installed"

print_step "Starting and enabling Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

NGINX_STATUS=$(sudo systemctl is-active nginx)
print_success "Nginx status: $NGINX_STATUS"

# ============================================================================
# STEP 6: CERTBOT & SSL INSTALLATION
# ============================================================================

print_header "STEP 6: CERTBOT & SSL INSTALLATION"

print_step "Installing Certbot..."
sudo apt install -y certbot python3-certbot-nginx

CERTBOT_VERSION=$(certbot --version)
print_success "Certbot installed: $CERTBOT_VERSION"

# ============================================================================
# STEP 7: UFW FIREWALL SETUP
# ============================================================================

print_header "STEP 7: UFW FIREWALL SETUP"

print_step "Installing UFW..."
sudo apt install -y ufw

print_success "UFW installed"

print_step "Configuring UFW rules..."

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential ports
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Enable UFW
sudo ufw enable

# Show UFW status
print_success "UFW configured"
echo -e "${BLUE}UFW Rules:${NC}"
sudo ufw status

# ============================================================================
# STEP 8: APPLICATION SETUP
# ============================================================================

print_header "STEP 8: APPLICATION SETUP"

print_step "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown -R ubuntu:ubuntu $APP_DIR
print_success "Application directory created at $APP_DIR"

print_step "Cloning repository..."
cd $APP_DIR
git clone $REPO_URL
print_success "Repository cloned"

cd $APP_DIR/Meridian_Wealth_Training/$APP_NAME
print_success "Working directory: $(pwd)"

print_step "Creating Python virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

print_step "Activating virtual environment and installing dependencies..."
source venv/bin/activate

print_step "Upgrading pip..."
pip install --upgrade pip setuptools wheel
print_success "Pip upgraded"

print_step "Installing project requirements..."
pip install -r requirements.txt
print_success "Project dependencies installed"

# Verify installations
echo -e "\n${BLUE}Installed Python Packages:${NC}"
pip list | grep -E "fastapi|uvicorn|langchain|openai|pydantic" | sed 's/^/  /'

# ============================================================================
# STEP 9: ENVIRONMENT CONFIGURATION
# ============================================================================

print_header "STEP 9: ENVIRONMENT CONFIGURATION"

print_step "Creating .env file..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
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
EOF
    print_success ".env file created"
    print_error "IMPORTANT: Edit .env with your actual API keys:"
    echo "  nano $APP_DIR/Meridian_Wealth_Training/$APP_NAME/.env"
else
    print_success ".env file already exists"
fi

# ============================================================================
# STEP 10: NGINX CONFIGURATION
# ============================================================================

print_header "STEP 10: NGINX CONFIGURATION"

print_step "Creating Nginx configuration..."

sudo tee /etc/nginx/sites-available/meridian-wealth > /dev/null << 'NGINX_CONFIG'
upstream app_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name DOMAIN_NAME www.DOMAIN_NAME;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name DOMAIN_NAME www.DOMAIN_NAME;

    ssl_certificate /etc/letsencrypt/live/DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_NAME/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    access_log /var/log/nginx/meridian-wealth-access.log;
    error_log /var/log/nginx/meridian-wealth-error.log;

    client_max_body_size 10M;

    location / {
        proxy_pass http://app_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://app_server;
        access_log off;
    }
}
NGINX_CONFIG

# Replace domain name
sudo sed -i "s/DOMAIN_NAME/$DOMAIN_NAME/g" /etc/nginx/sites-available/meridian-wealth

print_success "Nginx configuration created"

print_step "Enabling Nginx configuration..."
sudo ln -sf /etc/nginx/sites-available/meridian-wealth /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

print_step "Testing Nginx configuration..."
if sudo nginx -t; then
    print_success "Nginx configuration is valid"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

print_step "Reloading Nginx..."
sudo systemctl reload nginx
print_success "Nginx reloaded"

# ============================================================================
# STEP 11: SSL CERTIFICATE
# ============================================================================

print_header "STEP 11: SSL CERTIFICATE SETUP"

print_step "SSL certificate setup for: $DOMAIN_NAME"
echo -e "${YELLOW}Run the following command to obtain SSL certificate:${NC}"
echo ""
echo -e "${BLUE}sudo certbot certonly --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME${NC}"
echo ""
echo -e "${YELLOW}This will be done interactively.${NC}"

# Optional: Auto-setup if email provided
if [ -n "$SSL_EMAIL" ]; then
    sudo certbot certonly --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --email $SSL_EMAIL --agree-tos --non-interactive
    print_success "SSL certificate obtained"
fi

# ============================================================================
# STEP 12: STARTUP SCRIPT
# ============================================================================

print_header "STEP 12: APPLICATION STARTUP SCRIPT"

print_step "Creating startup script..."

cat > $APP_DIR/Meridian_Wealth_Training/$APP_NAME/start-app.sh << 'STARTUP_SCRIPT'
#!/bin/bash

SESSION_NAME="meridian-app"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    tmux kill-session -t $SESSION_NAME
fi

tmux new-session -d -s $SESSION_NAME -c $APP_DIR
tmux send-keys -t $SESSION_NAME "source venv/bin/activate" Enter
tmux send-keys -t $SESSION_NAME "python -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4 --log-level info" Enter

echo "✓ Application started in tmux session '$SESSION_NAME'"
echo "✓ Attach with: tmux attach-session -t $SESSION_NAME"
STARTUP_SCRIPT

chmod +x $APP_DIR/Meridian_Wealth_Training/$APP_NAME/start-app.sh
print_success "Startup script created"

# ============================================================================
# FINAL VERIFICATION
# ============================================================================

print_header "FINAL VERIFICATION"

echo -e "${BLUE}System Information:${NC}"
echo "  OS: $(lsb_release -ds)"
echo "  Python: $(python3 --version)"
echo "  Pip: $(python3 -m pip --version | cut -d' ' -f2-)"
echo "  Nginx: $(nginx -v 2>&1 | cut -d' ' -f3)"
echo "  Tmux: $(tmux -V)"
echo "  Certbot: $(certbot --version 2>&1 | cut -d' ' -f1-2)"
echo ""

echo -e "${BLUE}Services Status:${NC}"
echo "  Nginx: $(sudo systemctl is-active nginx)"
echo "  UFW: $(sudo ufw status | head -1)"
echo ""

echo -e "${BLUE}Firewall Rules:${NC}"
sudo ufw status | grep -E "(22|80|443)" | sed 's/^/  /'
echo ""

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================

print_header "DEPLOYMENT SUMMARY"

echo -e "${GREEN}✓ System Update & Upgrade${NC}"
echo -e "${GREEN}✓ Python 3.12 Installed${NC}"
echo -e "${GREEN}✓ Dependencies Installed (Tmux, Nginx, Certbot, UFW)${NC}"
echo -e "${GREEN}✓ Application Cloned & Setup${NC}"
echo -e "${GREEN}✓ Nginx Configured${NC}"
echo -e "${GREEN}✓ Firewall Configured${NC}"
echo ""

print_header "NEXT STEPS"

echo -e "${YELLOW}1. Configure API Keys:${NC}"
echo "   nano $APP_DIR/Meridian_Wealth_Training/$APP_NAME/.env"
echo ""

echo -e "${YELLOW}2. Obtain SSL Certificate:${NC}"
echo "   sudo certbot certonly --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME"
echo ""

echo -e "${YELLOW}3. Test Application:${NC}"
echo "   cd $APP_DIR/Meridian_Wealth_Training/$APP_NAME"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app:app --host 127.0.0.1 --port 8000"
echo ""

echo -e "${YELLOW}4. Start Application with Tmux:${NC}"
echo "   bash $APP_DIR/Meridian_Wealth_Training/$APP_NAME/start-app.sh"
echo ""

echo -e "${YELLOW}5. View Application Logs:${NC}"
echo "   tmux attach-session -t meridian-app"
echo ""

echo -e "${YELLOW}6. View Nginx Logs:${NC}"
echo "   sudo tail -f /var/log/nginx/meridian-wealth-error.log"
echo "   sudo tail -f /var/log/nginx/meridian-wealth-access.log"
echo ""

echo -e "${YELLOW}7. Test API:${NC}"
echo "   curl https://$DOMAIN_NAME/health"
echo ""

print_header "DEPLOYMENT COMPLETE ✓"

echo -e "${GREEN}Your Meridian Wealth application is ready for deployment!${NC}"
echo ""
