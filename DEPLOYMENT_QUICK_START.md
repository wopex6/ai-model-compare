# Production Deployment - Quick Start Guide
## Get AI Model Compare running in production in 15 minutes

---

## **Choose Your Deployment Method**

### **Option 1: One-Command VPS Deployment** ⭐ (Recommended)

**Requirements:**
- Ubuntu 20.04+ or Debian 11+ server
- Root SSH access
- Domain name pointed to server IP

**Steps:**

1. **SSH into your server:**
```bash
ssh root@your-server-ip
```

2. **Download and run deployment script:**
```bash
cd /tmp
wget https://raw.githubusercontent.com/wopex6/ai-model-compare/main/deployment/deploy.sh
sudo bash deploy.sh your-domain.com
```

3. **Add your OpenAI API key:**
```bash
sudo nano /var/www/ai-model-compare/.env
# Change: OPENAI_API_KEY=your-actual-key-here
```

4. **Restart the app:**
```bash
sudo systemctl restart ai-model-compare
```

5. **Done!** Visit: `https://your-domain.com`

---

### **Option 2: Docker Deployment** 🐳 (Easiest)

**Requirements:**
- Docker and Docker Compose installed
- Domain name (optional for local testing)

**Steps:**

1. **Clone the repository:**
```bash
git clone https://github.com/wopex6/ai-model-compare.git
cd ai-model-compare
```

2. **Create .env file:**
```bash
cp .env.example .env
nano .env
# Add your OPENAI_API_KEY and generate SECRET_KEY
```

3. **Update domain in nginx config:**
```bash
sed -i 's/your-domain.com/yourdomain.com/g' deployment/nginx.conf
```

4. **Start everything:**
```bash
docker-compose up -d
```

5. **Done!** Visit: `http://localhost` (or your domain)

**Check status:**
```bash
docker-compose ps
docker-compose logs -f
```

---

### **Option 3: Cloud Platform** ☁️ (Simplest)

#### **Heroku:**

```bash
# 1. Install Heroku CLI and login
heroku login

# 2. Create app
heroku create your-app-name

# 3. Set environment variables
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

# 4. Deploy
git push heroku main

# 5. Open
heroku open
```

#### **Railway:**

1. Go to https://railway.app
2. Click "Deploy from GitHub"
3. Select your repository
4. Add environment variables (OPENAI_API_KEY, SECRET_KEY)
5. Railway auto-deploys!

#### **Render:**

1. Go to https://render.com
2. Click "New Web Service"
3. Connect GitHub repository
4. Add environment variables
5. Render auto-deploys!

---

## **Critical Environment Variables**

### **Required:**

```bash
OPENAI_API_KEY=sk-your-actual-key-here      # MUST set this!
SECRET_KEY=generate-with-command-below       # MUST be random!
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### **Recommended:**

```bash
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_PATH=./databases/production_integrated_users.db
DISABLE_AUTO_DOCS=true
LOG_LEVEL=INFO
```

---

## **Database Migration**

### **Option A: Fresh Start** (Recommended)

Users register new accounts. Database creates automatically.

### **Option B: Migrate Existing Data**

```bash
# 1. Backup local databases
cp integrated_users.db backups/

# 2. Copy to production
scp integrated_users.db user@server:/var/www/ai-model-compare/databases/production_integrated_users.db

