from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Admin, AdminRole, AdminAction, PublisherHouse
from schemas import AdminCreate, Admin as AdminSchema, AdminUpdate, LoginRequest, PublisherHouse as PublisherHouseSchema
from security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ADMIN_CODE,
    SECRET_KEY,
    ALGORITHM
)

from typing import Optional, List
from jose import JWTError, jwt
import json

router = APIRouter()

# Helper functions for dependencies (moved to top)
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
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return authorization.replace("Bearer ", "")

async def get_current_admin(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> Admin:
    """Get current admin from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        entity_type: str = payload.get("entity_type")
        
        if username is None or entity_type != "admin":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None:
        raise credentials_exception
    
    return admin

async def get_super_admin(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    """Check if admin is super admin"""
    if not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_admin

# Admin Registration (Super Admin Only)
@router.post("/register", response_model=AdminSchema)
async def register_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db)
):
    """Register a new admin (requires admin code)"""
    
    # Verify admin code
    if admin_data.admin_code != ADMIN_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin code"
        )
    
    # Check if username already exists
    existing_admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Set permissions based on role
    permissions = {
        "can_manage_users": admin_data.role in [AdminRole.user_admin, AdminRole.super_admin],
        "can_manage_publishers": admin_data.role in [AdminRole.publisher_admin, AdminRole.super_admin],
        "can_manage_content": admin_data.role in [AdminRole.content_admin, AdminRole.super_admin],
        "can_manage_system": admin_data.role == AdminRole.super_admin
    }
    
    # Create new admin
    hashed_password = get_password_hash(admin_data.password)
    db_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        phone_number=admin_data.phone_number,
        hashed_password=hashed_password,
        role=admin_data.role,
        is_super_admin=admin_data.role == AdminRole.super_admin,
        permissions=json.dumps(permissions),
        **permissions
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    

    
    return db_admin

# Admin Login
@router.post("/login")
async def admin_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login for admin users"""
    
    # Authenticate admin
    admin = db.query(Admin).filter(Admin.email == login_data.email).first()
    if not admin or not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin account is inactive"
        )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": admin.username,
            "entity_type": "admin",
            "role": admin.role.value,
            "is_super_admin": admin.is_super_admin
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": admin.role.value,
        "entity_type": "admin",
        "admin_id": admin.id,
        "username": admin.username,
        "is_super_admin": admin.is_super_admin,
        "permissions": {
            "can_manage_users": admin.can_manage_users,
            "can_manage_publishers": admin.can_manage_publishers,
            "can_manage_content": admin.can_manage_content,
            "can_manage_system": admin.can_manage_system
        }
    }

# Get Admin Profile
@router.get("/me", response_model=AdminSchema)
async def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get current admin profile"""
    return current_admin

# Update Admin Profile
@router.put("/me", response_model=AdminSchema)
async def update_admin_profile(
    admin_update: AdminUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    
    if admin_update.phone_number is not None:
        current_admin.phone_number = admin_update.phone_number
    if admin_update.permissions is not None:
        current_admin.permissions = admin_update.permissions
    
    db.commit()
    db.refresh(current_admin)
    
    return current_admin

# Get All Admins (Super Admin Only)
@router.get("/", response_model=List[AdminSchema])
async def get_all_admins(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """Get all admins (super admin only)"""
    admins = db.query(Admin).offset(skip).limit(limit).all()
    return admins

# Route: Get all publisher registration requests (admin only)
@router.get("/publisher-requests", response_model=list[PublisherHouseSchema])
def get_all_publisher_requests(db: Session = Depends(get_db)):
    """Get all publisher registration requests (admin only)"""
    publishers = db.query(PublisherHouse).all()
    return publishers

# Route: Accept or decline a publisher registration (admin only)
@router.put("/publisher-requests/{publisher_id}/status")
def update_publisher_status(
    publisher_id: int,
    is_active: bool,
    is_verified: bool = None,
    db: Session = Depends(get_db)
):
    """Accept or decline a publisher registration (admin only)"""
    publisher = db.query(PublisherHouse).filter(PublisherHouse.id == publisher_id).first()
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher house not found")
    publisher.is_active = is_active
    if is_verified is not None:
        publisher.is_verified = is_verified
    db.commit()
    db.refresh(publisher)
    return {
        "id": publisher.id,
        "name": publisher.name,
        "email": publisher.email,
        "is_active": publisher.is_active,
        "is_verified": publisher.is_verified
    }

# Update Admin (Super Admin Only)
@router.put("/{admin_id}", response_model=AdminSchema)
async def update_admin(
    admin_id: int,
    admin_update: AdminUpdate,
    current_admin: Admin = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """Update admin (super admin only)"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
   
    if admin_update.phone_number is not None:
        admin.phone_number = admin_update.phone_number
    if admin_update.role is not None:
        admin.role = admin_update.role
        # Update permissions based on new role
        permissions = {
            "can_manage_users": admin_update.role in [AdminRole.user_admin, AdminRole.super_admin],
            "can_manage_publishers": admin_update.role in [AdminRole.publisher_admin, AdminRole.super_admin],
            "can_manage_content": admin_update.role in [AdminRole.content_admin, AdminRole.super_admin],
            "can_manage_system": admin_update.role == AdminRole.super_admin
        }
        admin.permissions = json.dumps(permissions)
        admin.can_manage_users = permissions["can_manage_users"]
        admin.can_manage_publishers = permissions["can_manage_publishers"]
        admin.can_manage_content = permissions["can_manage_content"]
        admin.can_manage_system = permissions["can_manage_system"]
    
    db.commit()
    db.refresh(admin)
    
    return admin

# Delete Admin (Super Admin Only)
@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_admin: Admin = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """Delete admin (super admin only)"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Prevent self-deletion
    if admin.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(admin)
    db.commit()
    
    return {"message": "Admin deleted successfully"} 