# app/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .auth import decode_token  # FIXED: decode_token now takes only token
from .models import ADPUser, ADPRole, ADPUserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> ADPUser:
    """Get the current authenticated user from JWT token."""
    try:
        token_data = decode_token(token)  # FIXED: no second argument needed
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(ADPUser).filter(ADPUser.user_id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


def get_current_user_roles(db: Session = Depends(get_db), user: ADPUser = Depends(get_current_user)) -> list[str]:
    """Get the roles for the current user."""
    roles = (
        db.query(ADPUserRole, ADPRole)
        .join(ADPRole, ADPRole.role_code == ADPUserRole.role_code)
        .filter(ADPUserRole.user_id == user.user_id)
        .all()
    )
    return [r.ADPRole.role_code for r in roles]


def require_admin(
    user: ADPUser = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
) -> ADPUser:
    """Dependency that requires ADMIN or EMPLOYEE role."""
    if "ADMIN" not in roles and "EMPLOYEE" not in roles:
        raise HTTPException(status_code=403, detail="Admin/employee privileges required")
    return user
