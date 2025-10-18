"""
Automated Documentation Update System
Monitors code changes and automatically updates documentation files
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import ast
import re

class DocumentationUpdater:
    """Automatically updates documentation when code changes are detected."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.doc_files = {
            "SYSTEM_REGENERATION_GUIDE.md": self._update_system_guide,
            "AI_REGENERATION_SPEC.md": self._update_ai_spec,
            "ENHANCEMENTS.md": self._update_enhancements,
            "README.md": self._update_readme
        }
        self.monitored_files = [
            "ai_compare/*.py",
            "app.py",
            "requirements.txt",
            ".env"
        ]
        self.change_log_file = self.project_root / "doc_changes.json"
        self.last_hashes = self._load_file_hashes()
        
    def _load_file_hashes(self) -> Dict[str, str]:
        """Load previously stored file hashes."""
        if self.change_log_file.exists():
            try:
                with open(self.change_log_file, 'r') as f:
                    return json.load(f).get('file_hashes', {})
            except:
                return {}
        return {}
    
    def _save_file_hashes(self, hashes: Dict[str, str]):
        """Save current file hashes."""
        data = {
            'file_hashes': hashes,
            'last_update': datetime.now().isoformat(),
            'update_count': self._get_update_count() + 1
        }
        with open(self.change_log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_update_count(self) -> int:
        """Get current update count."""
        if self.change_log_file.exists():
            try:
                with open(self.change_log_file, 'r') as f:
                    return json.load(f).get('update_count', 0)
            except:
                return 0
        return 0
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _analyze_python_file(self, file_path: Path) -> Dict:
        """Analyze Python file for classes, methods, and key information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                'file_path': str(file_path),
                'line_count': len(content.splitlines()),
                'classes': [],
                'functions': [],
                'imports': [],
                'docstring': ast.get_docstring(tree) or ""
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    analysis['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': methods,
                        'docstring': ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    analysis['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node) or ""
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis['imports'].append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            analysis['imports'].append(f"{module}.{alias.name}")
            
            return analysis
        except Exception as e:
            return {'error': str(e), 'file_path': str(file_path)}
    
    def check_for_changes(self) -> Dict[str, List[str]]:
        """Check for changes in monitored files."""
        changes = {
            'modified': [],
            'added': [],
            'deleted': []
        }
        
        current_hashes = {}
        
        # Check all Python files in ai_compare
        for py_file in (self.project_root / "ai_compare").glob("*.py"):
            if py_file.name != "__pycache__":
                file_key = str(py_file.relative_to(self.project_root))
                current_hash = self._get_file_hash(py_file)
                current_hashes[file_key] = current_hash
                
                if file_key not in self.last_hashes:
                    changes['added'].append(file_key)
                elif self.last_hashes[file_key] != current_hash:
                    changes['modified'].append(file_key)
        
        # Check other monitored files
        for file_pattern in ["app.py", "requirements.txt", ".env"]:
            file_path = self.project_root / file_pattern
            if file_path.exists():
                file_key = str(file_path.relative_to(self.project_root))
                current_hash = self._get_file_hash(file_path)
                current_hashes[file_key] = current_hash
                
                if file_key not in self.last_hashes:
                    changes['added'].append(file_key)
                elif self.last_hashes[file_key] != current_hash:
                    changes['modified'].append(file_key)
        
        # Check for deleted files
        for file_key in self.last_hashes:
            if file_key not in current_hashes:
                changes['deleted'].append(file_key)
        
        self.last_hashes = current_hashes
        self._save_file_hashes(current_hashes)
        
        return changes
    
    def _update_system_guide(self, changes: Dict[str, List[str]]):
        """Update SYSTEM_REGENERATION_GUIDE.md based on changes."""
        guide_path = self.project_root / "SYSTEM_REGENERATION_GUIDE.md"
        
        if not guide_path.exists():
            return
        
        # Analyze current system state
        system_analysis = self._analyze_current_system()
        
        # Read current guide
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update sections based on analysis
        updated_content = self._update_guide_sections(content, system_analysis, changes)
        
        # Add update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_content = self._add_update_timestamp(updated_content, timestamp)
        
        # Write updated guide
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def _update_ai_spec(self, changes: Dict[str, List[str]]):
        """Update AI_REGENERATION_SPEC.md based on changes."""
        spec_path = self.project_root / "AI_REGENERATION_SPEC.md"
        
        if not spec_path.exists():
            return
        
        # Analyze current system for AI regeneration
        system_analysis = self._analyze_current_system()
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update critical sections
        updated_content = self._update_ai_spec_sections(content, system_analysis, changes)
        
        # Add update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_content = self._add_update_timestamp(updated_content, timestamp)
        
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def _update_enhancements(self, changes: Dict[str, List[str]]):
        """Update ENHANCEMENTS.md with new changes."""
        enhancements_path = self.project_root / "ENHANCEMENTS.md"
        
        if not enhancements_path.exists():
            return
        
        if not any(changes.values()):
            return  # No changes to document
        
        with open(enhancements_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add new enhancement entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = self._create_enhancement_entry(changes, timestamp)
        
        # Insert new entry after the overview section
        insertion_point = content.find("## 🔧 Enhancement 1:")
        if insertion_point != -1:
            updated_content = (content[:insertion_point] + 
                             new_entry + "\n\n" + 
                             content[insertion_point:])
        else:
            updated_content = content + "\n\n" + new_entry
        
        with open(enhancements_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def _update_readme(self, changes: Dict[str, List[str]]):
        """Update README.md if it exists."""
        readme_path = self.project_root / "README.md"
        
        if readme_path.exists():
            # Add update timestamp to README
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Look for existing update line and replace it
            update_pattern = r"Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            if re.search(update_pattern, content):
                updated_content = re.sub(update_pattern, f"Last updated: {timestamp}", content)
            else:
                # Add update line at the end
                updated_content = content + f"\n\nLast updated: {timestamp}"
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
    
    def _analyze_current_system(self) -> Dict:
        """Analyze current system state for documentation updates."""
        analysis = {
            'files': {},
            'total_lines': 0,
            'class_count': 0,
            'function_count': 0,
            'dependencies': []
        }
        
        # Analyze Python files
        for py_file in (self.project_root / "ai_compare").glob("*.py"):
            if py_file.name != "__pycache__":
                file_analysis = self._analyze_python_file(py_file)
                analysis['files'][py_file.name] = file_analysis
                analysis['total_lines'] += file_analysis.get('line_count', 0)
                analysis['class_count'] += len(file_analysis.get('classes', []))
                analysis['function_count'] += len(file_analysis.get('functions', []))
        
        # Analyze app.py
        app_file = self.project_root / "app.py"
        if app_file.exists():
            file_analysis = self._analyze_python_file(app_file)
            analysis['files']['app.py'] = file_analysis
            analysis['total_lines'] += file_analysis.get('line_count', 0)
        
        # Analyze requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                analysis['dependencies'] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        return analysis
    
    def _update_guide_sections(self, content: str, analysis: Dict, changes: Dict) -> str:
        """Update specific sections in the system guide."""
        # Update file structure section
        structure_pattern = r"(```\nai-model-compare/.*?```)"
        if re.search(structure_pattern, content, re.DOTALL):
            new_structure = self._generate_file_structure(analysis)
            content = re.sub(structure_pattern, new_structure, content, flags=re.DOTALL)
        
        return content
    
    def _update_ai_spec_sections(self, content: str, analysis: Dict, changes: Dict) -> str:
        """Update specific sections in the AI regeneration spec."""
        # Update exact file structure
        structure_pattern = r"(```\nai-model-compare/.*?```)"
        if re.search(structure_pattern, content, re.DOTALL):
            new_structure = self._generate_detailed_structure(analysis)
            content = re.sub(structure_pattern, new_structure, content, flags=re.DOTALL)
        
        return content
    
    def _generate_file_structure(self, analysis: Dict) -> str:
        """Generate current file structure for documentation."""
        structure = "```\nai-model-compare/\n"
        
        # Add main files
        for filename, file_info in analysis['files'].items():
            if filename == 'app.py':
                structure += f"├── {filename}                              # Flask application ({file_info.get('line_count', 0)} lines)\n"
            elif filename.endswith('.py'):
                structure += f"│   ├── {filename}             # {file_info.get('docstring', 'Core module').split('.')[0]} ({file_info.get('line_count', 0)} lines)\n"
        
        structure += "├── requirements.txt                    # Python dependencies\n"
        structure += "├── .env                               # Environment variables\n"
        structure += "├── conversations/                     # Auto-created conversation storage\n"
        structure += "└── test_*.py                         # Test files\n```"
        
        return structure
    
    def _generate_detailed_structure(self, analysis: Dict) -> str:
        """Generate detailed file structure with line counts."""
        structure = "```\nai-model-compare/\n"
        
        for filename, file_info in analysis['files'].items():
            if filename == 'app.py':
                structure += f"├── {filename}                              # Flask application ({file_info.get('line_count', 0)} lines)\n"
            elif filename.endswith('.py') and filename != '__init__.py':
                line_count = file_info.get('line_count', 0)
                structure += f"│   ├── {filename:<25} # {file_info.get('docstring', 'Core module').split('.')[0]} ({line_count} lines)\n"
        
        structure += "├── requirements.txt                    # Dependencies\n"
        structure += "├── .env                               # API keys\n"
        structure += "└── conversations/                     # Storage\n```"
        
        return structure
    
    def _create_enhancement_entry(self, changes: Dict, timestamp: str) -> str:
        """Create a new enhancement entry for the documentation."""
        entry = f"## 🔄 Auto-Update {timestamp}\n\n"
        entry += "### Changes Detected\n"
        
        if changes['added']:
            entry += f"**Files Added:** {', '.join(changes['added'])}\n\n"
        
        if changes['modified']:
            entry += f"**Files Modified:** {', '.join(changes['modified'])}\n\n"
        
        if changes['deleted']:
            entry += f"**Files Deleted:** {', '.join(changes['deleted'])}\n\n"
        
        entry += "Documentation automatically updated to reflect current system state.\n"
        
        return entry
    
    def _add_update_timestamp(self, content: str, timestamp: str) -> str:
        """Add or update timestamp in documentation."""
        timestamp_pattern = r"Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        
        if re.search(timestamp_pattern, content):
            return re.sub(timestamp_pattern, f"Last updated: {timestamp}", content)
        else:
            # Add timestamp at the beginning after title
            lines = content.split('\n')
            if lines and lines[0].startswith('#'):
                lines.insert(1, f"\n*Last updated: {timestamp}*\n")
                return '\n'.join(lines)
            else:
                return f"*Last updated: {timestamp}*\n\n{content}"
    
    def update_all_documentation(self):
        """Check for changes and update all documentation files."""
        changes = self.check_for_changes()
        
        if any(changes.values()):
            print(f"Documentation update triggered - Changes detected:")
            for change_type, files in changes.items():
                if files:
                    print(f"  {change_type.title()}: {', '.join(files)}")
            
            # Update each documentation file
            for doc_file, update_func in self.doc_files.items():
                try:
                    update_func(changes)
                    print(f"  ✓ Updated {doc_file}")
                except Exception as e:
                    print(f"  ✗ Failed to update {doc_file}: {e}")
        
        return changes

# Auto-update hook that can be imported and called
def auto_update_docs(project_root: str = "."):
    """Convenience function to trigger documentation update."""
    updater = DocumentationUpdater(project_root)
    return updater.update_all_documentation()

if __name__ == "__main__":
    # Run documentation update
    updater = DocumentationUpdater()
    changes = updater.update_all_documentation()
    
    if not any(changes.values()):
        print("No changes detected - documentation is up to date.")
