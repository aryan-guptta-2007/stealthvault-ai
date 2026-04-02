import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.db_models import DBTenant, DBUser
from app.core.security import get_password_hash
from app.api.auth import get_current_user

router = APIRouter(prefix="/saas", tags=["SaaS Onboarding"])

class TenantRegister(BaseModel):
    """Schema for new tenant registration."""
    tenant_name: str = Field(..., min_length=3, max_length=100)
    admin_username: str = Field(..., min_length=3, max_length=50)
    admin_password: str = Field(..., min_length=8)

class TenantResponse(BaseModel):
    """Schema for registration response."""
    tenant_id: str
    tenant_name: str
    api_key: str
    admin_username: str
    message: str

@router.post("/register", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(request: TenantRegister, db: AsyncSession = Depends(get_db)):
    """
    🏢 REGISTER A NEW TENANT
    
    This creates an isolated environment for a new customer,
    generates a unique Sensor API Key, and sets up the primary 
    Admin account for their team.
    """
    try:
        # 1. Check if tenant name already exists
        result = await db.execute(select(DBTenant).where(DBTenant.name == request.tenant_name))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tenant with this name already exists."
            )
        
        # 2. Check if username already exists
        user_result = await db.execute(select(DBUser).where(DBUser.username == request.admin_username))
        if user_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken."
            )
        
        print(f"DEBUG [saas/register]: Registering {request.tenant_name} with admin {request.admin_username}")
        print(f"DEBUG [saas/register]: Password length: {len(request.admin_password)}")

        # 3. Create Tenant
        tenant_id = str(uuid.uuid4())
        api_key = f"sv_{secrets.token_urlsafe(32)}"
        
        new_tenant = DBTenant(
            id=tenant_id,
            name=request.tenant_name,
            api_key=api_key
        )
        db.add(new_tenant)
        await db.flush()
        
        # 4. Create Admin User
        admin_pass = str(request.admin_password)
        new_user = DBUser(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            username=request.admin_username,
            password_hash=get_password_hash(admin_pass),
            roles=["admin", "soc_analyst"]
        )
        db.add(new_user)
        
        await db.commit()
        await db.refresh(new_tenant)
        
        # ⚔️ BATTLE-MODE: Mission-Critical Hardening
        # Registration must ONLY provision identity/tenancy.
        # Background simulations are strictly prohibited at this boundary.
        # trigger_simulation()    # ❌ (Disabled)
        # run_background_attack() # ❌ (Disabled)
        # auto_attack_daemon()    # ❌ (Disabled)
        
        return TenantResponse(
            tenant_id=new_tenant.id,
            tenant_name=new_tenant.name,
            api_key=new_tenant.api_key,
            admin_username=new_user.username,
            message="🚀 StealthVault AI environment successfully provisioned."
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"CRITICAL ERROR in saas/register: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SaaS Provisioning failed: {str(e)}"
        )

from app.api.rbac import RoleChecker

class UserCreate(BaseModel):
    """Schema for adding a new user to an existing tenant."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    roles: list[str] = Field(default=["soc_analyst"])

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def add_tenant_user(
    request: UserCreate, 
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    👥 ADD TEAM MEMBER
    
    Admins can invite new analysts or viewers to their tenant.
    All data remains strictly siloed within the tenant boundary.
    """
    try:
        tenant_id = getattr(current_user, "tenant_id", None)
        
        # Check if username already exists globally
        user_result = await db.execute(select(DBUser).where(DBUser.username == request.username))
        if user_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken."
            )
        
        # Create User
        new_user = DBUser(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            username=request.username,
            password_hash=get_password_hash(request.password),
            roles=request.roles
        )
        db.add(new_user)
        await db.commit()
        
        return {
            "id": new_user.id,
            "username": new_user.username,
            "roles": new_user.roles,
            "message": f"Successfully added {request.username} to your SOC team."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"CRITICAL ERROR in add_tenant_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team member: {str(e)}"
        )

@router.get("/users", response_model=list)
async def list_tenant_users(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users belonging to the current tenant."""
    tenant_id = getattr(current_user, "tenant_id", None)
    result = await db.execute(select(DBUser).where(DBUser.tenant_id == tenant_id))
    users = result.scalars().all()
    
    return [
        {"id": u.id, "username": u.username, "roles": u.roles, "created_at": u.created_at}
        for u in users
    ]

@router.get("/tenant", response_model=dict)
async def get_my_tenant(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retrieve details about the current logged-in tenant."""
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
         raise HTTPException(status_code=404, detail="Tenant context not found for user.")
    
    result = await db.execute(select(DBTenant).where(DBTenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
        
    return {
        "id": tenant.id,
        "name": tenant.name,
        "api_key": tenant.api_key,
        "created_at": tenant.created_at,
        "role": current_user.roles
    }
