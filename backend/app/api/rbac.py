"""
StealthVault AI - RBAC Enforcement
Dependency factory for role-based access control.
"""

from typing import List
from fastapi import Depends, HTTPException, status
from app.api.auth import get_current_user

class RoleChecker:
    """Dependency factory that checks if current user has any of the required roles."""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
        
    def __call__(self, user: object = Depends(get_current_user)):
        """Check for role intersection."""
        # 🔑 ADMIN OVERRIDE
        # Admins are the system's "Mission Commanders" and bypass all RBAC checks.
        user_roles = getattr(user, 'roles', [])
        if "admin" in user_roles:
            return user
            
        # 🛡️ ROLE VALIDATION
        if not any(role in user_roles for role in self.allowed_roles):
            # 📜 AUDIT: Unauthorized Access Attempt
            # Log the attempt for forensic analysis and mission sabotage prevention.
            from app.core.logger import logger
            logger.warning(
                f"🚫 RBAC FAILURE | User: {getattr(user, 'username', 'unknown')} | "
                f"Roles: {user_roles} | Required: {self.allowed_roles}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"🛡️ MISSION ACCESS DENIED: Your current SOC privileges ('{user_roles}') "
                    f"do not permit this tactical operation. Required: {self.allowed_roles}"
                )
            )
            
        return user
