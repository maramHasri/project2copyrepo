from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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
# Remove the JSON-based registration endpoint for /register
# @router.post("/register", response_model=PublisherHouseSchema)
# async def register_publisher_house(
#     publisher_data: PublisherHouseCreate, 
#     db: Session = Depends(get_db)
# ):
#     """Register a new publisher house"""
    
#     # Check if email already exists
#     existing_publisher = db.query(PublisherHouse).filter(PublisherHouse.email == publisher_data.email).first()
#     if existing_publisher:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     # Check if name already exists
#     existing_publisher = db.query(PublisherHouse).filter(PublisherHouse.name == publisher_data.name).first()
#     if existing_publisher:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Publisher house name already exists"
#         )
    
#     # Create new publisher house
#     hashed_password = get_password_hash(publisher_data.password)
#     db_publisher = PublisherHouse(
#         name=publisher_data.name,
#         email=publisher_data.email,
#         hashed_password=hashed_password,
#         license_image=publisher_data.license_image,
#         logo_image=publisher_data.logo_image
#     )
#     db.add(db_publisher)
#     db.commit()
#     db.refresh(db_publisher)
    

    
#     return db_publisher



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
    
    return PublisherHouseToken(
        access_token=access_token,
        token_type="bearer",
        publisher_house_id=publisher_house.id,
        name=publisher_house.name,
        email=publisher_house.email
    )

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

# Rename /submit-form-logo to /register
@router.post("/register")
async def register_publisher_house_form(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    license_image: UploadFile = File(...),
    logo_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Register Publisher House"""
    # 1. Check if email or name already exists
    if db.query(PublisherHouse).filter(PublisherHouse.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(PublisherHouse).filter(PublisherHouse.name == name).first():
        raise HTTPException(status_code=400, detail="Publisher house name already exists")
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # 2. Save uploaded files
    uploads_dir = "uploads/images/publisher_licenses"
    os.makedirs(uploads_dir, exist_ok=True)
    license_filename = f"license_{email}_{license_image.filename}"
    license_path = os.path.join(uploads_dir, license_filename)
    with open(license_path, "wb") as f:
        f.write(await license_image.read())
    await license_image.seek(0)

    uploads_dir_logo = "uploads/images/publisher_logos"
    os.makedirs(uploads_dir_logo, exist_ok=True)
    logo_filename = f"logo_{email}_{logo_image.filename}"
    logo_path = os.path.join(uploads_dir_logo, logo_filename)
    with open(logo_path, "wb") as f:
        f.write(await logo_image.read())
    await logo_image.seek(0)

    # 3. Hash password
    hashed_password = get_password_hash(password)

    # 4. Create and save PublisherHouse
    db_publisher = PublisherHouse(
        name=name,
        email=email,
        hashed_password=hashed_password,
        license_image=license_path,
        logo_image=logo_path,
        is_active=False,  # Pending approval
        is_verified=False  # Pending approval
    )
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)

    # 5. Return created user (excluding password)
    return {
        "id": db_publisher.id,
        "name": db_publisher.name,
        "email": db_publisher.email,
        "license_image": db_publisher.license_image,
        "logo_image": db_publisher.logo_image
    } 

@router.get("/publisher-requests")
def get_all_publisher_requests(db: Session = Depends(get_db)):
    publishers = db.query(PublisherHouse).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "date_of_registration": p.created_at,
            "state": "active" if p.is_active else "nonactive"
        }
        for p in publishers
    ] 