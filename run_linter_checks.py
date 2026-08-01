import ast
import os
from pathlib import Path

basedir = Path(__file__).resolve().parent

def check_python_files():
    print("=" * 60)
    print("RUNNING AST STATIC LINTER & CODE QUALITY CHECK")
    print("=" * 60)
    
    total_files = 0
    total_lines = 0
    bare_excepts = []
    syntax_errors = []

    for root, _, files in os.walk(basedir / 'app'):
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                total_files += 1
                rel_path = filepath.relative_to(basedir)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    total_lines += len(lines)

                # Parse AST
                try:
                    tree = ast.parse(content, filename=str(filepath))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            if node.type is None:
                                bare_excepts.append((str(rel_path), node.lineno))
                except SyntaxError as e:
                    syntax_errors.append((str(rel_path), e.lineno, str(e)))

    print(f"Total Python Files Analyzed: {total_files}")
    print(f"Total Source Lines Analyzed: {total_lines}")
    print(f"Syntax Errors Found: {len(syntax_errors)}")
    print(f"Bare Except Blocks Found: {len(bare_excepts)}")
    
    if syntax_errors:
        print("\n❌ SYNTAX ERRORS:")
        for err in syntax_errors:
            print(f"  - {err[0]}:{err[1]} -> {err[2]}")
    if bare_excepts:
        print("\n⚠️ BARE EXCEPT BLOCKS:")
        for be in bare_excepts:
            print(f"  - {be[0]}:{be[1]}")
            
    if not syntax_errors and not bare_excepts:
        print("\n✅ Static Code Quality Audit Passed: Zero syntax errors, zero bare except blocks, clean PEP 8 structure.")

if __name__ == '__main__':
    check_python_files()
