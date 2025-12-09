# Production Deployment Guide
## Complete checklist for deploying AI Model Compare to production

---

## **Pre-Deployment Checklist**

### **✅ Code Status:**
- [x] All 7 character templates migrated to ConversationBox
- [x] Smart Response system functional
- [x] Database integration complete
- [x] JWT authentication implemented
- [x] All issues fixed (CSS, badges, templates)
- [x] Code pushed to GitHub

### **🗄️ Databases to Backup/Migrate:**

1. **`integrated_users.db`** - Main user database
   - Users table (credentials, profiles)
   - User sessions (per character)
   - Conversation history (dual-layer)
   - Smart Response learning data

2. **`smart_response.db`** - Smart Response system
   - User interaction history
   - User style learning profiles
   - AI usage logs
   - Budget tracking

3. **`conversations/`** - Legacy JSON sessions (5715 files)
   - May be needed for data recovery
   - Consider archiving vs migrating

4. **`user_profiles/`** - User personality profiles
   - User-specific data
   - Should be migrated to production

---

## **Environment Variables Required**

### **Critical (Must Set):**

```bash
# API Keys
OPENAI_API_KEY=sk-...                    # Required for AI responses
SECRET_KEY=your-super-secret-key-here    # Required for JWT auth

# Database (Optional - defaults to development)
DATABASE_PATH=./production_integrated_users.db
SMART_RESPONSE_DB=./production_smart_response.db

# Environment
FLASK_ENV=production
FLASK_DEBUG=0

# Security
SESSION_COOKIE_SECURE=True               # HTTPS only
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### **Optional (Recommended):**

```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Performance
WORKERS=4                                # Gunicorn workers
THREADS=2                                # Threads per worker

# AI Budget (Production limits)
MAX_AI_CALLS_PER_DAY=100                # Per user
ADMIN_AI_CALLS_PER_DAY=1000             # For admin testing
SYSTEM_AI_CALL_CAP=2000                 # Hard system limit
```

---

## **Production Server Setup**

### **Option 1: Traditional VPS (DigitalOcean, AWS EC2, etc.)**

#### **1. Install Dependencies:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx
sudo apt install nginx -y

# Install Git
sudo apt install git -y
```

#### **2. Clone Repository:**

```bash
cd /var/www
sudo git clone https://github.com/wopex6/ai-model-compare.git
cd ai-model-compare
```

#### **3. Setup Python Environment:**

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### **4. Create Environment File:**

```bash
sudo nano .env
```

**Contents:**
```ini
OPENAI_API_KEY=sk-your-actual-key-here
SECRET_KEY=generate-a-strong-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_PATH=./production_integrated_users.db
SMART_RESPONSE_DB=./production_smart_response.db
SESSION_COOKIE_SECURE=True
LOG_LEVEL=INFO
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### **5. Migrate Databases:**

```bash
# Create production databases directory
mkdir -p /var/www/ai-model-compare/databases

# Copy development databases (if migrating data)
scp local_path/integrated_users.db server:/var/www/ai-model-compare/databases/production_integrated_users.db
scp local_path/smart_response.db server:/var/www/ai-model-compare/databases/production_smart_response.db

# OR start fresh (recommended for production)
python3 -c "from app import db; db.execute('SELECT 1')"  # Auto-creates tables
```

#### **6. Setup Gunicorn (Production WSGI Server):**

Create `gunicorn_config.py`:
```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "./logs/access.log"
errorlog = "./logs/error.log"
loglevel = "info"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

Install Gunicorn:
```bash
pip install gunicorn
```

#### **7. Create Systemd Service:**

```bash
sudo nano /etc/systemd/system/ai-model-compare.service
```

**Contents:**
```ini
[Unit]
Description=AI Model Compare Flask App
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-model-compare
Environment="PATH=/var/www/ai-model-compare/venv/bin"
ExecStart=/var/www/ai-model-compare/venv/bin/gunicorn --config gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-model-compare
sudo systemctl start ai-model-compare
sudo systemctl status ai-model-compare
```

#### **8. Setup Nginx Reverse Proxy:**

```bash
sudo nano /etc/nginx/sites-available/ai-model-compare
```

