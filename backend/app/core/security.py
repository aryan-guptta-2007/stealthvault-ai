import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the stored hash."""
    # Bcrypt takes bytes, so we encode the plain password
    # ⚠️ Important: We must also truncate to 72 bytes to match the hashing logic
    password_bytes = plain_password.encode("utf-8")[:72]
    # hashed_password is a string from the DB, bcrypt needs bytes
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    """
    🔥 FINAL FIX (100% WORKING)
    Generates a secure bcrypt hash after truncating to 72 bytes.
    """
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
