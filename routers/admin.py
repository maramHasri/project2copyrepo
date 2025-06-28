from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, Book, Category, Publisher, UserRole
from schemas import User as UserSchema, Book as BookSchema, Category as CategorySchema, CategoryCreate, Publisher as PublisherSchema, AdminStats, UserManagement
from security import check_admin_role, get_current_active_user

router = APIRouter()

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    # Get counts
    total_users = db.query(User).count()
    total_books = db.query(Book).count()
    total_categories = db.query(Category).count()
    total_publishers = db.query(Publisher).count()
    
    # Get users by role
    users_by_role = {}
    for role in [UserRole.reader, UserRole.writer, UserRole.publisher, UserRole.admin]:
        users_by_role[role.value] = db.query(User).filter(User.role == role).count()
    
    # Get recent books (last 10)
    recent_books = db.query(Book).order_by(Book.created_at.desc()).limit(10).all()
    
    # Get recent users (last 10)
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    
    return AdminStats(
        total_users=total_users,
        total_books=total_books,
        total_categories=total_categories,
        total_publishers=total_publishers,
        users_by_role=users_by_role,
        recent_books=recent_books,
        recent_users=recent_users
    )

@router.get("/users", response_model=List[UserSchema])
async def get_all_users_admin(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.offset(skip).limit(limit).all()
    return users

@router.put("/users/{user_id}/manage")
async def manage_user(
    user_id: int,
    management: UserManagement,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    # Get user to manage
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from managing themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot manage your own account"
        )
    
    # Perform action
    if management.action == "activate":
        user.is_active = True
        message = "User activated"
    elif management.action == "deactivate":
        user.is_active = False
        message = "User deactivated"
    elif management.action == "change_role":
        if not management.new_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New role is required for change_role action"
            )
        try:
            new_role = UserRole(management.new_role)
            user.role = new_role
            message = f"User role changed to {new_role.value}"
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role"
            )
    elif management.action == "delete":
        db.delete(user)
        message = "User deleted"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )
    
    db.commit()
    return {"message": message}

@router.get("/books", response_model=List[BookSchema])
async def get_all_books_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    books = db.query(Book).offset(skip).limit(limit).all()
    return books

@router.delete("/books/{book_id}")
async def delete_book_admin(
    book_id: int,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}

@router.get("/categories", response_model=List[CategorySchema])
async def get_all_categories_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.delete("/categories/{category_id}")
async def delete_category_admin(
    category_id: int,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category is in use
    if category.books or category.interested_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category that is in use"
        )
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

@router.get("/publishers", response_model=List[PublisherSchema])
async def get_all_publishers_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    publishers = db.query(Publisher).offset(skip).limit(limit).all()
    return publishers

@router.delete("/publishers/{publisher_id}")
async def delete_publisher_admin(
    publisher_id: int,
    current_user: User = Depends(check_admin_role()),
    db: Session = Depends(get_db)
):
    publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    
    # Check if publisher has books
    if publisher.books:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete publisher that has books"
        )   
    
    db.delete(publisher)
    db.commit()
    return {"message": "Publisher deleted successfully"}

@router.post("/categories/", response_model=CategorySchema)
async def create_category_admin(
    category: CategoryCreate,
    _: User = Depends(check_admin_role),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to create a new category."""
    db_category = db.query(Category).filter(Category.name == category.name).first()
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists"
        )
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category 