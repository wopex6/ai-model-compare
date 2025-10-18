"""Direct test of documentation system functionality."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_documentation_system():
    """Test the documentation system directly."""
    
    results = []
    
    # Test 1: Check if core files exist
    required_files = [
        "ai_compare/doc_updater.py",
        "auto_doc_hook.py", 
        "doc_config.py"
    ]
    
    for file_path in required_files:
        exists = Path(file_path).exists()
        results.append(f"{'✓' if exists else '✗'} {file_path}: {'Found' if exists else 'Missing'}")
    
    # Test 2: Import and initialize
    try:
        from ai_compare.doc_updater import DocumentationUpdater
        updater = DocumentationUpdater()
        results.append("✓ DocumentationUpdater: Successfully imported and initialized")
        
        # Test file analysis
        app_file = Path("app.py")
        if app_file.exists():
            analysis = updater._analyze_python_file(app_file)
            line_count = analysis.get('line_count', 0)
            class_count = len(analysis.get('classes', []))
            function_count = len(analysis.get('functions', []))
            results.append(f"✓ File Analysis: app.py - {line_count} lines, {class_count} classes, {function_count} functions")
        
        # Test change detection
        changes = updater.check_for_changes()
        total_files = sum(len(files) for files in changes.values())
        results.append(f"✓ Change Detection: Monitoring {total_files} files")
        
        # Test system analysis
        system_analysis = updater._analyze_current_system()
        total_lines = system_analysis.get('total_lines', 0)
        total_classes = system_analysis.get('class_count', 0)
        results.append(f"✓ System Analysis: {total_lines} total lines, {total_classes} classes across project")
        
    except Exception as e:
        results.append(f"✗ DocumentationUpdater: Failed - {str(e)}")
    
    # Test 3: Auto-doc hook
    try:
        from auto_doc_hook import auto_doc, update_docs_now
        running = auto_doc.running
        interval = auto_doc.update_interval
        results.append(f"✓ Auto-doc Hook: Imported, Running: {running}, Interval: {interval}s")
    except Exception as e:
        results.append(f"✗ Auto-doc Hook: Failed - {str(e)}")
    
    # Test 4: Configuration
    try:
        from doc_config import doc_config
        status = doc_config.get_status()
        enabled = status.get('enabled', False)
        results.append(f"✓ Configuration: Loaded, Enabled: {enabled}")
    except Exception as e:
        results.append(f"✗ Configuration: Failed - {str(e)}")
    
    # Test 5: Check documentation files
    doc_files = [
        "SYSTEM_REGENERATION_GUIDE.md",
        "AI_REGENERATION_SPEC.md", 
        "ENHANCEMENTS.md"
    ]
    
    for doc_file in doc_files:
        exists = Path(doc_file).exists()
        if exists:
            size = Path(doc_file).stat().st_size
            results.append(f"✓ Documentation: {doc_file} exists ({size} bytes)")
        else:
            results.append(f"○ Documentation: {doc_file} will be created when needed")
    
    return results

def show_integration_status():
    """Show Flask integration status."""
    
    integration_results = []
    
    try:
        app_file = Path("app.py")
        if app_file.exists():
            with open(app_file, 'r') as f:
                content = f.read()
            
            checks = [
                ("auto_doc_hook import", "from auto_doc_hook import" in content),
                ("enable_auto_docs call", "enable_auto_docs()" in content),
                ("update_docs_now call", "update_docs_now()" in content)
            ]
            
            for check_name, passed in checks:
                status = "✓" if passed else "○"
                integration_results.append(f"{status} Flask Integration: {check_name}")
        else:
            integration_results.append("✗ Flask Integration: app.py not found")
            
    except Exception as e:
        integration_results.append(f"✗ Flask Integration: Error checking - {str(e)}")
    
    return integration_results

if __name__ == "__main__":
    print("=== Documentation System Test Results ===\n")
    
    # Run core tests
    test_results = test_documentation_system()
    for result in test_results:
        print(result)
    
    print("\n=== Flask Integration Status ===\n")
    
    # Check integration
    integration_results = show_integration_status()
    for result in integration_results:
        print(result)
    
    print("\n=== How to Test Live ===")
    print("1. Run: python app.py")
    print("2. Documentation will auto-update every 30 seconds")
    print("3. Make changes to any Python file to trigger updates")
    print("4. Check timestamps in documentation files")
    
    print("\n=== Manual Testing ===")
    print("from doc_config import doc_config")
    print("doc_config.update_now()  # Force immediate update")
    
    # Write results to file for verification
    with open("doc_test_results.txt", "w") as f:
        f.write("Documentation System Test Results\n")
        f.write("=" * 40 + "\n\n")
        for result in test_results + integration_results:
            f.write(result + "\n")
    
    print(f"\n✓ Test results saved to: doc_test_results.txt")
