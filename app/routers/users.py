# app/routers/users.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.auth import get_user_roles

router = APIRouter()


# -------------------------------------------------------------------------
# GET CURRENT USER (ME)
# -------------------------------------------------------------------------

@router.get("/me", response_model=schemas.UserRead)
def get_me(user: models.ADPUser = Depends(get_current_user)):
    """Get the current authenticated user."""
    return schemas.UserRead(
        id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
    )


@router.get("/me/roles", response_model=List[str])
def get_my_roles(
    db: Session = Depends(get_db),
    user: models.ADPUser = Depends(get_current_user),
):
    """Get the roles of the current user."""
    return get_user_roles(db, user.user_id)


# -------------------------------------------------------------------------
# LIST USERS (ADMIN)
# -------------------------------------------------------------------------

@router.get("/", response_model=List[schemas.UserRead])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """List all users (admin only)."""
    users = db.query(models.ADPUser).offset(skip).limit(limit).all()
    return [
        schemas.UserRead(
            id=u.user_id,
            email=u.email,
            username=u.username,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=schemas.UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Get a specific user by ID (admin only)."""
    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserRead(
        id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
    )


# -------------------------------------------------------------------------
# ROLE MANAGEMENT (ADMIN)
# -------------------------------------------------------------------------

@router.get("/roles/all", response_model=List[schemas.RoleRead])
def list_all_roles(
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """List all available roles (admin only)."""
    roles = db.query(models.ADPRole).all()
    return roles


@router.post("/roles/assign", status_code=status.HTTP_204_NO_CONTENT)
def assign_role(
    payload: schemas.UserRoleAssign,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Assign a role to a user (admin only)."""
    # Check user exists
    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check role exists
    role = db.query(models.ADPRole).filter(models.ADPRole.role_code == payload.role_code).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if already assigned
    existing = (
        db.query(models.ADPUserRole)
        .filter(
            models.ADPUserRole.user_id == payload.user_id,
            models.ADPUserRole.role_code == payload.role_code,
        )
        .first()
    )
    if existing:
        return  # Already assigned

    # Assign role
    user_role = models.ADPUserRole(user_id=payload.user_id, role_code=payload.role_code)
    db.add(user_role)
    db.commit()


@router.delete("/roles/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_role(
    payload: schemas.UserRoleAssign,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Revoke a role from a user (admin only)."""
    user_role = (
        db.query(models.ADPUserRole)
        .filter(
            models.ADPUserRole.user_id == payload.user_id,
            models.ADPUserRole.role_code == payload.role_code,
        )
        .first()
    )
    if not user_role:
        raise HTTPException(status_code=404, detail="User does not have this role")

    db.delete(user_role)
    db.commit()


@router.get("/{user_id}/roles", response_model=List[str])
def get_user_roles_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Get roles for a specific user (admin only)."""
    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return get_user_roles(db, user_id)


# -------------------------------------------------------------------------
# DEACTIVATE USER (ADMIN)
# -------------------------------------------------------------------------

@router.post("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Deactivate a user account (admin only)."""
    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()


@router.post("/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Activate a user account (admin only)."""
    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
