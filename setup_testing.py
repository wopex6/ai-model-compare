#!/usr/bin/env python3
"""
Quick setup script for automated testing
Installs Playwright and verifies installation
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and show progress"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(e.stderr)
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🤖 Automated Testing - Setup Script                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Install Playwright
    if not run_command(
        f"{sys.executable} -m pip install playwright",
        "Installing Playwright"
    ):
        print("\n❌ Failed to install Playwright")
        return False
    
    # Step 2: Install browser engines
    if not run_command(
        f"{sys.executable} -m playwright install chromium",
        "Installing Chromium browser"
    ):
        print("\n❌ Failed to install browser")
        return False
    
    # Step 3: Verify installation
    print("\n" + "="*60)
    print("🔍 Verifying Installation")
    print("="*60)
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright imported successfully")
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
            print("✅ Browser launch test successful")
        
        print("\n" + "="*60)
        print("✨ SETUP COMPLETE!")
        print("="*60)
        print("\n📝 Next Steps:")
        print("1. Make sure your Flask app is running:")
        print("   python app.py")
        print("\n2. Run the automated tests:")
        print("   python automated_test.py")
        print("\n3. Check test results in 'test_screenshots' folder")
        print("\n🎉 You're all set!")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