**Contents:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (use Certbot/Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/ai-model-compare-access.log;
    error_log /var/log/nginx/ai-model-compare-error.log;

    # Static files
    location /static {
        alias /var/www/ai-model-compare/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;

    # Max upload size
    client_max_body_size 10M;
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/ai-model-compare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### **9. Setup SSL with Let's Encrypt:**

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo certbot renew --dry-run  # Test auto-renewal
```

#### **10. Setup Firewall:**

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

---

### **Option 2: Docker Deployment (Recommended)**

#### **1. Create `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs databases conversations user_profiles

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
```

#### **2. Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: ai-model-compare
    restart: always
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
      - FLASK_DEBUG=0
      - DATABASE_PATH=/app/databases/production_integrated_users.db
      - SMART_RESPONSE_DB=/app/databases/production_smart_response.db
    volumes:
      - ./databases:/app/databases
      - ./logs:/app/logs
      - ./conversations:/app/conversations
      - ./user_profiles:/app/user_profiles
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: ai-model-compare-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/app/static:ro
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - app
```

#### **3. Deploy with Docker:**

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

---

### **Option 3: Cloud Platform (Heroku, Railway, Render)**

#### **Heroku Example:**

1. **Create `Procfile`:**
```
web: gunicorn app:app
```

2. **Create `runtime.txt`:**
```
python-3.11.0
```

3. **Deploy:**
```bash
heroku login
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SECRET_KEY=your-secret
git push heroku main
```

---

## **Database Migration Strategy**

### **Option A: Migrate Existing Data** (If users exist)

```bash
# 1. Backup local databases
cp integrated_users.db backups/integrated_users_$(date +%Y%m%d).db
cp smart_response.db backups/smart_response_$(date +%Y%m%d).db

# 2. Copy to production server
scp integrated_users.db user@server:/var/www/ai-model-compare/databases/production_integrated_users.db
scp smart_response.db user@server:/var/www/ai-model-compare/databases/production_smart_response.db

# 3. Set permissions
sudo chown www-data:www-data /var/www/ai-model-compare/databases/*.db
sudo chmod 664 /var/www/ai-model-compare/databases/*.db
```

### **Option B: Fresh Start** (Recommended for production)

```bash
# Tables will be created automatically on first run
# Users will need to register fresh
```

### **Option C: Selective Migration** (Recommended)

```bash
# Export important data only
sqlite3 integrated_users.db "SELECT * FROM users WHERE created_at > date('now', '-30 days');" > recent_users.csv

# Import to production after deployment
```

---

## **Post-Deployment Checklist**

### **1. Health Checks:**

```bash
# Test app is running
curl https://your-domain.com/health

# Test login
curl -X POST https://your-domain.com/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Test character endpoints
curl https://your-domain.com/scientist
curl https://your-domain.com/life_coach
```

### **2. Monitor Logs:**

```bash
# Application logs
tail -f logs/app.log

# Nginx access logs
sudo tail -f /var/log/nginx/ai-model-compare-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/ai-model-compare-error.log

# Systemd logs
sudo journalctl -u ai-model-compare -f
```

### **3. Database Backups:**

```bash
# Create backup script
sudo nano /usr/local/bin/backup-ai-db.sh
```

**Contents:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/ai-model-compare"
DB_PATH="/var/www/ai-model-compare/databases"

mkdir -p $BACKUP_DIR

# Backup databases
sqlite3 $DB_PATH/production_integrated_users.db ".backup '$BACKUP_DIR/integrated_users_$DATE.db'"
sqlite3 $DB_PATH/production_smart_response.db ".backup '$BACKUP_DIR/smart_response_$DATE.db'"

# Compress
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/*_$DATE.db
rm $BACKUP_DIR/*_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Make executable and schedule:**
```bash
sudo chmod +x /usr/local/bin/backup-ai-db.sh

# Add to crontab (daily at 3 AM)
sudo crontab -e
# Add: 0 3 * * * /usr/local/bin/backup-ai-db.sh >> /var/log/backup-ai-db.log 2>&1
```

### **4. Monitoring Setup:**

```bash
# Install monitoring tools
sudo apt install htop iotop -y

# Monitor processes
htop

# Monitor disk usage
df -h

# Monitor database size
du -sh databases/
```

---

## **Security Hardening**

### **1. File Permissions:**

```bash
# Set proper ownership
sudo chown -R www-data:www-data /var/www/ai-model-compare

# Secure permissions
sudo chmod 750 /var/www/ai-model-compare
sudo chmod 640 /var/www/ai-model-compare/.env
sudo chmod 660 /var/www/ai-model-compare/databases/*.db
```

### **2. Environment Variables:**

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets manager (AWS Secrets Manager, etc.) in production
```

### **3. Rate Limiting:**

Add to Nginx config:
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

location /login {
    limit_req zone=login burst=3 nodelay;
    # ... rest of config
}

location /api {
    limit_req zone=api burst=20 nodelay;
    # ... rest of config
}
```

### **4. Fail2Ban:**

```bash
sudo apt install fail2ban -y

# Create jail for app
sudo nano /etc/fail2ban/jail.d/ai-model-compare.conf
```

**Contents:**
```ini
[ai-model-compare]
enabled = true
port = http,https
filter = ai-model-compare
logpath = /var/log/nginx/ai-model-compare-error.log
maxretry = 5
bantime = 3600
```

---

## **Performance Optimization**

### **1. Enable Caching:**

```python
# Add to app.py
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/static/<path:filename>')
@cache.cached(timeout=86400)  # 24 hours
def serve_static(filename):
    return send_from_directory('static', filename)
```

### **2. Database Optimization:**

```bash
# Vacuum databases monthly
sqlite3 production_integrated_users.db "VACUUM;"
sqlite3 production_smart_response.db "VACUUM;"

# Analyze for query optimization
sqlite3 production_integrated_users.db "ANALYZE;"
```

### **3. CDN for Static Files (Optional):**

- Upload `/static` folder to CDN (Cloudflare, AWS CloudFront)
- Update URLs in templates to point to CDN

---

## **Cost Estimation**

### **Infrastructure:**

| Service | Cost/Month | Notes |
|---------|------------|-------|
| **DigitalOcean Droplet** | $12-24 | 2-4GB RAM |
| **AWS EC2 t3.small** | $15-30 | With reserved instance |
| **Heroku Hobby** | $7 | Simple deployment |
| **Railway/Render** | $5-20 | Easy deployment |
| **Domain** | $1-15 | .com/.ai/.tech |
| **SSL Certificate** | $0 | Free with Let's Encrypt |

### **AI Costs:**

| Usage | Cost/Month | Notes |
|-------|------------|-------|
| **100 users, 10 msg/day** | ~$60 | 30k messages × $0.002 |
| **500 users, 10 msg/day** | ~$300 | 150k messages × $0.002 |
| **With Smart Response** | ~40% less | 60% quick replies |

**Total estimated:** $20-80/month (infrastructure + AI)

---

## **Rollback Plan**

### **If deployment fails:**

```bash
# 1. Stop new version
sudo systemctl stop ai-model-compare

# 2. Restore previous code
cd /var/www/ai-model-compare
git checkout [previous-commit-hash]

# 3. Restore databases
cp backups/integrated_users_backup.db databases/production_integrated_users.db
cp backups/smart_response_backup.db databases/production_smart_response.db

# 4. Restart
sudo systemctl start ai-model-compare

# 5. Verify
curl https://your-domain.com/health
```

---

## **Maintenance Schedule**

### **Daily:**
- [ ] Monitor logs for errors
- [ ] Check application health

### **Weekly:**
- [ ] Review AI usage and costs
- [ ] Check database size
- [ ] Review user feedback

### **Monthly:**
- [ ] Update dependencies (`pip list --outdated`)
- [ ] VACUUM databases
- [ ] Review and delete old backups
- [ ] Security updates (`sudo apt update && sudo apt upgrade`)

### **Quarterly:**
- [ ] Rotate SSL certificates (automated with certbot)
- [ ] Review and optimize database queries
- [ ] Performance testing
- [ ] Update documentation

---

## **Quick Deployment Commands**

### **Deploy from scratch (Ubuntu/Debian):**

```bash
#!/bin/bash
# Quick production deployment script

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git -y

# 3. Clone and setup
cd /var/www
sudo git clone https://github.com/wopex6/ai-model-compare.git
cd ai-model-compare
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Create environment file
echo "OPENAI_API_KEY=your-key-here
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
FLASK_DEBUG=0" | sudo tee .env

# 5. Setup systemd service
sudo cp deployment/ai-model-compare.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-model-compare
sudo systemctl start ai-model-compare

# 6. Setup nginx
sudo cp deployment/nginx.conf /etc/nginx/sites-available/ai-model-compare
sudo ln -s /etc/nginx/sites-available/ai-model-compare /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 7. Setup SSL
sudo certbot --nginx -d your-domain.com

# 8. Setup firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable

echo "Deployment complete!"
echo "Visit: https://your-domain.com"
```

---

## **Troubleshooting**

### **App won't start:**

```bash
# Check logs
sudo journalctl -u ai-model-compare -n 50

# Check permissions
ls -la /var/www/ai-model-compare

# Check environment
cat .env

# Test manually
cd /var/www/ai-model-compare
source venv/bin/activate
python app.py
```

### **Database errors:**

```bash
# Check database permissions
ls -la databases/

# Test database connection
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) FROM users;"

# Rebuild if corrupted
mv databases/production_integrated_users.db databases/corrupted_backup.db
python -c "from app import db; db.execute('SELECT 1')"
```

### **Nginx errors:**

```bash
# Test config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Restart
sudo systemctl restart nginx
```

---

## **Success Criteria**

✅ **App accessible** at https://your-domain.com
✅ **All 8 characters** load correctly
✅ **User registration** works
✅ **Chat functionality** works
✅ **Smart Response** triggers correctly
✅ **Database** persists conversations
✅ **SSL certificate** valid
✅ **Backups** running automatically
✅ **Monitoring** in place
✅ **Under budget** ($80/month max)

---

**Document Created:** Dec 9, 2025, 9:50 PM  
**Status:** Ready for deployment  
**Estimated time:** 2-4 hours for full production setup
