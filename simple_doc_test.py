#!/usr/bin/env python3
"""Simple test to verify documentation system works."""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_functionality():
    """Test basic documentation system functionality."""
    print("Testing Documentation System...")
    
    # Test 1: Check if files exist
    required_files = [
        "ai_compare/doc_updater.py",
        "auto_doc_hook.py", 
        "doc_config.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            return False
    
    # Test 2: Try importing the modules
    try:
        from ai_compare.doc_updater import DocumentationUpdater
        print("✓ DocumentationUpdater import successful")
    except Exception as e:
        print(f"✗ DocumentationUpdater import failed: {e}")
        return False
    
    try:
        from auto_doc_hook import auto_doc
        print("✓ auto_doc_hook import successful")
    except Exception as e:
        print(f"✗ auto_doc_hook import failed: {e}")
        return False
    
    # Test 3: Create updater instance
    try:
        updater = DocumentationUpdater()
        print("✓ DocumentationUpdater instance created")
    except Exception as e:
        print(f"✗ DocumentationUpdater creation failed: {e}")
        return False
    
    # Test 4: Test file analysis
    try:
        app_file = Path("app.py")
        if app_file.exists():
            analysis = updater._analyze_python_file(app_file)
            print(f"✓ File analysis works - app.py has {analysis.get('line_count', 0)} lines")
        else:
            print("⚠ app.py not found for analysis test")
    except Exception as e:
        print(f"✗ File analysis failed: {e}")
        return False
    
    # Test 5: Test change detection
    try:
        changes = updater.check_for_changes()
        print(f"✓ Change detection works - found {sum(len(v) for v in changes.values())} total changes")
    except Exception as e:
        print(f"✗ Change detection failed: {e}")
        return False
    
    print("\n🎉 Documentation system is working correctly!")
    
    # Show what the system monitors
    print("\nSystem monitors these files:")
    for pattern in updater.monitored_files:
        print(f"  - {pattern}")
    
    print("\nDocumentation files that get updated:")
    for doc_file in updater.doc_files.keys():
        if Path(doc_file).exists():
            print(f"  ✓ {doc_file}")
        else:
            print(f"  ⚠ {doc_file} (will be created)")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    
    if success:
        print("\n✅ Documentation system ready!")
        print("\nTo see it in action:")
        print("1. Run: python app.py")
        print("2. Make changes to any .py file")
        print("3. Documentation will auto-update every 30 seconds")
        print("4. Or force update with: python -c 'from doc_config import doc_config; doc_config.update_now()'")
    else:
        print("\n❌ Documentation system has issues")
