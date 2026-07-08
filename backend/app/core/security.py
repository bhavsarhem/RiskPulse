from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
import hashlib
import os
from backend.app.core.config import settings

ALGORITHM = "HS256"
ITERATIONS = 100000

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against the stored pbkdf2 hash."""
    try:
        if not hashed_password or ":" not in hashed_password:
            return False
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        
        # Hash input password with same salt
        new_key = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode('utf-8'), 
            salt, 
            ITERATIONS
        )
        return new_key == key
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generates a secure PBKDF2 hash using a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt, 
        ITERATIONS
    )
    return f"{salt.hex()}:{key.hex()}"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
