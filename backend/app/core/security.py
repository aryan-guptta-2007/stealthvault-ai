from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash for a plain-text password."""
    import traceback
    if not password:
        print("DEBUG [security]: CRITICAL - get_password_hash called with EMPTY password!")
        traceback.print_stack()
        # Return a known invalid hash instead of crashing the whole server
        return "$2b$12$eixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L6s577/qd7A9hqL" 
    
    return pwd_context.hash(password)
