from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Publisher, UserRole, Book
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
    
    # Validate admin registration
    if user.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is not allowed through this endpoint"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        full_name=user.full_name,
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Admin registration (protected)
@router.post("/register/admin", response_model=UserSchema)
async def register_admin(user: UserCreate, admin_code: str, db: Session = Depends(get_db)):
    # Verify admin code
    if admin_code != ADMIN_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin code"
        )
    
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
    
    # Create new admin
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        full_name=user.full_name,
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        role=UserRole.admin
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

@router.post("/upgrade-to-publisher", response_model=UserSchema)
async def upgrade_to_publisher(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.writer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only writers can upgrade to publisher role"
        )
    
    # Check if user has published at least 3 books
    book_count = db.query(Book).filter(Book.author_id == current_user.id).count()
    if book_count < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must have published at least 3 books to become a publisher"
        )
    
    current_user.role = UserRole.publisher
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/debug/me")
async def debug_current_user(current_user: User = Depends(get_current_active_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@router.get("/test-auth")
async def test_authentication(current_user: User = Depends(get_current_active_user)):
    return {
        "message": "Authentication successful!",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        }
    }

# OTP endpoints
@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(otp_request: OTPRequest):
    """Send OTP to email address"""
    otp = generate_otp()
    store_otp(otp_request.email, otp)
    
    # In production, send email here
    # For now, we'll return the OTP for testing
    return OTPResponse(
        message="OTP sent successfully",
        otp=otp  # Remove this in production
    )

@router.post("/verify-otp", response_model=dict)
async def verify_otp_endpoint(otp_verify: OTPVerify):
    """Verify OTP for email address"""
    if verify_otp(otp_verify.email, otp_verify.otp):
        return {"message": "OTP verified successfully", "verified": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

# Debug endpoint to check user status
@router.get("/debug/user-info")
async def debug_user_info(current_user: User = Depends(get_current_active_user)):
    """Debug endpoint to check current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    } 