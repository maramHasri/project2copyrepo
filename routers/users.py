from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from models import User, Category, PublisherHouse, Book, UserRole, Vacancy, CVApplication
from schemas import UserUpdate, User as UserSchema, UserInterests, PublisherHouseCreate, FileUploadResponse, Book as BookSchema, UserSkillsUpdate, PublisherHouse as PublisherHouseSchema, Vacancy as VacancySchema, CVApplication as CVApplicationSchema, CVApplicationCreate, WriterResponse
from security import get_current_active_user, check_user_role
from file_upload import save_cv_file
import json

router = APIRouter()

@router.put("/me", response_model=UserSchema)
async def update_user_profile(
    bio: Optional[str] = Form(None),
    social_links: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile with text fields only - Partial update supported"""
    # Only update fields that were explicitly provided (not None and not default values)
    updated = False
    
    if bio is not None and bio != "string":
        current_user.bio = bio
        updated = True
    
    if social_links is not None and social_links != "string":
        current_user.social_links = social_links
        updated = True
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    
    db.commit()
    db.refresh(current_user)
    return current_user


# Get all available categories (all interests)
@router.get("/interests", response_model=List[dict])
async def get_all_interests(db: Session = Depends(get_db)):
    """Get all available categories that users can be interested in"""
    categories = db.query(Category).all()
    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description
        }
        for category in categories
    ]

# Set user interests
@router.post("/me/interests", response_model=dict)
async def set_user_interests(
    interests: UserInterests,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Set user interests by category IDs"""
    # Clear existing interests
    current_user.interests = []
    
    # Add new interests
    for category_id in interests.category_ids:
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            current_user.interests.append(category)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "User interests updated successfully",
        "interests": [
            {
                "id": category.id,
                "name": category.name,
                "description": category.description
            }
            for category in current_user.interests
        ]
    }

# Get current user's interests
@router.get("/me/interests", response_model=List[dict])
async def get_user_interests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's interests (categories)"""
    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description
        }
        for category in current_user.interests
    ]

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Return user information (publishers now have separate system)
    return current_user

@router.get("/writers", response_model=List[WriterResponse])
async def get_all_writers(
    skip: int = 0,
    limit: int = 20,
    featured_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all writers with optional filtering"""
    query = db.query(User).filter(User.role == UserRole.writer, User.is_active == True)
    
    if featured_only:
        query = query.filter(User.is_featured_writer == True)
    
    writers = query.offset(skip).limit(limit).all()
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

@router.get("/publisher-houses", response_model=List[PublisherHouseSchema])
async def get_all_publisher_houses(
    db: Session = Depends(get_db)
):
    """Get all publisher houses"""
    publisher_houses = db.query(PublisherHouse).filter(PublisherHouse.is_active == True).all()
    return publisher_houses

@router.get("/publisher-houses/{publisher_id}/books", response_model=List[BookSchema])
async def get_publisher_books(
    publisher_id: int,
    db: Session = Depends(get_db)
):
    """Get all books of a specific publisher house by ID"""
    # First check if publisher house exists
    publisher_house = db.query(PublisherHouse).filter(
        PublisherHouse.id == publisher_id,
        PublisherHouse.is_active == True
    ).first()
    
    if not publisher_house:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher house not found"
        )
    
    # Get all books for this publisher house with publisher relationship loaded
    books = db.query(Book).filter(Book.publisher_house_id == publisher_id, Book.is_blocked == False).all()
    
    # Populate publisher_house_name for each book
    for book in books:
        if book.publisher_house:
            book.publisher_house_name = book.publisher_house.name
        else:
            book.publisher_house_name = None
    
    return books

@router.get("/vacancies", response_model=List[VacancySchema])
async def get_all_vacancies(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all active vacancies"""
    vacancies = db.query(Vacancy).filter(Vacancy.is_active == True).offset(skip).limit(limit).all()
    return vacancies

@router.get("/vacancies/{vacancy_id}", response_model=VacancySchema)
async def get_vacancy_by_id(
    vacancy_id: int,
    db: Session = Depends(get_db)
):
    """Get vacancy details by ID"""
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    return vacancy

@router.post("/vacancies/{vacancy_id}/apply", response_model=CVApplicationSchema)
async def apply_to_vacancy(
    vacancy_id: int,
    cv_file: UploadFile = File(..., description="CV file (PDF, DOC, DOCX)"),
    cover_letter: Optional[str] = Form(None, description="Optional cover letter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Apply to a vacancy by uploading CV and optional cover letter"""
    # Check if vacancy exists and is active
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.is_active == True).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found or not active"
        )
    
    # Check if user already applied to this vacancy
    existing_application = db.query(CVApplication).filter(
        CVApplication.user_id == current_user.id,
        CVApplication.vacancy_id == vacancy_id
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this vacancy"
        )
    
    # Save CV file
    cv_file_path = save_cv_file(cv_file, current_user.id, vacancy_id)
    
    # Create CV application
    cv_application = CVApplication(
        user_id=current_user.id,
        vacancy_id=vacancy_id,
        cv_file_path=cv_file_path,
        cover_letter=cover_letter,
        status="pending"
    )
    
    db.add(cv_application)
    db.commit()
    db.refresh(cv_application)
    
    # Load relationships for response
    cv_application = db.query(CVApplication).options(
        joinedload(CVApplication.user),
        joinedload(CVApplication.vacancy)
    ).filter(CVApplication.id == cv_application.id).first()
    
    return cv_application

@router.get("/my-applications", response_model=List[CVApplicationSchema])
async def get_my_applications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all CV applications submitted by the current user"""
    applications = db.query(CVApplication).options(
        joinedload(CVApplication.vacancy)
    ).filter(CVApplication.user_id == current_user.id).all()
    
    return applications
