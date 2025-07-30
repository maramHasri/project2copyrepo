from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Category, PublisherHouse, Book, UserRole
from schemas import UserUpdate, User as UserSchema, UserInterests, PublisherHouseCreate, FileUploadResponse
from security import get_current_active_user, check_user_role
from file_upload import save_profile_image, delete_file

router = APIRouter()

@router.put("/me", response_model=UserSchema)
async def update_user_profile(
    bio: Optional[str] = Form(None),
    social_links: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile with text fields and optional image"""
    # Update text fields
    if bio is not None:
        current_user.bio = bio
    if social_links is not None:
        current_user.social_links = social_links
    
    # Handle profile image upload
    if profile_image:
        # Delete old profile image if exists
        if current_user.profile_image:
            delete_file(current_user.profile_image)
        
        # Save new profile image
        image_url = save_profile_image(profile_image, current_user.id)
        current_user.profile_image = image_url
    
    db.commit()
    db.refresh(current_user)
    return current_user

# Removed redundant upload route - now handled in PUT /me

@router.put("/me/interests", response_model=List[dict])
async def update_user_interests_and_get_books(
    interests: UserInterests,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Clear existing interests
    current_user.interests = []
    # Add new interests
    categories = db.query(Category).filter(Category.id.in_(interests.category_ids)).all()
    current_user.interests = categories
    db.commit()
    db.refresh(current_user)
    # Return books in those categories
    books = db.query(Book).join(Book.categories).filter(Category.id.in_(interests.category_ids)).all()
    return [book.__dict__ for book in books]



@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Return user information (publishers now have separate system)
    return current_user



@router.get("/writers/{writer_id}", response_model=UserSchema)
async def get_writer(
    writer_id: int,
    db: Session = Depends(get_db)
):
    writer = db.query(User).filter(User.id == writer_id, User.role == UserRole.writer).first()
    if not writer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writer not found"
        )
    return writer 