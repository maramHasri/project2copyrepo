from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole, Book
from schemas import (
    UserCreate, User as UserSchema, Token, LoginRequest, RoleLoginRequest,
    OTPRequest, OTPVerify, OTPResponse, PasswordResetRequest, PasswordResetUpdate, PasswordResetResponse
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
    verify_otp,
    create_reset_token,
    verify_reset_token,
    mark_token_as_used
)
from gmail_utils import send_otp_email_gmail as send_otp_email, send_password_reset_email

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
    # Authenticate user by email instead of username
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is blocked by admin
    if user.is_blocked:
        reason = user.blocked_reason or "No reason provided"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"the system blocked you because {reason}"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
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



# OTP endpoints
@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(otp_request: OTPRequest):
    """Send OTP to email address"""
    otp = generate_otp()
    store_otp(otp_request.email, otp)
    send_otp_email(otp_request.email, otp)
    return OTPResponse(
        message="OTP sent successfully",
        success=True
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

# Password Reset endpoints
@router.post("/request-password-reset", response_model=PasswordResetResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset by email"""
    try:
        # Check if user exists with this email
        user = db.query(User).filter(User.email == reset_request.email).first()
        if not user:
            # For security, don't reveal if email exists or not
            return PasswordResetResponse(
                message="If an account with this email exists, a password reset link has been sent.",
                success=True
            )
        
        # Create reset token
        reset_token = create_reset_token(reset_request.email, db)
        
        # Send password reset email
        send_password_reset_email(reset_request.email, reset_token)
        
        return PasswordResetResponse(
            message="If an account with this email exists, a password reset link has been sent.",
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing password reset request: {str(e)}"
        )

@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    reset_data: PasswordResetUpdate,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        # Verify reset token
        email = verify_reset_token(reset_data.token, db)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)
        db.commit()
        
        # Mark token as used
        mark_token_as_used(reset_data.token, db)
        
        return PasswordResetResponse(
            message="Password has been reset successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )

 