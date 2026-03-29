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
        # Check if user object has 'roles' attribute
        if not hasattr(user, 'roles'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User permissions not correctly configured"
            )
            
        # Check if any allowed role matches user's roles
        # Roles are stored as a list in JWT/DB [e.g., ["admin", "soc_analyst"]]
        user_roles = getattr(user, 'roles', [])
        
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {self.allowed_roles}"
            )
            
        return user
