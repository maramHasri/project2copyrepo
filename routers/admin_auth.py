from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Admin, AdminRole, AdminAction, PublisherHouse, Vacancy, VacancyAttachment, User
from schemas import AdminCreate, Admin as AdminSchema, AdminUpdate, LoginRequest, PublisherHouse as PublisherHouseSchema, Vacancy as VacancySchema, User as UserSchema
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
    
    # Verify admin code FIRST - before any other operations
    if not admin_data.admin_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin code is required"
        )
    
    if admin_data.admin_code != ADMIN_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin code"
        )
    
    # Check if username already exists (AFTER admin code validation)
    existing_admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists (AFTER admin code validation)
    existing_admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # All admins have full permissions (super admin)
    permissions = {
        "can_manage_users": True,
        "can_manage_publishers": True,
        "can_manage_content": True,
        "can_manage_system": True
    }
    
    # Create new admin (all admins are super admins)
    hashed_password = get_password_hash(admin_data.password)
    db_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        phone_number=admin_data.phone_number,
        hashed_password=hashed_password,
        role=AdminRole.super_admin,  # All admins are super admins
        is_super_admin=True,         # Always true
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

# Get all publishers (admin only)
@router.get("/publishers", response_model=List[PublisherHouseSchema])
async def get_all_publishers(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all publishers (admin only)"""
    publishers = db.query(PublisherHouse).offset(skip).limit(limit).all()
    return publishers

# Get specific publisher by ID (admin only)
@router.get("/publishers/{publisher_id}", response_model=PublisherHouseSchema)
async def get_publisher_by_id(
    publisher_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific publisher by ID (admin only)"""
    publisher = db.query(PublisherHouse).filter(PublisherHouse.id == publisher_id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    return publisher

# Update Admin (Any admin can update other admins)
@router.put("/{admin_id}", response_model=AdminSchema)
async def update_admin(
    admin_id: int,
    admin_update: AdminUpdate,
    current_admin: Admin = Depends(get_current_admin),  # Any admin can update other admins
    db: Session = Depends(get_db)
):
    """Update admin (any admin can update other admins)"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Update fields (no role updates since all admins are super admins)
    if admin_update.phone_number is not None:
        admin.phone_number = admin_update.phone_number
    
    # All admins maintain full permissions
    permissions = {
        "can_manage_users": True,
        "can_manage_publishers": True,
        "can_manage_content": True,
        "can_manage_system": True
    }
    admin.permissions = json.dumps(permissions)
    admin.can_manage_users = True
    admin.can_manage_publishers = True
    admin.can_manage_content = True
    admin.can_manage_system = True
    
    db.commit()
    db.refresh(admin)
    
    return admin

# Delete Admin (Any admin can delete other admins)
@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_admin: Admin = Depends(get_current_admin),  # Any admin can delete other admins
    db: Session = Depends(get_db)
):
    """Delete admin (any admin can delete other admins)"""
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

# Admin Vacancy Management Endpoints
@router.get("/vacancies", response_model=List[VacancySchema])
async def admin_get_all_vacancies(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Admin endpoint: Get all vacancies"""
    vacancies = db.query(Vacancy).offset(skip).limit(limit).all()
    return vacancies

@router.delete("/vacancies/{vacancy_id}")
async def admin_delete_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Admin endpoint: Delete any vacancy"""
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    db.delete(vacancy)
    db.commit()
    return {"message": "Vacancy deleted successfully by admin"}

@router.put("/vacancies/{vacancy_id}/toggle-status")
async def admin_toggle_vacancy_status(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Admin endpoint: Toggle vacancy active status"""
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    vacancy.is_active = not vacancy.is_active
    db.commit()
    db.refresh(vacancy)
    status_text = "activated" if vacancy.is_active else "deactivated"
    return {"message": f"Vacancy {status_text} successfully"} 

# Get All Users (Readers, Writers, Publishers)
@router.get("/users", response_model=List[UserSchema])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,  # Filter by role: "reader", "writer", or None for all
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users (readers and writers) with optional role filtering"""
    query = db.query(User)
    
    # Filter by role if specified
    if role:
        if role not in ["reader", "writer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'reader' or 'writer'"
            )
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    return users

# Get All Publishers
@router.get("/publishers", response_model=List[PublisherHouseSchema])
async def get_all_publishers(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all publishers"""
    publishers = db.query(PublisherHouse).offset(skip).limit(limit).all()
    return publishers

# Get User Statistics
@router.get("/users/stats")
async def get_user_statistics(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user statistics for admin dashboard"""
    total_users = db.query(User).count()
    total_readers = db.query(User).filter(User.role == "reader").count()
    total_writers = db.query(User).filter(User.role == "writer").count()
    total_publishers = db.query(PublisherHouse).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    return {
        "total_users": total_users,
        "total_readers": total_readers,
        "total_writers": total_writers,
        "total_publishers": total_publishers,
        "active_users": active_users,
        "verified_users": verified_users,
        "verification_rate": round((verified_users / total_users * 100), 2) if total_users > 0 else 0
    } 