from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, PublisherHouse, UserRole
from schemas import UnifiedToken, LoginRequest
from security import verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from unified_auth import create_unified_access_token, get_current_unified_user, debug_unified_auth

router = APIRouter()

@router.post("/login", response_model=UnifiedToken)
async def unified_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Unified login for Users and PublisherHouses ONLY
    Admin uses separate /admin/login endpoint
    Automatically detects the entity type and returns appropriate token
    """
    
    # Try to authenticate as User first
    user = db.query(User).filter(User.username == login_data.username).first()
    if user and verify_password(login_data.password, user.hashed_password):
        # Create token for user (reader/writer)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_unified_access_token(
            data={
                "sub": user.username,
                "entity_type": "user",
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role.value,
            "entity_type": "user",
            "user_id": user.id
        }
    
    # Try to authenticate as PublisherHouse
    publisher = db.query(PublisherHouse).filter(PublisherHouse.name == login_data.username).first()
    if publisher and verify_password(login_data.password, publisher.hashed_password):
        # Create token for publisher
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_unified_access_token(
            data={
                "sub": publisher.name,
                "entity_type": "publisher",
                "role": "publisher"
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "publisher",
            "entity_type": "publisher",
            "user_id": publisher.id
        }
    
    # If neither found, raise error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password. Note: Admin login is at /admin/login",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/login/user", response_model=UnifiedToken)
async def user_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login specifically for Users (readers/writers)"""
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_unified_access_token(
        data={
            "sub": user.username,
            "entity_type": "user",
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "entity_type": "user",
        "user_id": user.id
    }

@router.post("/login/publisher", response_model=UnifiedToken)
async def publisher_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login specifically for PublisherHouses"""
    publisher = db.query(PublisherHouse).filter(PublisherHouse.name == login_data.username).first()
    if not publisher or not verify_password(login_data.password, publisher.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_unified_access_token(
        data={
            "sub": publisher.name,
            "entity_type": "publisher",
            "role": "publisher"
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "publisher",
        "entity_type": "publisher",
        "user_id": publisher.id
    }

@router.get("/me")
async def get_unified_profile(current_user = Depends(get_current_unified_user)):
    """Get current user/publisher profile (NO ADMIN)"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "entity_type": current_user.entity_type,
        "is_active": getattr(current_user, 'is_active', None),
        "is_verified": getattr(current_user, 'is_verified', None),
        "email": getattr(current_user, 'email', None),
        "note": "Admin profiles are accessed via /admin/me"
    }

@router.get("/debug")
async def debug_endpoint():
    """Debug endpoint to show unified authentication info"""
    return {
        "message": "Unified Authentication System",
        "description": "Handles Users (readers/writers) and PublisherHouses ONLY",
        "admin_note": "Admin authentication is separate at /admin/login",
        "token_types": {
            "user": "For readers and writers",
            "publisher": "For publisher houses",
            "admin": "Separate system at /admin/login"
        },
        "permissions": {
            "readers": "Can read books, save favorites, view publishers",
            "writers": "Can create books, manage their content, view publishers",
            "publishers": "Can manage their books, create vacancies, view writers",
            "admins": "Separate system with full management permissions"
        }
    } 