from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

import models
from database import get_db

# --- Configuration ---
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_GOES_HERE" # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# --- Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Functions ---

def verify_password(plain_password, hashed_password):
    """Checks if a plain password matches a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generates a hash from a plain password."""
    return pwd_context.hash(password)

def authenticate_admin(db: Session, username: str, password: str) -> models.Admin | None:
    """Finds an admin and verifies their password."""
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if not admin:
        return None
    if not verify_password(password, admin.hashed_password):
        return None
    return admin

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Generates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Admin:
    """
    Dependency to get the current logged-in admin.
    This is used to protect endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if admin is None:
        raise credentials_exception
    return admin

# Alias for simplicity
get_current_active_admin = get_current_admin