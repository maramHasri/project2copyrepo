from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Admin, AdminRole, AdminAction, PublisherHouse, Vacancy, VacancyAttachment, User, Book, Quote
from schemas import AdminCreate, Admin as AdminSchema, AdminUpdate, LoginRequest, PublisherHouse as PublisherHouseSchema, Vacancy as VacancySchema, User as UserSchema, Book as BookSchema, Quote as QuoteSchema
from security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ADMIN_CODE,
    SECRET_KEY,
    ALGORITHM,
    get_current_admin
)

from typing import Optional, List
from jose import JWTError, jwt

router = APIRouter()

# Helper functions for dependencies (moved to top)
async def get_bearer_token(authorization: Optional[str] = Header(None, include_in_schema=False)) -> str:
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


async def get_super_admin(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    """Check if admin is super admin"""
    if not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_admin

# Admin Registration 
@router.post("/register", response_model=AdminSchema)
async def register_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db)
):
    
    
    
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
    
    
   
    existing_admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    
    hashed_password = get_password_hash(admin_data.password)
    db_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        phone_number=admin_data.phone_number,
        hashed_password=hashed_password,
        role=AdminRole.super_admin, 
        is_super_admin=True         # Always true
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
        "is_super_admin": admin.is_super_admin
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

# Get all books (admin only)
@router.get("/books", response_model=List[BookSchema])
async def get_all_books(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all books (admin only)"""
    books = db.query(Book).offset(skip).limit(limit).all()
    
    # Populate publisher_house_name for each book
    for book in books:
        if book.publisher_house:
            book.publisher_house_name = book.publisher_house.name
        else:
            book.publisher_house_name = None
    
    return books

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


# Delete Book (Admin only)
@router.delete("/books/{book_id}")
async def delete_book(
    book_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete book (admin only)"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db.delete(book)
    db.commit()
    
    return {"message": "Book deleted successfully"}


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

# Admin Quote Management Endpoints
@router.get("/quotes", response_model=List[QuoteSchema])
async def admin_get_all_quotes(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint: Get all quotes with pagination"""
    quotes = db.query(Quote).offset(skip).limit(limit).all()
    return quotes

@router.delete("/quotes/{quote_id}")
async def admin_delete_quote(
    quote_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint: Delete any quote by ID"""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    db.delete(quote)
    db.commit()
    return {"message": "Quote deleted successfully by admin"} 