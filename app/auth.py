from datetime import datetime, timedelta
from typing import List

from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings
from .schemas import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: int, roles: List[str]) -> str:
    to_encode = {
        "sub": str(user_id),
        "roles": roles,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str = payload.get("sub")
        roles = payload.get("roles", [])
        if user_id_str is None:
            raise ValueError("Missing sub claim")
        return TokenData(user_id=int(user_id_str), roles=roles)
    except JWTError as e:
        raise ValueError("Invalid token") from e