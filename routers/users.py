from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Category, Publisher, Book, UserRole
from schemas import UserUpdate, User as UserSchema, UserInterests, PublisherCreate, FileUploadResponse
from security import get_current_active_user, check_user_role
from file_upload import save_profile_image, delete_file

router = APIRouter()

@router.put("/me/with-image", response_model=UserSchema)
async def update_user_with_image(
    bio: Optional[str] = Form(None),
    social_links: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
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

@router.post("/me/upload-profile-image", response_model=FileUploadResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Delete old profile image if exists
    if current_user.profile_image:
        delete_file(current_user.profile_image)
    
    # Save new profile image
    image_url = save_profile_image(file, current_user.id)
    current_user.profile_image = image_url
    
    db.commit()
    db.refresh(current_user)
    
    return FileUploadResponse(
        filename=file.filename,
        file_url=image_url,
        message="Profile image uploaded successfully"
    )

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

@router.post("/upgrade-to-publisher")
async def upgrade_to_publisher(
    publisher_data: PublisherCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user is already a publisher
    if current_user.role == UserRole.publisher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a publisher"
        )
    
    # Check if user has at least 3 books
    if len(current_user.books) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must have at least 3 books to become a publisher"
        )
    
    # Update user role to publisher
    current_user.role = UserRole.publisher
    
    # Check if Publisher record already exists
    existing_publisher = db.query(Publisher).filter(Publisher.user_id == current_user.id).first()
    if existing_publisher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher record already exists for this user"
        )
    
    # Create new Publisher record
    new_publisher = Publisher(
        user_id=current_user.id,
        name=publisher_data.name,
        logo=publisher_data.logo,
        foundation_date=publisher_data.foundation_date,
        address=publisher_data.address,
        contact_info=publisher_data.contact_info
    )
    
    db.add(new_publisher)
    db.commit()
    db.refresh(current_user)
    
    return {"message": "User upgraded to publisher"}

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get publisher information
    publisher = db.query(Publisher).filter(Publisher.user_id == current_user.id).first()
    
    # Create response with publisher info
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "profile_image": current_user.profile_image,
        "bio": current_user.bio,
        "social_links": current_user.social_links,
        "publisher_id": publisher.id if publisher else None,
        "has_publisher_record": publisher is not None
    }
    
    return user_data

@router.get("/", response_model=List[UserSchema])
async def get_all_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/readers", response_model=List[UserSchema])
async def get_readers(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    readers = db.query(User).filter(User.role == UserRole.reader).offset(skip).limit(limit).all()
    return readers

@router.get("/publishers", response_model=List[UserSchema])
async def get_publishers(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    publishers = db.query(User).filter(User.role == UserRole.publisher).offset(skip).limit(limit).all()
    return publishers

@router.get("/writers", response_model=List[UserSchema])
async def get_writers(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    writers = db.query(User).filter(User.role == UserRole.writer).offset(skip).limit(limit).all()
    return writers

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