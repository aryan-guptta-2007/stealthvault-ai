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
from app.models.db_models import DBUser, DBTenant, DBWaitlist
from app.core.limiter import limiter
from fastapi import Request
from app.core.audit import log_audit
from app.models.alert import RegisterInput
from app.core.security import get_password_hash
import secrets

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
        # 🛡️ AUDIT: Failed Login Attempt
        # Use the actual tenant if user was found, else "global"
        failed_tenant = user.tenant_id if user else "global"
        
        await log_audit(
            action="LOGIN",
            target=form_data.username,
            tenant_id=failed_tenant,
            result="FAILURE",
            message="Invalid credentials",
            metadata={"ip": request.client.host}
        )
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

    # 🛡️ AUDIT: Successful Login
    await log_audit(
        action="LOGIN",
        target=user.username,
        tenant_id=user.tenant_id,
        user_id=user.id,
        username=user.username,
        result="SUCCESS",
        metadata={"ip": request.client.host}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_tenant(
    payload: RegisterInput,
    db: AsyncSession = Depends(get_db)
):
    """
    🚀 SAAS ONBOARDING (One-Click)
    Creates a new Tenant and its first Admin user.
    """
    try:
        # 1. 🛡️ Verification
        # Check if username or tenant exists
        user_check = await db.execute(select(DBUser).where(DBUser.username == payload.username))
        if user_check.scalars().first():
            raise HTTPException(status_code=400, detail="Username already exists")
            
        tenant_check = await db.execute(select(DBTenant).where(DBTenant.name == payload.tenant_name))
        if tenant_check.scalars().first():
            raise HTTPException(status_code=400, detail="Tenant name already taken")

        # 2. 🧱 Provisioning
        # Set quotas based on Plan
        quotas = {
            "FREE": 100000,
            "PRO": 5000000,
            "ENTERPRISE": 100000000
        }
        limit = quotas.get(payload.plan.upper(), 100000)

        # Create Tenant
        new_tenant = DBTenant(
            name=payload.tenant_name,
            api_key=f"sv_{secrets.token_urlsafe(32)}",
            plan=payload.plan.upper(),
            monthly_packet_limit=limit
        )
        db.add(new_tenant)
        await db.flush() # Get the new tenant ID

        # Create Admin User
        new_user = DBUser(
            tenant_id=new_tenant.id,
            username=payload.username,
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            roles=["admin", "billing_admin", "soc_manager"]
        )
        db.add(new_user)
        
        # 3. 📜 Audit Trail
        await log_audit(
            action="TENANT_REGISTER",
            target=new_tenant.id,
            tenant_id=new_tenant.id,
            result="SUCCESS",
            message=f"New SaaS onboarded: {payload.tenant_name} ({payload.plan})",
            metadata={"email": payload.email, "username": payload.username}
        )
        
        await db.commit()
        
        return {
            "message": "Welcome to StealthVault AI!",
            "tenant_id": new_tenant.id,
            "api_key": new_tenant.api_key,
            "plan": new_tenant.plan
        }
    except HTTPException as he:
        # Re-raise HTTPExceptions as they are already handled
        raise he
    except Exception as e:
        # Log and wrap generic exceptions
        print(f"CRITICAL ERROR in register_tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/beta/waitlist", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def join_waitlist(
    request: Request,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    🚀 THE STARTUP SEED: Capture early user interest.
    Enables zero-cost user validation before the full SaaS launch.
    """
    # 1. 🛡️ Verification
    check = await db.execute(select(DBWaitlist).where(DBWaitlist.email == email))
    if check.scalars().first():
        return {"message": "Welcome back! You're already on our priority list."}

    # 2. 🧱 Persistence
    new_entry = DBWaitlist(email=email)
    db.add(new_entry)
    
    # 3. 📜 Audit
    from app.core.audit import log_audit
    await log_audit(
        action="WAITLIST_JOIN",
        target=email,
        tenant_id="global",
        result="SUCCESS",
        message="New potential beta user onboarded."
    )
    
    await db.commit()
    
    return {
        "message": "Launch code received. You're now on the priority list!",
        "status": "confirmed"
    }
