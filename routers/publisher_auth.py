from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import PublisherHouse
from schemas import (
    PublisherHouseCreate, PublisherHouse as PublisherHouseSchema, 
    PublisherHouseLogin, PublisherHouseToken, PublisherHouseUpdate
)
from security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_bearer_token
)
from jose import JWTError, jwt

from typing import Optional
import os
from datetime import datetime


router = APIRouter()

def get_current_publisher_house(publisher_house_id: int, db: Session = Depends(get_db)):
    """Get current publisher house by ID"""
    publisher_house = db.query(PublisherHouse).filter(PublisherHouse.id == publisher_house_id).first()
    if not publisher_house:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher house not found"
        )
    if not publisher_house.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher house is inactive"
        )
    return publisher_house

async def get_current_publisher_house_from_token(
    token: str = Depends(get_bearer_token), 
    db: Session = Depends(get_db)
) -> PublisherHouse:
    """Get current publisher house from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, "N93qNdu1uEX7oKM3ZQnHdV02TIuRt4umLG07eV4JhzI", algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None or not email.startswith("publisher_"):
            raise credentials_exception
        publisher_email = email.replace("publisher_", "")
    except JWTError:
        raise credentials_exception
    
    publisher_house = db.query(PublisherHouse).filter(PublisherHouse.email == publisher_email).first()
    if publisher_house is None:
        raise credentials_exception
    if not publisher_house.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher house is inactive"
        )
    return publisher_house

# Publisher House Registration
@router.post("/register", response_model=PublisherHouseSchema)
async def register_publisher_house(
    publisher_data: PublisherHouseCreate, 
    db: Session = Depends(get_db)
):
    """Register a new publisher house"""
    
    # Check if email already exists
    existing_publisher = db.query(PublisherHouse).filter(PublisherHouse.email == publisher_data.email).first()
    if existing_publisher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if name already exists
    existing_publisher = db.query(PublisherHouse).filter(PublisherHouse.name == publisher_data.name).first()
    if existing_publisher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher house name already exists"
        )
    
    # Create new publisher house
    hashed_password = get_password_hash(publisher_data.password)
    db_publisher = PublisherHouse(
        name=publisher_data.name,
        email=publisher_data.email,
        hashed_password=hashed_password,
        license_image=publisher_data.license_image,
        logo_image=publisher_data.logo_image
    )
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    

    
    return db_publisher



# Publisher House Login
@router.post("/login", response_model=PublisherHouseToken)
async def login_publisher_house(
    login_data: PublisherHouseLogin,
    db: Session = Depends(get_db)
):
    """Login for publisher house"""
    
    # Authenticate publisher house
    publisher_house = db.query(PublisherHouse).filter(PublisherHouse.email == login_data.email).first()
    if not publisher_house or not verify_password(login_data.password, publisher_house.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not publisher_house.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher house account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": f"publisher_{publisher_house.email}"}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "publisher_house_id": publisher_house.id,
        "name": publisher_house.name,
        "email": publisher_house.email
    }

# Get Publisher House Profile
@router.get("/me", response_model=PublisherHouseSchema)
async def get_publisher_house_profile(
    publisher_house_id: int,
    db: Session = Depends(get_db)
):
    """Get current publisher house profile"""
    publisher_house = get_current_publisher_house(publisher_house_id, db)
    return publisher_house

# Update Publisher House Profile
@router.put("/me", response_model=PublisherHouseSchema)
async def update_publisher_house_profile(
    publisher_data: PublisherHouseUpdate,
    publisher_house_id: int,
    db: Session = Depends(get_db)
):
    """Update publisher house profile"""
    publisher_house = get_current_publisher_house(publisher_house_id, db)
    
    # Update fields if provided
    if publisher_data.name is not None:
        # Check if name is already taken by another publisher
        existing = db.query(PublisherHouse).filter(
            PublisherHouse.name == publisher_data.name,
            PublisherHouse.id != publisher_house_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publisher house name already exists"
            )
        publisher_house.name = publisher_data.name
    
    if publisher_data.address is not None:
        publisher_house.address = publisher_data.address
    
    if publisher_data.contact_info is not None:
        publisher_house.contact_info = publisher_data.contact_info
    
    if publisher_data.logo_image is not None:
        publisher_house.logo_image = publisher_data.logo_image
    
    db.commit()
    db.refresh(publisher_house)
    return publisher_house

# Upload License Image
@router.post("/upload-license")
async def upload_license_image(
    file: UploadFile = File(...),
    publisher_house_id: int = None,
    db: Session = Depends(get_db)
):
    """Upload license image for publisher house"""
    if not publisher_house_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher house ID is required"
        )
    
    publisher_house = get_current_publisher_house(publisher_house_id, db)
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/images/publisher_licenses"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"license_{publisher_house_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update publisher house record
    publisher_house.license_image = file_path
    db.commit()
    
    return {
        "message": "License image uploaded successfully",
        "filename": filename,
        "file_path": file_path
    }

# Upload Logo Image
@router.post("/upload-logo")
async def upload_logo_image(
    file: UploadFile = File(...),
    publisher_house_id: int = None,
    db: Session = Depends(get_db)
):
    """Upload logo image for publisher house"""
    if not publisher_house_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher house ID is required"
        )
    
    publisher_house = get_current_publisher_house(publisher_house_id, db)
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/images/publisher_logos"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logo_{publisher_house_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update publisher house record
    publisher_house.logo_image = file_path
    db.commit()
    
    return {
        "message": "Logo image uploaded successfully",
        "filename": filename,
        "file_path": file_path
    }

# Test endpoint for publisher authentication
@router.get("/test-auth")
async def test_publisher_auth(publisher_house_id: int, db: Session = Depends(get_db)):
    """Test publisher house authentication"""
    publisher_house = get_current_publisher_house(publisher_house_id, db)
    return {
        "message": "Publisher authentication successful!",
        "publisher_house": {
            "id": publisher_house.id,
            "name": publisher_house.name,
            "email": publisher_house.email,
            "is_verified": publisher_house.is_verified
        }
    }

# Get all publisher houses (for admin)
@router.get("/all", response_model=list[PublisherHouseSchema])
async def get_all_publisher_houses(db: Session = Depends(get_db)):
    """Get all publisher houses (admin only)"""
    publisher_houses = db.query(PublisherHouse).all()
    return publisher_houses 