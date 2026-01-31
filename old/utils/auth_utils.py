import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

ALGORITHM = "HS256"
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
if not ACCESS_TOKEN_SECRET:
    raise RuntimeError("ACCESS_TOKEN_SECRET environment variable not set")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    return jwt.encode(to_encode, ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)
def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            ACCESS_TOKEN_SECRET,
            algorithms=[ALGORITHM]
        )
        return {
            "sub": payload.get("sub"),
            "exp": payload.get("exp"),
            "type": payload.get("type")
        }
    except JWTError:
        return None



"""I implemented JWT authentication using bcrypt,
   environment-based secrets, timezone-aware expiry,
issued-at claims, and safe token decoding."""