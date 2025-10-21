#!/usr/bin/env python3
"""
Startup script for the Integrated AI Chatbot Multi-User System
Handles initialization, dependency checking, and system startup
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask', 'flask_cors', 'bcrypt', 'jwt', 'sqlite3', 
        'asyncio', 'requests', 'pathlib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'jwt':
                __import__('jwt')
            elif package == 'flask_cors':
                __import__('flask_cors')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            # Map package names to pip install names
            pip_names = {
                'jwt': 'pyjwt',
                'flask_cors': 'flask-cors'
            }
            
            for package in missing_packages:
                pip_name = pip_names.get(package, package)
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name])
                print(f"✅ Installed {pip_name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def check_environment():
    """Check environment setup"""
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found - creating default configuration")
        create_default_env()
    else:
        print("✅ .env file exists")
    
    return True

def create_default_env():
    """Create default .env file"""
    default_env = """# Integrated AI Chatbot Configuration
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production

# AI API Keys (add your actual keys here)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional: Other AI service keys
GOOGLE_API_KEY=your-google-api-key-here
"""
    
    with open('.env', 'w') as f:
        f.write(default_env)
    
    print("📝 Created default .env file")
    print("   ⚠️  Please add your actual API keys to .env file for full functionality")

def check_database():
    """Check if integrated database exists"""
    db_file = Path('integrated_users.db')
    if db_file.exists():
        print("✅ Integrated database exists")
    else:
        print("📊 Database will be created on first run")
    return True

def start_server():
    """Start the Flask server"""
    print("\n🚀 Starting Integrated AI Chatbot Server...")
    print("   Server will start at: http://localhost:5000")
    print("   ChatChat Interface: http://localhost:5000/chatchat")
    print("   Press Ctrl+C to stop the server")
    print("\n" + "="*60)
    
    try:
        # Import and run the Flask app
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

def open_browser():
    """Open browser to the chatchat interface"""
    try:
        time.sleep(2)  # Wait for server to start
        webbrowser.open('http://localhost:5000/chatchat')
        print("🌐 Opening browser to ChatChat interface...")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("   Please manually open: http://localhost:5000/chatchat")

def print_welcome():
    """Print welcome message"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🤖 Integrated AI Chatbot Multi-User System 🤖        ║
║                                                              ║
║  A comprehensive AI chatbot with multi-user authentication, ║
║  personalized conversations, and psychology trait profiling ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🎯 Features:
   • Multi-user authentication and profiles
   • Real AI conversations (GPT, Claude, etc.)
   • Psychology trait-based personalization
   • Persistent conversation history
   • Modern web interface

👤 Default User:
   Username: Wai Tse
   Password: .//

🌐 Access Points:
   • ChatChat Interface: http://localhost:5000/chatchat
   • Original AI Compare: http://localhost:5000/
""")

def main():
    """Main startup function"""
    print_welcome()
    
    print("🔍 System Check:")
    print("-" * 20)
    
    # Run system checks
    if not check_python_version():
        return 1
    
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    if not check_environment():
        return 1
    
    if not check_database():
        return 1
    
    print("\n✅ All system checks passed!")
    
    # Ask user if they want to start the server
    print("\n🚀 Ready to start the Integrated AI Chatbot System!")
    
    try:
        user_input = input("\nStart the server now? (y/n): ").lower().strip()
        if user_input in ['y', 'yes', '']:
            # Start server in background and open browser
            import threading
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            start_server()
        else:
            print("\n📝 To start manually, run:")
            print("   python app.py")
            print("\n🌐 Then visit: http://localhost:5000/chatchat")
    except KeyboardInterrupt:
        print("\n\n👋 Startup cancelled by user")
        return 0
    
    return 0

if __name__ == "__main__":
    exit(main())
