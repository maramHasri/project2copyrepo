from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Category, User
from schemas import CategoryCreate, Category as CategorySchema
from security import get_current_active_user
from routers.admin_auth import get_current_admin

router = APIRouter()

@router.post("/", response_model=CategorySchema)
async def create_category(
    category: CategoryCreate,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Only admins can create categories. Use the Authorize button above to provide admin token."""
    # Check if category name already exists
    db_category = db.query(Category).filter(Category.name == category.name).first()
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists"
        )
    
    # Create new category
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategorySchema])
async def get_categories(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update category. Admin authentication required. """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if new name conflicts with existing category
    existing_category = db.query(Category).filter(
        Category.name == category.name,
        Category.id != category_id
    ).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete category. Admin authentication required. Use the Authorize button above."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"} 