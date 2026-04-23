"""
Authorization Helpers - Role-Based Access Control

Provides centralized authorization checks for all services:
- chercheur:      Can manage own applications
- admin_dpgr:     CS admin - can manage all applications, deliberations
- assistant_dpgr:  CS assistant - can manage all applications, deliberations  
- super_admin:    Only for user/system management (create/delete/edit users, settings)
"""

from uuid import UUID
from fastapi import HTTPException
from app.core.database import AsyncSession
from app.models.user import User
from app.models.enums import UserRole


async def verify_user_exists(user_id: UUID, db: AsyncSession) -> User:
    """Verify user exists in database"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def verify_chercheur_role(user_id: UUID, db: AsyncSession) -> User:
    """
    Verify user is a chercheur (researcher).
    
    Args:
        user_id: User to verify
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException(403) if not chercheur
    """
    user = await verify_user_exists(user_id, db)
    
    if user.role != UserRole.chercheur:
        raise HTTPException(
            status_code=403,
            detail="This action requires chercheur role"
        )
    
    return user


async def verify_cs_admin_role(user_id: UUID, db: AsyncSession) -> User:
    """
    Verify user is CS admin (admin_dpgr or assistant_dpgr).
    Super admin is NOT included - use super_admin verifier for admin operations.
    
    Args:
        user_id: User to verify
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException(403) if not CS admin
    """
    user = await verify_user_exists(user_id, db)
    
    if user.role not in [UserRole.admin_dpgr, UserRole.assistant_dpgr]:
        raise HTTPException(
            status_code=403,
            detail="CS operations require admin_dpgr or assistant_dpgr role"        )
    
    return user


async def verify_super_admin_role(user_id: UUID, db: AsyncSession) -> User:
    """
    Verify user is super admin.
    
    Used ONLY for:
    - Creating/editing/deleting users
    - System settings management
    - Adding/removing administrative roles
    
    Args:
        user_id: User to verify
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException(403) if not super_admin
    """
    user = await verify_user_exists(user_id, db)
    
    if user.role != UserRole.super_admin:
        raise HTTPException(
            status_code=403,
            detail="This action requires super_admin role"
        )
    
    return user


async def verify_cs_admin_or_chercheur(user_id: UUID, db: AsyncSession) -> User:
    """
    Verify user is either chercheur or CS admin.
    
    Used for operations where both roles can read/view applications.
    
    Args:
        user_id: User to verify
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException(403) if neither role
    """
    user = await verify_user_exists(user_id, db)
    
    allowed_roles = [UserRole.chercheur, UserRole.admin_dpgr, UserRole.assistant_dpgr]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="This action requires chercheur or CS admin role"
        )
    
    return user


async def verify_ownership(owner_id: UUID, requester_id: UUID) -> None:
    """
    Verify that requester is the owner of a resource.
    
    Args:
        owner_id: ID of the resource owner
        requester_id: ID of the user making the request
        
    Raises:
        HTTPException(403) if not the owner
    """
    if owner_id != requester_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this resource"
        )
