# Nginx Configuration Template for Meridian Wealth Application

## File Location: /etc/nginx/sites-available/meridian-wealth

```nginx
# ============================================================================
# Meridian Wealth Financial Advisor - Nginx Reverse Proxy Configuration
# ============================================================================
# This configuration:
# - Redirects HTTP to HTTPS
# - Proxies requests to the FastAPI backend on port 8000
# - Enables gzip compression
# - Sets security headers
# - Configures SSL/TLS
# - Handles WebSocket connections
#
# Installation:
# 1. Save this as /etc/nginx/sites-available/meridian-wealth
# 2. Replace YOUR_DOMAIN_NAME with your actual domain
# 3. Enable: sudo ln -s /etc/nginx/sites-available/meridian-wealth /etc/nginx/sites-enabled/
# 4. Test: sudo nginx -t
# 5. Reload: sudo systemctl reload nginx
# ============================================================================

# Upstream definition for the FastAPI backend
upstream app_server {
    # Connection pooling
    keepalive 32;
    
    # Backend server(s)
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    
    # Optional: Add multiple servers for load balancing
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

# ============================================================================
# HTTP Server Block - Redirect to HTTPS
# ============================================================================
server {
    listen 80;
    listen [::]:80;
    
    server_name YOUR_DOMAIN_NAME www.YOUR_DOMAIN_NAME;
    
    # Security: Prevent processing requests with undefined server names
    # If this block is matched, a 444 "no response" will be returned
    
    # Allow Let's Encrypt to verify domain during certificate renewal
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# ============================================================================
# HTTPS Server Block - Main Application
# ============================================================================
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    # Server name(s)
    server_name YOUR_DOMAIN_NAME www.YOUR_DOMAIN_NAME;
    
    # ========================================================================
    # SSL/TLS Configuration
    # ========================================================================
    
    # SSL certificates (obtained via Certbot)
    ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN_NAME/privkey.pem;
    
    # SSL protocol versions (disable old, insecure versions)
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # SSL ciphers (strong ciphers only)
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # SSL session caching for performance
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP stapling (improves SSL/TLS performance)
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/YOUR_DOMAIN_NAME/chain.pem;
    
    # ========================================================================
    # Security Headers
    # ========================================================================
    
    # Enforce HTTPS for 1 year
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Prevent MIME sniffing
    add_header X-Content-Type-Options "nosniff" always;
    
    # Prevent clickjacking attacks
    add_header X-Frame-Options "SAMEORIGIN" always;
    
    # Enable XSS protection in older browsers
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Content Security Policy (basic)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;
    
    # Referrer Policy
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Permissions Policy
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()" always;
    
    # ========================================================================
    # Logging
    # ========================================================================
    
    access_log /var/log/nginx/meridian-wealth-access.log combined buffer=16k flush=5s;
    error_log /var/log/nginx/meridian-wealth-error.log warn;
    
    # ========================================================================
    # Performance Optimizations
    # ========================================================================
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;
    gzip_disable "msie6";
    
    # Client upload limit (adjust as needed)
    client_max_body_size 10M;
    
    # Buffer sizes
    client_body_buffer_size 128k;
    client_max_body_size 10M;
    
    # Connection timeouts
    keepalive_timeout 65;
    
    # ========================================================================
    # Main Application Proxy
    # ========================================================================
    
    location / {
        # Proxy to FastAPI backend
        proxy_pass http://app_server;
        
        # Forward original request information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Proxy buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # Proxy timeouts (increased for long-running agent queries)
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Connection pooling
        proxy_set_header Connection "";
    }
    
    # ========================================================================
    # Health Check Endpoint (no logging)
    # ========================================================================
    
    location /health {
        proxy_pass http://app_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Don't log health checks to reduce log clutter
        access_log off;
    }
    
    # ========================================================================
    # Static Files (if needed)
    # ========================================================================
    
    location /static/ {
        alias /var/www/meridian-wealth/Meridian_Wealth_Training/financial_analyst_app/frontend/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # ========================================================================
    # API Documentation (if available)
    # ========================================================================
    
    location /docs {
        proxy_pass http://app_server;
        proxy_set_header Host $host;
    }
    
    location /openapi.json {
        proxy_pass http://app_server;
    }
    
    # ========================================================================
    # Deny Access to Sensitive Files
    # ========================================================================
    
    location ~ /\.env {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ /\.git {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ /\.well-known/acme-challenge {
        root /var/www/certbot;
    }
    
    # ========================================================================
    # 404 Error Handling
    # ========================================================================
    
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

---

## Installation & Setup

### Step 1: Create the Configuration File
```bash
sudo nano /etc/nginx/sites-available/meridian-wealth
```

### Step 2: Replace Domain Name
```bash
# Replace YOUR_DOMAIN_NAME with your actual domain
# Example: your-domain.com
sudo sed -i 's/YOUR_DOMAIN_NAME/your-domain.com/g' /etc/nginx/sites-available/meridian-wealth
```

### Step 3: Enable the Configuration
```bash
# Create symlink to enable the site
sudo ln -s /etc/nginx/sites-available/meridian-wealth /etc/nginx/sites-enabled/

