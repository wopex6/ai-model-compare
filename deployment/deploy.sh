#!/bin/bash
# Quick Production Deployment Script for AI Model Compare
# Usage: sudo bash deploy.sh your-domain.com

set -e  # Exit on error

DOMAIN=$1
if [ -z "$DOMAIN" ]; then
    echo "❌ Error: Domain name required"
    echo "Usage: sudo bash deploy.sh your-domain.com"
    exit 1
fi

echo "🚀 Starting deployment for $DOMAIN..."

# 1. Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# 2. Install dependencies
echo "📦 Installing dependencies..."
apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git sqlite3

# 3. Create application directory
echo "📁 Setting up application directory..."
mkdir -p /var/www
cd /var/www

# 4. Clone repository (if not exists)
if [ ! -d "ai-model-compare" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/wopex6/ai-model-compare.git
fi

cd ai-model-compare

# 5. Update code
echo "🔄 Updating code..."
git pull origin main

# 6. Create Python virtual environment
echo "🐍 Setting up Python environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 7. Create .env file (if not exists)
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment file..."
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    cat > .env << EOF
# Generated on $(date)
OPENAI_API_KEY=PLEASE_SET_YOUR_OPENAI_KEY
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_PATH=./databases/production_integrated_users.db
SMART_RESPONSE_DB=./databases/production_smart_response.db
SESSION_COOKIE_SECURE=True
DISABLE_AUTO_DOCS=true
LOG_LEVEL=INFO
MAX_AI_CALLS_PER_DAY=100
EOF

    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY!"
    echo "   Run: nano /var/www/ai-model-compare/.env"
    read -p "Press Enter after you've added your API key..."
fi

# 8. Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs databases conversations user_profiles

# 9. Set permissions
echo "🔒 Setting permissions..."
chown -R www-data:www-data /var/www/ai-model-compare
chmod 750 /var/www/ai-model-compare
chmod 640 .env
chmod 660 databases/*.db 2>/dev/null || true

# 10. Setup systemd service
echo "⚙️  Setting up systemd service..."
cp deployment/ai-model-compare.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ai-model-compare
systemctl restart ai-model-compare

# Wait for app to start
echo "⏳ Waiting for app to start..."
sleep 5

# Check if app is running
if systemctl is-active --quiet ai-model-compare; then
    echo "✅ Application is running!"
else
    echo "❌ Application failed to start. Check logs:"
    echo "   sudo journalctl -u ai-model-compare -n 50"
    exit 1
fi

# 11. Setup Nginx
echo "🌐 Setting up Nginx..."

# Update domain in nginx config
sed "s/your-domain.com/$DOMAIN/g" deployment/nginx.conf > /etc/nginx/sites-available/ai-model-compare

# Enable site
ln -sf /etc/nginx/sites-available/ai-model-compare /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test nginx config
nginx -t

# Restart nginx
systemctl restart nginx

# 12. Setup SSL with Let's Encrypt
echo "🔒 Setting up SSL certificate..."
read -p "Setup SSL certificate with Let's Encrypt? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email || \
        echo "⚠️  SSL setup failed. You can run manually: sudo certbot --nginx -d $DOMAIN"
fi

# 13. Setup firewall
echo "🔥 Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 'Nginx Full'
    ufw allow OpenSSH
    ufw --force enable
fi

# 14. Setup database backups
echo "💾 Setting up automatic backups..."
cat > /usr/local/bin/backup-ai-db.sh << 'EOF'
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

echo "✅ Backup completed: $DATE" >> /var/log/backup-ai-db.log
EOF

chmod +x /usr/local/bin/backup-ai-db.sh

# Add to crontab (daily at 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-ai-db.sh >> /var/log/backup-ai-db.log 2>&1") | crontab -

echo ""
echo "🎉 =========================================="
echo "🎉  DEPLOYMENT COMPLETE!"
echo "🎉 =========================================="
echo ""
echo "📍 Your site: https://$DOMAIN"
echo "📊 Status: sudo systemctl status ai-model-compare"
echo "📝 Logs: sudo journalctl -u ai-model-compare -f"
echo "🔄 Restart: sudo systemctl restart ai-model-compare"
echo ""
echo "⚠️  NEXT STEPS:"
echo "   1. Verify your OPENAI_API_KEY is set in /var/www/ai-model-compare/.env"
echo "   2. Visit https://$DOMAIN and test registration/login"
echo "   3. Test each character chat"
echo "   4. Monitor logs for the first 24 hours"
echo ""
echo "📚 Documentation: /var/www/ai-model-compare/PRODUCTION_DEPLOYMENT.md"
echo ""
