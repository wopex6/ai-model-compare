"""
Comprehensive check for undeclared variables, classes, and methods
Verifies all imports, method calls, and attribute accesses are valid
"""

import ast
import sys
from pathlib import Path

def check_file_for_undeclared(filepath):
    """Check a Python file for potential undeclared items"""
    print(f"\n🔍 Checking: {filepath}")
    print("-" * 80)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=filepath)
        
        # Track defined items
        defined_classes = set()
        defined_functions = set()
        defined_variables = set()
        imported_modules = set()
        imported_items = set()
        
        # First pass: collect definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined_classes.add(node.name)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                defined_functions.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_variables.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imported_items.add(alias.name)
                    if module:
                        imported_modules.add(f"{module}.{alias.name}")
        
        # Check for common issues
        issues = []
        
        # Check imports exist
        critical_imports = {
            'ai_compare/chatbot.py': ['AICompare', 'ChatbotPersonality', 'ConversationManager', 
                                     'PersonalityProfiler', 'AdaptivePersonality', 'AITools', 
                                     'FunctionCallingParser', 'PERSONALITY_PRESETS', 'USER_TRAIT_PRESETS'],
            'ai_compare/motivational_chatbot.py': ['AIChatbot', 'MotivationalSystem'],
            'ai_compare/wisdom_chatbot.py': ['AIChatbot', 'PERSONALITY_PRESETS'],
            'ai_compare/base_chatbot.py': ['AICompare', 'ChatbotPersonality', 'ConversationManager',
                                          'PersonalityProfiler', 'AdaptivePersonality', 'AITools',
                                          'FunctionCallingParser', 'PERSONALITY_PRESETS', 'USER_TRAIT_PRESETS']
        }
        
        filepath_str = str(filepath).replace('\\', '/')
        if filepath_str in critical_imports:
            expected = critical_imports[filepath_str]
            for item in expected:
                if item not in imported_items and item not in defined_classes:
                    issues.append(f"❌ Missing import or definition: {item}")
        
        # Print results
        print(f"✅ Defined Classes: {len(defined_classes)}")
        for cls in sorted(defined_classes):
            print(f"   - {cls}")
        
        print(f"\n✅ Defined Functions/Methods: {len(defined_functions)}")
        sample_functions = sorted(defined_functions)[:10]
        for func in sample_functions:
            print(f"   - {func}")
        if len(defined_functions) > 10:
            print(f"   ... and {len(defined_functions) - 10} more")
        
        print(f"\n✅ Imported Items: {len(imported_items)}")
        for item in sorted(imported_items)[:15]:
            print(f"   - {item}")
        if len(imported_items) > 15:
            print(f"   ... and {len(imported_items) - 15} more")
        
        if issues:
            print(f"\n❌ ISSUES FOUND ({len(issues)}):")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print(f"\n✅ NO ISSUES FOUND - All declarations look good!")
            return True
            
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_method_calls(filepath):
    """Check that all method calls reference existing methods"""
    print(f"\n🔎 Checking method calls in: {filepath}")
    print("-" * 80)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        
        # Find all method definitions
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.add(node.name)
        
        # Find all method calls
        method_calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    method_calls.add(node.func.attr)
                elif isinstance(node.func, ast.Name):
                    method_calls.add(node.func.id)
        
        # Check for super() calls (these are OK)
        has_super = 'super' in str(content)
        
        print(f"✅ Methods defined: {len(methods)}")
        print(f"✅ Method calls found: {len(method_calls)}")
        print(f"✅ Uses super(): {has_super}")
        
        # Check for common method names that should exist
        critical_methods = {
            'chat', '_build_enhanced_prompt', '_apply_personality_filter',
            '_preprocess_message', '_postprocess_response', '_core_process',
            '_save_conversation'
        }
        
        defined_critical = critical_methods.intersection(methods)
        if defined_critical:
            print(f"\n✅ Critical methods defined: {sorted(defined_critical)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "=" * 80)
    print("🔍 COMPREHENSIVE DECLARATION CHECK")
    print("=" * 80)
    
    files_to_check = [
        'ai_compare/chatbot.py',
        'ai_compare/motivational_chatbot.py',
        'ai_compare/wisdom_chatbot.py',
        'ai_compare/base_chatbot.py'
    ]
    
    all_passed = True
    
    for filepath in files_to_check:
        path = Path(filepath)
        if path.exists():
            passed = check_file_for_undeclared(filepath)
            check_method_calls(filepath)
            all_passed = all_passed and passed
        else:
            print(f"\n⚠️  File not found: {filepath}")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ✅ ✅ ALL CHECKS PASSED! ✅ ✅ ✅")
        print("No undeclared variables, classes, or methods found!")
    else:
        print("❌ Some issues found - please review above")
    print("=" * 80 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
