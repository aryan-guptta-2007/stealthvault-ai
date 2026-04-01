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
import re
import time

# Security settings from centralized config
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 🔐 Add cryptographic unique ID (jti) for revocation
    if "jti" not in to_encode:
        to_encode.update({"jti": str(uuid.uuid4())})
        
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    🧬 GENERATE LONG-LIVED REFRESH TOKEN
    Used to obtain new access tokens without re-authenticating.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
        jti: str = payload.get("jti")
        token_type: str = payload.get("type", "access")

        if username is None or tenant_id is None or jti is None or token_type != "access":
            raise credentials_exception
            
        # 🛡️ REVOCATION CHECK: Is this token blacklisted?
        from app.models.db_models import DBRevokedToken
        revoked_check = await db.execute(select(DBRevokedToken).where(DBRevokedToken.jti == jti))
        if revoked_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="🛡️ SESSION EXPIRED: This token has been revoked or logged out.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except jwt.PyJWTError:
        raise credentials_exception
        
    class CurrentUser:
        def __init__(self, username, tenant_id, roles, uid, jti):
            self.username = username
            self.tenant_id = tenant_id
            self.roles = roles
            self.uid = uid
            self.jti = jti
            
    return CurrentUser(username, tenant_id, roles, payload.get("uid"), jti)
 
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
    
    # 1. BRUTE-FORCE COUNTERMEASURE: Account Lock Check
    if user.locked_until and user.locked_until > datetime.utcnow():
        lock_remaining = (user.locked_until - datetime.utcnow()).total_seconds() / 60
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"🛡️ ACCOUNT LOCKED: Brute-force violation detected. Try again in {int(lock_remaining)} minutes."
        )

    # 2. Secure Password Verification (Bcrypt)
    if not user or not verify_password(form_data.password, user.password_hash):
        # ⏳ SLOWDOWN: Defensive friction against bots
        time.sleep(1.0)
        
        # 🔔 Tracking Failed Attempt
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=10)
                message = "Account locked due to excessive failed attempts."
            else:
                message = f"Invalid credentials. Attempt {user.failed_attempts}/5"
            await db.commit()
        else:
            message = "Invalid credentials"

        # 🛡️ AUDIT: Failed Login Attempt
        failed_tenant = user.tenant_id if user else "global"
        await log_audit(
            action="LOGIN",
            target=form_data.username,
            tenant_id=failed_tenant,
            result="FAILURE",
            message=message,
            metadata={"ip": request.client.host}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. MISSION SUCCESS: Reset session state
    user.failed_attempts = 0
    user.locked_until = None
    await db.commit()
        
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
    
    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "tenant_id": user.tenant_id,
            "uid": user.id
        }
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

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


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


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    🔐 MISSION LOGOUT: Revoke current session.
    Blacklists the active access token until it naturally expires.
    """
    from app.models.db_models import DBRevokedToken
    
    # 🛡️ Cryptographically revoke the token
    revocation = DBRevokedToken(
        jti=getattr(current_user, "jti"),
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(revocation)
    
    # 🛡️ AUDIT: Logout
    await log_audit(
        action="LOGOUT",
        target=current_user.username,
        tenant_id=current_user.tenant_id,
        user_id=current_user.uid,
        username=current_user.username,
        result="SUCCESS",
        metadata={"ip": request.client.host}
    )
    
    await db.commit()
    return {"message": "Identity de-authorized. Session terminated."}

@router.post("/refresh")
async def refresh_token_endpoint(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    🧬 SESSION PROLONGATION: Swap valid refresh token for a new access token.
    Enables smooth UX without compromising long-term token security.
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        username = payload.get("sub")
        # Find user to get latest roles
        result = await db.execute(select(DBUser).where(DBUser.username == username))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        # Issue new Access Token
        new_access_token = create_access_token(
            data={
                "sub": user.username,
                "tenant_id": user.tenant_id,
                "roles": user.roles,
                "uid": user.id
            }
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