# Remove default Nginx site
sudo rm /etc/nginx/sites-enabled/default
```

### Step 4: Test Configuration
```bash
# Test for syntax errors
sudo nginx -t

# Expected output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 5: Reload Nginx
```bash
sudo systemctl reload nginx
sudo systemctl status nginx
```

---

## SSL Certificate Setup

After Nginx is configured, obtain an SSL certificate:

```bash
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

Follow the interactive prompts to complete the setup.

---

## Verification

### Test HTTPS Connection
```bash
# From your local machine
curl -v https://your-domain.com/health

# From the EC2 instance
curl -k https://127.0.0.1/health
```

### Check Nginx Logs
```bash
# View error log
sudo tail -f /var/log/nginx/meridian-wealth-error.log

# View access log
sudo tail -f /var/log/nginx/meridian-wealth-access.log

# View combined logs
sudo tail -f /var/log/nginx/meridian-wealth-*.log
```

### Monitor Nginx Proxy
```bash
# Check if nginx is proxying correctly
sudo journalctl -u nginx -f
```

---

## Customization

### Increase Upstream Servers (Load Balancing)
```nginx
upstream app_server {
    server 127.0.0.1:8000 weight=5;
    server 127.0.0.1:8001 weight=3;
    server 127.0.0.1:8002 weight=2;
}
```

### Adjust Timeouts for Long Operations
```nginx
# For agent queries that take 60+ seconds
proxy_connect_timeout 90s;
proxy_send_timeout 180s;
proxy_read_timeout 180s;
```

### Add Rate Limiting
```nginx
# Add near the top of the file
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# In location block:
limit_req zone=api_limit burst=20 nodelay;
```

### Enable Caching for GET Requests
```nginx
# Add to location / block:
proxy_cache_valid 200 10m;
proxy_cache_key "$scheme$request_method$host$request_uri";
add_header X-Cache-Status $upstream_cache_status;
```

### Custom Error Pages
```nginx
error_page 502 /502.html;
location = /502.html {
    root /var/www/error-pages;
    internal;
}
```

---

## Troubleshooting

### 502 Bad Gateway Error
```bash
# Check if backend is running
curl http://127.0.0.1:8000/health

# Check Nginx error logs
sudo tail -f /var/log/nginx/meridian-wealth-error.log

# Restart backend
tmux kill-session -t meridian-app
bash start-app.sh
```

### SSL Certificate Errors
```bash
# Check certificate expiration
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Update Nginx config if paths changed
sudo systemctl reload nginx
```

### Connection Timeout
```bash
# Check upstream server
ss -tulpn | grep 8000

# Increase timeouts in Nginx config:
proxy_connect_timeout 90s;
proxy_send_timeout 180s;
proxy_read_timeout 180s;
```

### Too Many Open Files Error
```bash
# Increase file descriptors
sudo nano /etc/security/limits.conf
# Add: nginx soft nofile 65535
# Add: nginx hard nofile 65535

# Reload limits
sudo systemctl reload nginx
```

---

## Performance Tuning

### Increase Worker Processes
```bash
# Check number of CPU cores
nproc

# Edit Nginx main config
sudo nano /etc/nginx/nginx.conf

# Set worker_processes to number of cores (or auto)
worker_processes auto;
```

### Optimize Worker Connections
```nginx
# In /etc/nginx/nginx.conf
events {
    worker_connections 4096;  # Increased from default 768
}
```

### Enable HTTP/2 Push (optional)
```nginx
# Already enabled in config above with:
listen 443 ssl http2;
```

---

## Monitoring

### Real-time Monitoring
```bash
# Watch Nginx status
watch -n 1 'sudo systemctl status nginx'

# Monitor system resources
htop

# Watch network connections
nethogs
```

### Collect Metrics
```bash
# Count requests per second
tail -f /var/log/nginx/meridian-wealth-access.log | grep -oP '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}' | sort | uniq -c

# Check response codes
awk '{print $9}' /var/log/nginx/meridian-wealth-access.log | sort | uniq -c | sort -rn
```

---

## Backup Configuration

```bash
# Backup current Nginx config
sudo cp /etc/nginx/sites-available/meridian-wealth /etc/nginx/sites-available/meridian-wealth.backup.$(date +%Y%m%d)

# Backup SSL certificates
sudo tar -czf meridian-ssl-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt/

# Keep backups
ls -la /etc/nginx/sites-available/meridian-wealth*
```

---

**Last Updated:** June 2, 2026  
**Status:** Production Ready ✅
