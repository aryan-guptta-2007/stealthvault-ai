from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash for a plain-text password."""
    import hashlib
    import bcrypt
    
    # 🔍 Forensic Debug Step (Unmasking the Hashing Source)
    print(f"DEBUG [security]: Hashing Password | Type: {type(password)} | Length: {len(str(password))}")
    
    if not password:
        print("DEBUG [security]: CRITICAL - get_password_hash called with EMPTY password!")
        # Return a known invalid hash instead of crashing the whole server
        return "$2b$12$eixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L6s577/qd7A9hqL" 

    # 🚀 PRO FIX: SHA-256 layer + Direct Bcrypt
    # This ensures we never hit bcrypt's 72-char limit and the input is always a predictable hex string.
    sha_hash = hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(sha_hash.encode(), salt)
    
    return hashed.decode('utf-8')
