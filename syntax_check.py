"""Check for syntax errors in personality system files"""

import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse the AST
        ast.parse(source, filename=str(file_path))
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def main():
    files_to_check = [
        "ai_compare/personality_profiler.py",
        "ai_compare/adaptive_personality.py", 
        "ai_compare/personality_ui.py",
        "ai_compare/chatbot.py",
        "app.py"
    ]
    
    print("Syntax Check Results:")
    print("=" * 40)
    
    all_good = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            is_valid, error = check_syntax(file_path)
            status = "✓" if is_valid else "✗"
            print(f"{status} {file_path}")
            if error:
                print(f"  Error: {error}")
                all_good = False
        else:
            print(f"? {file_path} (not found)")
    
    print("\n" + "=" * 40)
    if all_good:
        print("✅ No syntax errors found!")
    else:
        print("❌ Syntax errors detected above")
    
    return all_good

if __name__ == "__main__":
    main()
