from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserLogin, Token, UserResponse
from ..auth import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    email = login_data.email.strip().lower()
    password = login_data.password

    user = db.query(User).filter(User.email == email).first()

    # If demo credentials are supplied and user is missing, initialize on-the-fly
    if not user and email == "demo@oasense.ai" and password == "demo123":
        user = User(
            name="Dr. Sarah Mitchell",
            email="demo@oasense.ai",
            password_hash=get_password_hash("demo123"),
            role="healthcare_worker"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.name},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.name,
        "user_email": user.email,
        "role": user.role
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_db)):
    # Simple verification helper
    user = current_user.query(User).filter(User.email == "demo@oasense.ai").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
