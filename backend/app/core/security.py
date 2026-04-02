from passlib.context import CryptContext
import jwt
import os
from datetime import datetime, timedelta

# Cryptographic Configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 Access mission-critical secrets from environment or specialized config
SECRET_KEY = os.getenv("SV_JWT_SECRET_KEY", "3a1c8f9d2e4b7a1c8f9d2e4b7a1c8f9d") # Fallback for local dev only
ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that the provided password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash for storage."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    🧬 GENERATE ACCESS TOKEN
    Issues a cryptographically signed JWT for session authorization.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
