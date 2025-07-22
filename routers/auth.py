from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole, Book
from schemas import (
    UserCreate, User as UserSchema, Token, LoginRequest, RoleLoginRequest,
    OTPRequest, OTPVerify, OTPResponse
)
from security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ADMIN_CODE,
    generate_otp,
    store_otp,
    verify_otp
)

from typing import Optional

router = APIRouter()

# General registration with role selection
@router.post("/register", response_model=UserSchema)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if phone number already exists
    db_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Check if email already exists (if provided)
    if user.email:
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Note: Admin registration is now handled by /admin/register endpoint
    # This endpoint is only for regular users (readers/writers)
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        full_name=user.full_name,
        phone_number=user.phone_number,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    

    
    return db_user



# General login
@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

# Role-specific login
@router.post("/login/{role}", response_model=Token)
async def login_with_role(
    role: UserRole,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has the required role
    if user.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have {role} role"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

# Role upgrade endpoints
@router.post("/upgrade-to-writer", response_model=UserSchema)
async def upgrade_to_writer(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.reader:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only readers can upgrade to writer role"
        )
    
    current_user.role = UserRole.writer
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user



# OTP endpoints
@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(otp_request: OTPRequest):
    """Send OTP to email address"""
    # Use constant OTP for testing
    TEST_OTP = "123456"
    otp = TEST_OTP
    store_otp(otp_request.email, otp)
    
    # For now, just return the OTP (email service removed)
    return OTPResponse(
        message="OTP generated successfully",
        success=True,
        otp=otp  # Always include the constant OTP for testing
    )

@router.post("/verify-otp", response_model=dict)
async def verify_otp_endpoint(otp_verify: OTPVerify):
    """Verify OTP for email address"""
    if verify_otp(otp_verify.email, otp_verify.otp):
        return {
            "message": "OTP verified successfully", 
            "verified": True,
            "email": otp_verify.email
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

 