#!/usr/bin/env python3
import sys
import os
import ast
import subprocess

def get_staged_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True
    )
    return [f for f in result.stdout.strip().split("\n") if f and f.endswith(".py")]

def check_file_ast(filepath):
    # Load exemptions from JSON configuration if available
    exemptions = ["pre_commit_gate", "quality_sentinel", "swarm_consensus"]
    import json
    if os.path.exists(".pre-commit-exemptions.json"):
        try:
            with open(".pre-commit-exemptions.json", "r") as f:
                exemptions = json.load(f)
        except Exception:
            pass

    # Exempt quality validator scripts from self-violations
    if any(ex in filepath for ex in exemptions):
        return []


    violations = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        
        tree = ast.parse(code, filename=filepath)
        for node in ast.walk(tree):
            # Check for imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sentence_transformers":
                        violations.append(f"{filepath}: Forbidden import of sentence_transformers.")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "sentence_transformers":
                    violations.append(f"{filepath}: Forbidden import of sentence_transformers.")
            
            # Check for string literals (absolute paths, drop table queries)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                if any(path in val for path in ["/home/", "/etc/", "/usr/local/bin/"]):
                    # To allow RAE-core src path or test files, filter accordingly
                    if not filepath.startswith("tests/") and not "test_" in filepath:
                        violations.append(f"{filepath}: Found absolute path in string literal: '{val}'")
                if any(sql in val.upper() for sql in ["DROP TABLE", "TRUNCATE TABLE", "DROP DATABASE"]):
                    violations.append(f"{filepath}: Found destructive database query in string literal: '{val}'")
    except SyntaxError as e:
        violations.append(f"{filepath}: Syntax Error: {e.msg} at line {e.lineno}")
    except Exception as e:
        violations.append(f"{filepath}: Parsing Error: {str(e)}")
    return violations

def main():
    files = get_staged_files()
    if not files:
        sys.exit(0)
        
    all_violations = []
    for f in files:
        # Only check code, skip tests to allow mock payloads
        if "test" in f or "tests/" in f:
            continue
        violations = check_file_ast(f)
        all_violations.extend(violations)
        
    if all_violations:
        print("\n❌ RAE-Suite Quality Gate: Commit Blocked due to AST violations:")
        for v in all_violations:
            print(f"  - {v}")
        print("\nPlease fix these violations before committing.\n")
        sys.exit(1)
        
    print("✅ RAE-Suite AST Quality Gate Passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
