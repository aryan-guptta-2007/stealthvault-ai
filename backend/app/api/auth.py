"""
StealthVault AI - API Security
JWT Authentication and RBAC mappings for enterprise deployment.
"""

from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.config import settings

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.db_models import DBUser, DBTenant
from app.core.limiter import limiter
from fastapi import Request

# The secret key should come from env or config. Hardcoded for Phase 4 immediate auth.
SECRET_KEY = "STEALTHVAULT_SUPER_SECRET_KEY_V1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency for securing API routes."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        roles: list = payload.get("roles", [])
        if username is None or tenant_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    class CurrentUser:
        def __init__(self, username, tenant_id, roles):
            self.username = username
            self.tenant_id = tenant_id
            self.roles = roles
            
    return CurrentUser(username, tenant_id, roles)

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

async def get_optional_user(token: str | None = Depends(oauth2_scheme_optional)):
    """Dependency for Hybrid Auth. Returns user object if token valid, else None."""
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

from app.core.security import verify_password

@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    🔐 OBTAIN ACCESS TOKEN
    
    Verifies credentials and issues a JWT scoped to a specific tenant.
    Includes RBAC roles for enterprise access control.
    """
    # Lookup User in Postgres
    result = await db.execute(select(DBUser).where(DBUser.username == form_data.username))
    user = result.scalars().first()
    
    # Secure Password Verification (Bcrypt)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "tenant_id": user.tenant_id, 
            "roles": user.roles,
            "uid": user.id
        }, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
