from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Category, PublisherHouse, Book, UserRole
from schemas import UserUpdate, User as UserSchema, UserInterests, PublisherHouseCreate, FileUploadResponse, Book as BookSchema, UserSkillsUpdate
from security import get_current_active_user, check_user_role
import json

router = APIRouter()

@router.put("/me", response_model=UserSchema)
async def update_user_profile(
    bio: Optional[str] = Form(None),
    social_links: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile with text fields only"""
    # Update text fields
    if bio is not None:
        current_user.bio = bio
    if social_links is not None:
        current_user.social_links = social_links
    
    db.commit()
    db.refresh(current_user)
    return current_user

# Simple skills update endpoint
@router.put("/me/skills", response_model=UserSchema)
async def update_user_skills(
    skills_update: UserSkillsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user skills"""
    current_user.skills = json.dumps(skills_update.skills)
    db.commit()
    db.refresh(current_user)
    return current_user

# Get skills for dropdown menu
@router.get("/skills")
async def get_skills_dropdown():
    """Get all available skills for dropdown menu"""
    return {
        "Editing & Proofreading": [
            "تحرير نصوص",
            "مراجعة لغوية",
            "تدقيق إملائي ونحوي",
            "تحرير محتوى رقمي",
            "مراجعة علمية",
            "كتابة المحتوى"
        ],
        "Design & Layout": [
            "تصميم غلاف",
            "تصميم داخلي للكتاب",
            "تصميم جرافيك",
            "رسم توضيحي",
            "Photoshop",
            "Illustrator",
            "InDesign",
            "تصميم واجهات المستخدم"
        ],
        "Printing & Production": [
            "إدارة الإنتاج",
            "تشغيل الطابعة",
            "ضبط الألوان",
            "مراقبة الجودة"
        ],
        "Marketing & Sales": [
            "التسويق الرقمي",
            "إدارة منصات التواصل الاجتماعي",
            "البيع والتوزيع",
            "إدارة الحملات الإعلانية",
            "تحسين محركات البحث"
        ],
        "Digital Publishing": [
            "تطوير كتب إلكترونية",
            "إدارة منصات رقمية",
            "تحرير ملفات PDF",
            "تنسيق EPUB"
        ],
        "Publishing House Management": [
            "إدارة المشروعات",
            "إدارة الموارد البشرية",
            "العلاقات العامة",
            "التمويل والمحاسبة"
        ]
    }

# # POST endpoint for user interests
# @router.post("/me/interests", response_model=List[BookSchema])
# async def post_user_interests(
#     interests: UserInterests,
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Set user interests and return books in those categories"""
#     # Clear existing interests
#     current_user.interests = []
    
#     # Add new interests
#     categories = db.query(Category).filter(Category.id.in_(interests.category_ids)).all()
#     current_user.interests = categories
    
#     db.commit()
#     db.refresh(current_user)
    
#     # Return books in those categories
#     books = db.query(Book).join(Book.categories).filter(Category.id.in_(interests.category_ids)).all()
#     return books

# GET endpoint for user interests
@router.get("/me/interests")
async def get_user_interests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's interests"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "interests": [
            {
                "id": category.id,
                "name": category.name,
                "description": category.description
            }
            for category in current_user.interests
        ]
    }

# GET endpoint for all available categories
@router.get("/categories")
async def get_all_categories(
    db: Session = Depends(get_db)
):
    """Get all available categories for user interests"""
    categories = db.query(Category).all()
    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description
        }
        for category in categories
    ]

# PUT endpoint for updating user interests (kept for backward compatibility)
@router.put("/me/interests", response_model=List[BookSchema])
async def update_user_interests_and_get_books(
    interests: UserInterests,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """get books for user depend on his interists"""
    # Clear existing interests
    current_user.interests = []
    
    # Add new interests
    categories = db.query(Category).filter(Category.id.in_(interests.category_ids)).all()
    current_user.interests = categories
    
    db.commit()
    db.refresh(current_user)
    
    # Return books in those categories
    books = db.query(Book).join(Book.categories).filter(Category.id.in_(interests.category_ids)).all()
    return books

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