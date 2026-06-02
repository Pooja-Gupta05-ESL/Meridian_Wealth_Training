# EC2 Deployment - Executive Summary

## 🎯 What's Been Created

Four comprehensive deployment guides have been created and pushed to GitHub:

### 1. **EC2_DEPLOYMENT_GUIDE.md** - Complete 7,000-word guide
- Step-by-step deployment for Ubuntu 24.04 LTS
- System preparation through production verification
- All tools installation and configuration
- Troubleshooting section included

### 2. **QUICK_REFERENCE_COMMANDS.md** - 500+ copy-paste commands
- Pre-organized by task
- Each command section independent
- Can be run in any order
- Quick lookups for any task

### 3. **NGINX_CONFIG_TEMPLATE.md** - Production-ready template
- Complete Nginx reverse proxy configuration
- SSL/TLS setup with security headers
- Performance optimization built-in
- Customization examples included

### 4. **deploy.sh** - Automated deployment script
- Single command execution: `bash deploy.sh your-domain.com`
- Color-coded output with progress tracking
- Full automation of all steps
- Error handling included

---

## 🚀 Quick Start (3 Options)

### **Option 1: Fully Automated (5 minutes)**
```bash
# On your EC2 instance:
bash deploy.sh your-domain.com

# Then configure:
nano .env                    # Add API keys
sudo certbot --nginx ...     # Get SSL certificate
bash start-app.sh           # Start application
```

### **Option 2: Manual Step-by-Step (30 minutes)**
Follow QUICK_REFERENCE_COMMANDS.md section by section with full control.

### **Option 3: Copy Individual Commands**
Use EC2_DEPLOYMENT_GUIDE.md for specific tasks as needed.

---

## 📋 Installed & Configured

| Component | Purpose | Status |
|-----------|---------|--------|
| **Python 3.12** | Application runtime | ✅ Documented |
| **Tmux** | Session management | ✅ Documented |
| **Nginx** | Reverse proxy | ✅ Documented |
| **Certbot** | SSL/TLS certificates | ✅ Documented |
| **UFW** | Firewall & security | ✅ Documented |
| **FastAPI** | Backend framework | ✅ Ready |
| **Virtual Environment** | Python isolation | ✅ Setup guide |

---

## 📦 Files Available in GitHub

```
Repository: Meridian_Wealth_Training/financial_analyst_app

Deployment Guides:
├── EC2_DEPLOYMENT_GUIDE.md (Complete reference)
├── QUICK_REFERENCE_COMMANDS.md (Command reference)
├── NGINX_CONFIG_TEMPLATE.md (Nginx template)
└── deploy.sh (Automated script)

Application Code:
├── app.py (FastAPI main)
├── source/ (Agent, RAG, database code)
├── frontend/ (Modern UI)
├── requirements.txt (Python dependencies)
└── data/ (Policy documents, SQLite)

Documentation:
├── README.md (Getting started)
├── ARCHITECTURE.md (System design)
├── API_DOCUMENTATION.md (API reference)
└── ... (7 more docs)
```

---

## ⚡ Key Commands to Know

```bash
# System update
sudo apt update && sudo apt upgrade -y

# Install all dependencies at once
sudo apt install -y python3.12 python3.12-venv git nginx tmux certbot python3-certbot-nginx ufw

# Clone & setup project
git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git
cd Meridian_Wealth_Training/financial_analyst_app
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Configure firewall
sudo ufw default deny incoming
sudo ufw allow 22,80,443/tcp
sudo ufw enable

# Start application
tmux new-session -d -s meridian-app
tmux send-keys -t meridian-app "source venv/bin/activate && python -m uvicorn app:app --port 8000" Enter

# Get SSL certificate
sudo certbot certonly --nginx -d your-domain.com

# Test endpoint
curl https://your-domain.com/health
```

---

## 📋 Pre-Deployment Checklist

- ☐ EC2 instance launched (Ubuntu 24.04 LTS, t3.medium+)
- ☐ Domain registered and pointing to instance IP
- ☐ Security group allows ports 22, 80, 443
- ☐ SSH key pair downloaded
- ☐ OpenAI API key obtained
- ☐ Tavily API key obtained

---

## 🔧 Estimated Deployment Time

- **Fully Automated:** 5-10 minutes
- **Manual (with reading):** 30-45 minutes
- **Conservative approach:** 1-2 hours

---

## 📈 Post-Deployment Verification

```bash
# Health check
curl https://your-domain.com/health
# Expected: {"status":"ok"}

# API test
curl -X POST https://your-domain.com/main/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show portfolio for CLT-001"}'

# Monitor logs
sudo tail -f /var/log/nginx/meridian-wealth-error.log
tmux attach-session -t meridian-app
```

---

## 🆘 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check if backend running: `curl http://127.0.0.1:8000/health` |
| Port in use | Find: `sudo lsof -i :8000` → Kill: `kill -9 <PID>` |
| SSL error | Renew: `sudo certbot renew --force-renewal` |
| Firewall blocking | Check: `sudo ufw status` → Allow: `sudo ufw allow 443/tcp` |
| App won't start | Check logs: `tmux capture-pane -t meridian-app -p -S -100` |

---

## 🔐 Security Best Practices (Included)

- ✅ UFW firewall with specific ports only
- ✅ HTTPS enforcement (HTTP → HTTPS redirect)
- ✅ Security headers (HSTS, X-Frame-Options, etc.)
- ✅ TLS 1.2+ only
- ✅ Strong SSL ciphers
- ✅ SSH key-based authentication
- ✅ .env file with .gitignore protection
- ✅ Non-root user for application

---

## 📞 Getting Help

1. **For general setup:** Read `EC2_DEPLOYMENT_GUIDE.md`
2. **For specific command:** Check `QUICK_REFERENCE_COMMANDS.md`
3. **For Nginx issues:** Review `NGINX_CONFIG_TEMPLATE.md`
4. **For automation:** Run `bash deploy.sh`

---

## 🎓 What You'll Learn

By following these guides, you'll understand:
- ✓ Ubuntu 24.04 LTS system administration
- ✓ Python 3.12 virtual environment setup
- ✓ Nginx reverse proxy configuration
- ✓ SSL/TLS certificate management
- ✓ Linux firewall (UFW) configuration
- ✓ Tmux session management
- ✓ FastAPI production deployment
- ✓ System monitoring and troubleshooting

---

## 📊 System Requirements

**Minimum:**
- t3.medium EC2 instance (2 vCPU, 4 GB RAM)
- 20 GB storage
- Ubuntu 24.04 LTS

**Recommended:**
- t3.large or t3.xlarge (4+ vCPU, 8+ GB RAM)
- 30+ GB storage
- Same OS

---

## ✅ All Documentation Committed to GitHub

Everything is ready in your repository:
https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training

Branch: `main`  
Latest Commit: Deployment documentation added

---

## 🎯 Next Actions

1. **Launch EC2 instance** (Ubuntu 24.04 LTS)
2. **SSH into instance:** `ssh -i key.pem ubuntu@ip-address`
3. **Clone repository:** `git clone https://github.com/Pooja-Gupta05-ESL/Meridian_Wealth_Training.git`
4. **Choose deployment method:**
   - Quick: `bash deploy.sh your-domain.com`
   - Manual: Follow guides step-by-step
5. **Configure API keys** in `.env` file
6. **Obtain SSL certificate** with Certbot
7. **Start application** with Tmux
8. **Verify** everything is working

---

**Status:** ✅ Ready for Deployment  
**Last Updated:** June 2, 2026  
**All Files:** In GitHub repository
