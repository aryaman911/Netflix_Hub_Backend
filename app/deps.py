# app/deps.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user, get_user_roles, decode_token
from .models import ADPUser, ADPAccount
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user_roles(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user)
) -> list[str]:
    """Get the roles for the current user."""
    return get_user_roles(db, user.user_id)


def require_admin(
    user: ADPUser = Depends(get_current_user),
    roles: list[str] = Depends(get_current_user_roles),
) -> ADPUser:
    """Dependency that requires ADMIN or EMPLOYEE role."""
    if "ADMIN" not in roles and "EMPLOYEE" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin/employee privileges required"
        )
    return user


def require_role(required_roles: list[str]):
    """Factory to create a dependency that requires specific roles."""
    def checker(
        user: ADPUser = Depends(get_current_user),
        roles: list[str] = Depends(get_current_user_roles),
    ) -> ADPUser:
        if not any(r in roles for r in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(required_roles)}"
            )
        return user
    return checker


def get_current_account(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user)
) -> ADPAccount:
    """Get the account linked to the current user."""
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user.user_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No account linked to this user. Please create an account first."
        )
    return account
