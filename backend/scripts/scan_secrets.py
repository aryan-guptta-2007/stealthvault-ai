import os
import re
import sys

# Windows encoding fix
try:
    import sys
    import codecs
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
except Exception:
    pass

def scan_for_secrets():
    """
    StealthVault AI - Secret Scanner
    Audits the codebase for potential hardcoded secrets and credentials.
    """
    SENSITIVE_PATTERNS = [
        (r'["\']sv_[a-zA-Z0-9]{32}["\']', "Potential StealthVault API Key"),
        (r'postgres:\/\/([^:@]+):([^@]+)@', "PostgreSQL Connection String"),
        (r'SECRET_KEY\s*=\s*["\']([^"\'\s]{16,})["\']', "Hardcoded JWT Secret Key"),
        (r'password\s*[:=]\s*["\']([^"\'\s]{8,})["\']', "Potential Hardcoded Password"),
        (r'AWS_SECRET_ACCESS_KEY\s*[:=]\s*["\']([^"\'\s]{20,})["\']', "AWS Secret Key"),
    ]
    
    EXCLUDE_DIRS = {'.git', '__pycache__', 'env', 'venv', 'node_modules', '.venv', '.gemini'}
    EXCLUDE_FILES = {'scan_secrets.py', '.env.example', 'README.md', 'audit_results.txt'}

    found_leaks = 0
    print("SEARCH START: StealthVault AI Secret Audit...")
    print("-" * 50)

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file in EXCLUDE_FILES:
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern, label in SENSITIVE_PATTERNS:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Avoid flagging .env files
                            if ".env" in file:
                                continue
                                
                            line_no = content.count('\n', 0, match.start()) + 1
                            print(f"[!] {label} FOUND!")
                            print(f"    File: {file_path}")
                            print(f"    Line: {line_no}")
                            print(f"    Snippet: {match.group(0)[:20]}...")
                            print("-" * 30)
                            found_leaks += 1
            except Exception:
                pass

    if found_leaks == 0:
        print("[SUCCESS] CLEAN AUDIT: No obvious hardcoded secrets detected.")
    else:
        print(f"[FAILED] AUDIT FAILED: Found {found_leaks} potential secret leaks!")
        print("ACTION: Move these values to environment variables immediately.")
        sys.exit(1)

if __name__ == "__main__":
    scan_for_secrets()
