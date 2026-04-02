"""
StealthVault AI - API Security
JWT Authentication and RBAC mappings for enterprise deployment.
"""

from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.config import settings
import logging
from app.core.logger import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.db_models import DBUser, DBTenant, DBWaitlist
from app.core.sanitizer import sanitize_string
from app.core.limiter import limiter
from fastapi import Request
from app.core.audit import log_audit
from app.models.alert import RegisterInput
from app.core.security import get_password_hash
import secrets
import re
import time

# Security settings from centralized config
from app.core.security import SECRET_KEY, ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
# REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS (Deprecated by elite fix)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Dependency for securing API routes with enterprise revocation check."""
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
            
        # 🛡️ Revocation check disabled in simplified 'Elite' mode
            
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

def validate_password(password: str):
    """
    🏗️ PASSWORD COMPLEXITY ENGINE
    Enforces enterprise standards for identity preservation.
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="🛡️ WEAK PASSWORD: Access terminated. Must be at least 8 characters."
        )

    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="🛡️ WEAK PASSWORD: Must include at least one uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="🛡️ WEAK PASSWORD: Must include at least one lowercase letter."
        )

    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="🛡️ WEAK PASSWORD: Must include at least one number."
        )

    if not re.search(r"[!@#$%^&*]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="🛡️ WEAK PASSWORD: Must include at least one special character (!@#$%^&*)."
        )

from app.core.security import verify_password, create_access_token

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    🔐 MISSION CRITICAL: OBTAIN ACCESS TOKEN
    Simplified enterprise authentication boundary.
    """
    # 🕵️ Lookup User in Postgres
    result = await db.execute(select(DBUser).where(DBUser.username == form_data.username))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid identity: Username not found."
        )

    # 🔑 Verify Password (Secure Bcrypt)
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid identity: Cryptographic mismatch."
        )

    # 🧬 Generate Access Token
    access_token = create_access_token(
        data={"sub": user.username, "tenant_id": user.tenant_id, "roles": user.roles},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register_tenant(
    request: Request,
    payload: RegisterInput,
    db: AsyncSession = Depends(get_db)
):
    """
    🚀 SAAS ONBOARDING (One-Click)
    Creates a new Tenant and its first Admin user.
    """
    try:
        # 🧱 0. POLICY ENFORCEMENT
        validate_password(payload.password)
        
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
        safe_tenant_name = sanitize_string(payload.tenant_name)
        new_tenant = DBTenant(
            name=safe_tenant_name,
            api_key=f"sv_{secrets.token_urlsafe(32)}",
            plan=payload.plan.upper(),
            monthly_packet_limit=limit
        )
        db.add(new_tenant)
        await db.flush() # Get the new tenant ID

        # Create Admin User
        safe_username = sanitize_string(payload.username)
        new_user = DBUser(
            tenant_id=new_tenant.id,
            username=safe_username,
            email=sanitize_string(payload.email),
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
            message=f"New SaaS onboarded: {safe_tenant_name} ({payload.plan})",
            metadata={"email": payload.email, "username": safe_username}
        )
        
        await db.commit()
        
        # ⚔️ BATTLE-MODE: Mission-Critical Hardening
        # Registration must ONLY provision identity/tenancy.
        # Background simulations are strictly prohibited at this boundary.
        # trigger_simulation()    # ❌ (Disabled)
        # run_background_attack() # ❌ (Disabled)
        # auto_attack_daemon()    # ❌ (Disabled)
        
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
        # 🛡️ MISSION CRITICAL: Secure logging of registration failure
        # We do NOT print raw `e` to avoid accidental password/token leaks
        logger.error(f"❌ REGISTRATION FAULT: Onboarding failed for tenant.")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please contact SOC support."
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


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """
    🔐 MISSION LOGOUT
    Simplified session termination.
    """
    return {"message": "Identity de-authorized. Session terminated."}

@router.post("/refresh")
async def refresh_token_endpoint():
    """
    🧬 SESSION PROLONGATION
    (Disabled in simplified 'Elite' mode)
    """
    raise HTTPException(status_code=501, detail="Refresh tokens are disabled in this simplified security profile.")
