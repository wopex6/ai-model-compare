# +++++++++++ FLASK WSGI CONFIGURATION FOR PYTHONANYWHERE +++++++++++
# This file should be copied to your WSGI configuration in PythonAnywhere
# Location: /var/www/yourusername_pythonanywhere_com_wsgi.py
#
# INSTRUCTIONS:
# 1. In PythonAnywhere Web tab, click on WSGI configuration file
# 2. DELETE all existing content
# 3. COPY this entire file content
# 4. PASTE into WSGI configuration
# 5. CHANGE 'yourusername' to your actual PythonAnywhere username (3 places)
# 6. Save the file
# 7. Click "Reload" button in Web tab

import sys
import os
from dotenv import load_dotenv

# ===== IMPORTANT: CHANGE 'yourusername' TO YOUR ACTUAL USERNAME =====
project_home = '/home/yourusername/ai-model-compare'
# ====================================================================

# Add project directory to Python path
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Change to project directory
os.chdir(project_home)

# Load environment variables from .env file
# This must happen BEFORE importing app
env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️  WARNING: .env file not found at {env_path}")
    print("   Make sure to create .env file with OPENAI_API_KEY!")

# Set Python path for imports
sys.path.insert(0, project_home)

# Import Flask application
# PythonAnywhere requires the variable to be named 'application'
try:
    from app import app as application
    print("✅ Flask app imported successfully")
except Exception as e:
    print(f"❌ Error importing Flask app: {e}")
    raise

# Verify critical environment variables are set
if not os.getenv('OPENAI_API_KEY'):
    print("⚠️  WARNING: OPENAI_API_KEY not set in environment!")
    print("   Add it to your .env file: OPENAI_API_KEY=sk-your-key-here")

if not os.getenv('SECRET_KEY'):
    print("⚠️  WARNING: SECRET_KEY not set in environment!")
    print("   Add it to your .env file: SECRET_KEY=your-secret-key-here")

print("✅ WSGI configuration loaded successfully")
print(f"   Project directory: {project_home}")
print(f"   Python version: {sys.version}")
print(f"   Python path: {sys.path[:3]}...")

# PythonAnywhere will use the 'application' object
# Do not rename this variable!
