from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
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

# Alternative PATCH endpoint for more reliable partial updates
@router.patch("/me", response_model=UserSchema)
async def patch_user_profile(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Patch user profile with only the provided fields - More reliable partial update"""
    # Get the raw JSON body
    try:
        body = await request.json()
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    # Only update fields that were explicitly provided
    updated = False
    for field, value in body.items():
        if field in ['bio', 'social_links']:  # Explicitly list allowed fields
            if hasattr(current_user, field):
                setattr(current_user, field, value)
                updated = True
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid field '{field}' for user update"
                )
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

# # Simple skills update endpoint
# @router.put("/me/skills", response_model=UserSchema)
# async def update_user_skills(
#     skills_update: UserSkillsUpdate,
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Update user skills"""
#     current_user.skills = json.dumps(skills_update.skills)
#     db.commit()
#     db.refresh(current_user)
#     return current_user

# # Get skills for dropdown menu
# @router.get("/skills")
# async def get_skills_dropdown():
#     """Get all available skills for dropdown menu"""
#     return {
#         "Editing & Proofreading": [
#             "تحرير نصوص",
#             "مراجعة لغوية",
#             "تدقيق إملائي ونحوي",
#             "تحرير محتوى رقمي",
#             "مراجعة علمية",
#             "كتابة المحتوى"
#         ],
#         "Design & Layout": [
#             "تصميم غلاف",
#             "تصميم داخلي للكتاب",
#             "تصميم جرافيك",
#             "رسم توضيحي",
#             "Photoshop",
#             "Illustrator",
#             "InDesign",
#             "تصميم واجهات المستخدم"
#         ],
#         "Printing & Production": [
#             "إدارة الإنتاج",
#             "تشغيل الطابعة",
#             "ضبط الألوان",
#             "مراقبة الجودة"
#         ],
#         "Marketing & Sales": [
#             "التسويق الرقمي",
#             "إدارة منصات التواصل الاجتماعي",
#             "البيع والتوزيع",
#             "إدارة الحملات الإعلانية",
#             "تحسين محركات البحث"
#         ],
#         "Digital Publishing": [
#             "تطوير كتب إلكترونية",
#             "إدارة منصات رقمية",
#             "تحرير ملفات PDF",
#             "تنسيق EPUB"
#         ],
#         "Publishing House Management": [
#             "إدارة المشروعات",
#             "إدارة الموارد البشرية",
#             "العلاقات العامة",
#             "التمويل والمحاسبة"
#         ]
#     }

# # POST endpoint for user interests
# @router.post("/me/interests", response_model=List[BookSchema])
# async def post_user_interests(
#     interests: UserInterests,
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Set user interests and return books in those categories"""

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