# 3. Set permissions
sudo chown www-data:www-data /var/www/ai-model-compare/databases/*.db
```

### **Important Databases:**

1. **`integrated_users.db`** - Users, sessions, conversations
2. **`smart_response.db`** - Learning data, AI usage logs
3. **`conversations/`** - 5715 legacy JSON files (optional to migrate)
4. **`user_profiles/`** - Personality data

**Backup command:**
```bash
sqlite3 production_integrated_users.db ".backup 'backup_$(date +%Y%m%d).db'"
```

---

## **Post-Deployment Checklist**

### **1. Verify App is Running:**

```bash
# Check status
sudo systemctl status ai-model-compare

# Check logs
sudo journalctl -u ai-model-compare -f

# Test endpoint
curl https://your-domain.com/health
```

### **2. Test All Features:**

- [ ] Visit homepage
- [ ] Register new account
- [ ] Login
- [ ] Test scientist chat
- [ ] Test each of 8 characters
- [ ] Send messages
- [ ] Refresh page (history loads)
- [ ] Check Smart Response badges ([SR] vs [AI])
- [ ] Test logout

### **3. Setup Monitoring:**

```bash
# Watch logs
sudo tail -f /var/www/ai-model-compare/logs/app.log

# Watch Nginx
sudo tail -f /var/log/nginx/ai-model-compare-access.log

# Monitor resources
htop
```

### **4. Verify Backups:**

```bash
# Check backup cron
crontab -l

# Test backup manually
sudo /usr/local/bin/backup-ai-db.sh

# Verify backups exist
ls -lh /var/backups/ai-model-compare/
```

---

## **Common Issues & Fixes**

### **App Won't Start:**

```bash
# Check logs
sudo journalctl -u ai-model-compare -n 50

# Check if port 8000 is in use
sudo lsof -i :8000

# Test manually
cd /var/www/ai-model-compare
source venv/bin/activate
python app.py
```

### **Database Errors:**

```bash
# Check permissions
ls -la /var/www/ai-model-compare/databases/

# Test connection
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) FROM users;"

# Rebuild if needed (WARNING: loses data!)
mv databases/production_integrated_users.db databases/backup.db
python -c "from app import db; db.execute('SELECT 1')"
```

### **Nginx Errors:**

```bash
# Test config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Restart
sudo systemctl restart nginx
```

### **SSL Certificate Issues:**

```bash
# Manual certificate generation
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

---

## **Costs Breakdown**

### **Infrastructure:**

| Provider | Plan | Cost/Month |
|----------|------|------------|
| DigitalOcean | 2GB Droplet | $12 |
| AWS EC2 | t3.small | $15-30 |
| Heroku | Hobby | $7 |
| Railway | Starter | $5 |
| Render | Starter | $7 |

### **Domain:**
- .com: $12/year (~$1/month)
- .ai: $180/year (~$15/month)
- .tech: $30/year (~$2.50/month)

### **SSL:**
- Let's Encrypt: **FREE** ✅

### **AI Usage:**

| Users | Messages/Day | Cost/Month |
|-------|--------------|------------|
| 10 | 100 total | $6 |
| 100 | 1,000 total | $60 |
| 500 | 5,000 total | $300 |

**With Smart Response:** ~40% reduction (60% quick replies)

### **Total Estimated:**

- **Small (10-50 users):** $20-30/month
- **Medium (100-500 users):** $70-100/month
- **Large (500-1000 users):** $300-400/month

---

## **Maintenance Commands**

### **Update Application:**

```bash
cd /var/www/ai-model-compare
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-model-compare
```

### **View Logs:**

```bash
# Application
sudo journalctl -u ai-model-compare -f

# Nginx access
sudo tail -f /var/log/nginx/ai-model-compare-access.log

# Nginx errors
sudo tail -f /var/log/nginx/ai-model-compare-error.log
```

### **Database Maintenance:**

```bash
# Vacuum (monthly)
sqlite3 databases/production_integrated_users.db "VACUUM;"

# Analyze (monthly)
sqlite3 databases/production_integrated_users.db "ANALYZE;"

# Check size
du -sh databases/
```

### **Restart Services:**

```bash
# Restart app
sudo systemctl restart ai-model-compare

# Restart Nginx
sudo systemctl restart nginx

# Restart both
sudo systemctl restart ai-model-compare nginx
```

---

## **Security Checklist**

- [ ] HTTPS enabled (SSL certificate)
- [ ] Firewall configured (ufw)
- [ ] Strong SECRET_KEY generated
- [ ] .env file not in git
- [ ] Database files have correct permissions (660)
- [ ] App runs as non-root user (www-data)
- [ ] Rate limiting enabled in Nginx
- [ ] Security headers configured
- [ ] Automatic backups working
- [ ] Monitoring in place

---

## **Getting Help**

### **Documentation:**
- Full guide: `PRODUCTION_DEPLOYMENT.md`
- Architecture: `INTELLIGENT_CONTEXT_ARCHITECTURE.md`
- Character tuning: `SMART_RESPONSE_TUNING.md`
- Testing: `COMPLETE_TESTING_GUIDE.md`

### **Logs to Check:**
- App: `/var/www/ai-model-compare/logs/app.log`
- Systemd: `sudo journalctl -u ai-model-compare`
- Nginx: `/var/log/nginx/ai-model-compare-*.log`

### **Common Log Locations:**
```bash
# All in one place
cd /var/www/ai-model-compare
ls -la logs/

# System logs
sudo ls -la /var/log/nginx/
```

---

## **Next Steps After Deployment**

1. **Test thoroughly** - All 8 characters, all features
2. **Monitor for 24 hours** - Watch logs, check for errors
3. **Setup alerts** (optional) - Email on errors, budget alerts
4. **Document your setup** - Note any custom configurations
5. **Plan scaling** - When to upgrade server/add features

---

## **Success Criteria**

✅ App accessible at your domain
✅ HTTPS working (green padlock)
✅ All 8 characters functional
✅ User registration/login works
✅ Chat messages save and persist
✅ Smart Response working ([SR] badges)
✅ Backups running automatically
✅ Under budget target

---

## **Quick Reference**

**Start app:** `sudo systemctl start ai-model-compare`
**Stop app:** `sudo systemctl stop ai-model-compare`
**Restart app:** `sudo systemctl restart ai-model-compare`
**View status:** `sudo systemctl status ai-model-compare`
**View logs:** `sudo journalctl -u ai-model-compare -f`
**Update code:** `cd /var/www/ai-model-compare && git pull && sudo systemctl restart ai-model-compare`

**Docker:**
**Start:** `docker-compose up -d`
**Stop:** `docker-compose down`
**Logs:** `docker-compose logs -f`
**Restart:** `docker-compose restart`

---

**Good luck with your deployment!** 🚀

If you encounter issues, check `PRODUCTION_DEPLOYMENT.md` for detailed troubleshooting.
