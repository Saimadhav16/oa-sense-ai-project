import os
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "oasense_ai_secure_development_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
DEMO_USER_EMAIL = os.getenv("DEMO_USER_EMAIL", "demo@oasense.ai")
DEMO_USER_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "demo123")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        demo_user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if demo_user:
            return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def seed_demo_user(db: Session):
    """Seed the default demo healthcare worker account if it doesn't already exist."""
    existing = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
    if not existing:
        demo_user = User(
            name="Dr. Sarah Mitchell",
            email=DEMO_USER_EMAIL,
            password_hash=get_password_hash(DEMO_USER_PASSWORD),
            role="healthcare_worker",
            created_at=datetime.utcnow()
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print(f"[AUTH] Seeded demo user account: {DEMO_USER_EMAIL}")
    else:
        # Update hash if needed
        if not verify_password(DEMO_USER_PASSWORD, existing.password_hash):
            existing.password_hash = get_password_hash(DEMO_USER_PASSWORD)
            db.commit()
