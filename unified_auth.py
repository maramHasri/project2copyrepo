#!/usr/bin/env python3
"""
Unified Authentication System
Handles authentication for Users and PublisherHouses ONLY
Admin has separate authentication system
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, PublisherHouse, UserRole
from schemas import TokenData
import enum

# Security configuration
SECRET_KEY = "N93qNdu1uEX7oKM3ZQnHdV02TIuRt4umLG07eV4JhzI"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

# Unified role system (NO ADMIN - admin has separate system)
class UnifiedRole(str, enum.Enum):
    # User roles only
    reader = "reader"
    writer = "writer"
    # Publisher roles
    publisher = "publisher"

class UnifiedUser:
    """Unified user object that can represent User or PublisherHouse (NOT Admin)"""
    def __init__(self, id: int, username: str, role: str, entity_type: str, **kwargs):
        self.id = id
        self.username = username
        self.role = role
        self.entity_type = entity_type  # "user" or "publisher" (NOT "admin")
        for key, value in kwargs.items():
            setattr(self, key, value)

async def get_bearer_token(authorization: Optional[str] = Header(None, include_in_schema=False)) -> str:
    """Extract bearer token from authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

async def get_unified_user(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> UnifiedUser:
    """Get unified user from token (User or PublisherHouse ONLY - NO Admin)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        entity_type: str = payload.get("entity_type", "user")
        
        if username is None:
            raise credentials_exception
        
        # REJECT admin tokens - admin has separate authentication
        if entity_type == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin authentication not allowed in unified system. Use /admin/login"
            )
            
    except JWTError:
        raise credentials_exception
    
    # Try to find user first
    user = db.query(User).filter(User.username == username).first()
    if user:
        return UnifiedUser(
            id=user.id,
            username=user.username,
            role=user.role.value,
            entity_type="user",
            is_active=user.is_active,
            is_verified=user.is_verified,
            email=user.email,
            full_name=user.full_name
        )
    
    # Try to find publisher house
    publisher = db.query(PublisherHouse).filter(PublisherHouse.name == username).first()
    if publisher:
        return UnifiedUser(
            id=publisher.id,
            username=publisher.name,
            role="publisher",
            entity_type="publisher",
            is_active=publisher.is_active,
            is_verified=publisher.is_verified,
            email=publisher.email
        )
    
    raise credentials_exception

async def get_current_unified_user(current_user: UnifiedUser = Depends(get_unified_user)) -> UnifiedUser:
    """Get current active unified user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def create_unified_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token with entity type information (NO ADMIN)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Role checking functions (NO ADMIN)
def check_unified_role(allowed_roles: list[str]):
    """Check if user has any of the allowed roles (NO ADMIN)"""
    async def role_checker(current_user: UnifiedUser = Depends(get_current_unified_user)) -> UnifiedUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of these roles: {', '.join(allowed_roles)}. Current role: {current_user.role}"
            )
        return current_user
    return role_checker

def check_writer_publisher_role():
    """Check if user is writer or publisher (NO ADMIN)"""
    return check_unified_role(["writer", "publisher"])

def check_publisher_role():
    """Check if user is publisher (NO ADMIN)"""
    return check_unified_role(["publisher"])

def check_writer_role():
    """Check if user is writer (NO ADMIN)"""
    return check_unified_role(["writer"])

def check_reader_writer_role():
    """Check if user is reader or writer (NO ADMIN)"""
    return check_unified_role(["reader", "writer"])

# Debug function
async def debug_unified_auth(current_user: UnifiedUser = Depends(get_current_unified_user)):
    """Debug endpoint to show unified user information (NO ADMIN)"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "entity_type": current_user.entity_type,
        "is_active": getattr(current_user, 'is_active', None),
        "is_verified": getattr(current_user, 'is_verified', None),
        "email": getattr(current_user, 'email', None),
        "note": "This is unified auth - admin uses separate /admin/login"
    } 