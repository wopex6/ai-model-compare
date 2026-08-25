# 🚀 AI Life Companion - Deployment Guide

**Last Updated:** June 26, 2026  
**Version:** 2.0  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Production Deployment (PythonAnywhere)](#production-deployment-pythonanywhere)
5. [Database Management](#database-management)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

---

## 🎯 Prerequisites

### **System Requirements**
- **Python:** 3.9 or higher
- **Database:** SQLite (included) or PostgreSQL (for production)
- **Memory:** Minimum 2GB RAM, 4GB recommended
- **Storage:** Minimum 10GB free space
- **Network:** Stable internet connection for AI APIs

### **API Keys Required**
- **OpenAI API Key** - For GPT models
- **Anthropic API Key** - For Claude models (optional)
- **Secret Key** - For JWT token signing

### **Development Tools**
- **Git** - Version control
- **Code Editor** - VS Code recommended
- **Browser** - Chrome/Firefox for testing

---

## 🛠️ Environment Setup

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/ai-model-compare.git
cd ai-model-compare
```

### **2. Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
```

### **5. Environment Variables (.env)**
```env
# AI Provider Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Security
SECRET_KEY=your_secret_key_for_jwt_sessions
FLASK_ENV=development

# Database (SQLite default)
DATABASE_URL=sqlite:///integrated_users.db

# Optional: PostgreSQL for production
# DATABASE_URL=postgresql://user:password@localhost/dbname

# AI Budget Settings
AI_DAILY_LIMIT=100
AI_HOURLY_LIMIT=30

# File Upload Settings
MAX_FILE_SIZE=52428800  # 50MB in bytes
UPLOAD_FOLDER=uploads

# Email Settings (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## 💻 Local Development

### **1. Initialize Database**
```bash
python app.py --init-db
```

### **2. Run Development Server**
```bash
python app.py
```

### **3. Access Application**
- **Main App:** http://localhost:5000
- **Admin Dashboard:** http://localhost:5000/admin/analytics
- **API Documentation:** http://localhost:5000/api/docs

### **4. Create Admin User**
```bash
python create_admin_user.py
```

### **5. Testing**
```bash
# Run comprehensive tests
python tests/test_comprehensive.py

# Run specific tests
python test_new_features_playwright.py
```

---

## 🌐 Production Deployment (PythonAnywhere)

### **1. PythonAnywhere Setup**
1. **Create Account:** Sign up at pythonanywhere.com
2. **Choose Plan:** Free tier for testing, paid for production
3. **Create Web App:** Bash console → Web tab → Add new web app

### **2. Configure Web App**
```bash
# Web App Configuration
Python version: 3.9+
Working directory: /home/yourusername/ai-model-compare
WSGI file: /home/yourusername/ai-model-compare/pythonanywhere_wsgi.py
```

### **3. Upload Code**
```bash
# Method 1: Git clone
git clone https://github.com/yourusername/ai-model-compare.git

# Method 2: Zip upload
# Upload zip file and extract in console
```

### **4. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **5. Configure Environment**
```bash
# Create .env file
nano .env

# Add your production keys
```

### **6. Database Setup**
```bash
# Initialize production database
python app.py --init-db

# Create admin user
python create_admin_user.py
```

### **7. Configure WSGI**
Edit `pythonanywhere_wsgi.py`:
```python
import sys
path = '/home/yourusername/ai-model-compare'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

### **8. Static Files Configuration**
```bash
# In PythonAnywhere Web tab
Static files URL: /static/
Static files directory: /home/yourusername/ai-model-compare/static/
```

### **9. Reload Web App**
```bash
# In PythonAnywhere Web tab
Click "Reload" button
```

---

## 🗄️ Database Management

### **SQLite (Default)**
```bash
# Backup database
cp integrated_users.db backup_$(date +%Y%m%d_%H%M%S).db

# Restore database
cp backup_20231201_120000.db integrated_users.db

# View database schema
sqlite3 integrated_users.db ".schema"
```

### **PostgreSQL (Production)**
```bash
# Create database
createdb ai_companion

# Backup database
pg_dump ai_companion > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
psql ai_companion < backup_20231201_120000.sql
```

### **Database Migrations**
```bash
# Run migration script
python apply_schema_migration.py

# Verify migration
python verify_database_schema.py
```

---

## 📊 Monitoring & Maintenance

### **1. System Monitoring**
```bash
# Check system status
python check_production_database.py

# Monitor AI usage
python -c "from smart_response.ai_budget_manager import AIBudgetManager; print(AIBudgetManager().get_daily_usage())"
```

### **2. Log Management**
```bash
# View application logs
tail -f /var/log/your_app.log

# Monitor error logs
grep ERROR /var/log/your_app.log
```

### **3. Automated Backups**
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp integrated_users.db backups/backup_$DATE.db
find backups/ -name "backup_*.db" -mtime +7 -delete
EOF

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### **4. Performance Monitoring**
- **AI Budget Alerts:** Automatic at 80% and 100%
- **Error Tracking:** Comprehensive error logging
- **Response Times:** Monitor API performance
- **User Analytics:** Track usage patterns

---

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Database Connection Error**
```bash
# Check database file exists
ls -la integrated_users.db

# Check permissions
chmod 664 integrated_users.db

# Recreate database
python app.py --init-db
```

#### **2. API Key Issues**
```bash
# Verify API keys
python check_openai_account.py

# Test API connectivity
python -c "import openai; print(openai.Model.list())"
```

#### **3. Memory Issues**
```bash
# Check memory usage
free -h

# Restart application
python app.py --restart
```

#### **4. Static Files Not Loading**
```bash
# Check static file permissions
chmod -R 755 static/

# Verify static file configuration in PythonAnywhere
```

### **Error Codes**
- **401:** Authentication failed - Check JWT secret
- **403:** Insufficient permissions - Check user roles
- **429:** Rate limit exceeded - Check AI budget
- **500:** Internal error - Check application logs

### **Debug Mode**
```bash
# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with debug output
python app.py --debug
```

---

## 🔐 Security Considerations

### **1. API Key Security**
- Never commit API keys to version control
- Use environment variables for all secrets
- Rotate API keys regularly
- Monitor API usage for anomalies

### **2. Database Security**
```bash
# Set appropriate file permissions
chmod 640 integrated_users.db
chmod 750 .env
```

### **3. Web Security**
- Enable HTTPS in production
- Use secure cookies for sessions
- Implement rate limiting
- Validate all user inputs

### **4. Backup Security**
```bash
# Encrypt backups
gpg --symmetric --cipher-algo AES256 backup_20231201.db

# Secure backup storage
chmod 600 backup_20231201.db.gpg
```

---

## 📈 Performance Optimization

### **1. Database Optimization**
```sql
-- Create indexes for better performance
CREATE INDEX idx_history_timestamp ON history_primary(timestamp);
CREATE INDEX idx_user_messages ON history_primary(user_id, timestamp);
```

### **2. Caching**
```python
# Enable response caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

### **3. AI Call Optimization**
- Use appropriate model sizes
- Implement response caching
- Batch similar requests
- Monitor token usage

---

## 🔄 Updates & Maintenance

### **1. Update Dependencies**
```bash
# Update requirements
pip-review --local --interactive

# Update specific packages
pip install --upgrade package_name
```

### **2. Deploy Updates**
```bash
# Pull latest changes
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations if needed
python apply_schema_migration.py

# Restart application
python app.py --restart
```

### **3. Version Control**
```bash
# Tag releases
git tag -a v2.0 -m "Production release v2.0"
git push origin v2.0

# Create release branch
git checkout -b release/v2.0
```

---

## 📞 Support & Resources

### **Documentation**
- **Architecture Overview:** `ARCHITECTURE_OVERVIEW.md`
- **System Design Principles:** `SYSTEM_DESIGN_PRINCIPLES.md`
- **API Documentation:** `/api/docs` endpoint
- **Implementation Status:** `IMPLEMENTATION_STATUS.md`

### **Monitoring Dashboards**
- **Admin Analytics:** `/admin/analytics`
- **AI Budget Status:** `/api/ai-budget/status`
- **System Health:** `/api/health`

### **Emergency Procedures**
1. **Circuit Breaker Activation:** Manual reset via `/api/ai-budget/reset-circuit-breaker`
2. **Database Recovery:** Restore from latest backup
3. **System Rollback:** Use Git tags to revert changes

---

## ✅ Deployment Checklist

### **Pre-Deployment**
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Admin user created
- [ ] API keys verified
- [ ] Backup strategy in place

### **Post-Deployment**
- [ ] Application accessible
- [ ] All features working
- [ ] Monitoring active
- [ ] Logs configured
- [ ] Security measures verified
- [ ] Documentation updated

---

## 🎉 Success Metrics

### **Deployment Success Indicators**
- ✅ Application loads without errors
- ✅ User authentication working
- ✅ AI responses functional
- ✅ Database operations successful
- ✅ Admin dashboard accessible
- ✅ Budget monitoring active

### **Performance Targets**
- **Page Load Time:** < 3 seconds
- **API Response Time:** < 2 seconds
- **AI Response Time:** < 10 seconds
- **Uptime:** > 99%
- **Error Rate:** < 1%

---

**🚀 Your AI Life Companion is now ready for production!**

For additional support, refer to the comprehensive documentation in the repository or contact the development team.

---

*Last Updated: June 26, 2026*  
*Version: 2.0*  
*Status: Production Ready*
