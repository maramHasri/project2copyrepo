from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from models import Comment, User, Book
from schemas import CommentCreate, Comment as CommentSchema
from security import get_current_active_user

router = APIRouter()

@router.post("/", response_model=CommentSchema)
async def create_comment(
    comment: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a comment for a book - any authenticated user can comment on any book"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == comment.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Create comment
    db_comment = Comment(
        text=comment.text,
        book_id=comment.book_id,
        user_id=current_user.id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    # Load the user relationship to populate user info
    db_comment = db.query(Comment).options(joinedload(Comment.user)).filter(Comment.id == db_comment.id).first()
    
    return db_comment

# @router.get("/", response_model=List[CommentSchema])
# async def get_comments(
#     book_id: Optional[int] = Query(None, description="Filter comments by book ID"),
#     user_id: Optional[int] = Query(None, description="Filter comments by user ID"),
#     skip: int = Query(0, ge=0, description="Number of comments to skip"),
#     limit: int = Query(10, ge=1, le=100, description="Number of comments to return"),
#     db: Session = Depends(get_db)
# ):
#     """Get comments with optional filtering by book_id or user_id"""
#     query = db.query(Comment).options(joinedload(Comment.user))
    
#     if book_id:
#         query = query.filter(Comment.book_id == book_id)
#     if user_id:
#         query = query.filter(Comment.user_id == user_id)
    
#     comments = query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
#     return comments

@router.get("/book/{book_id}", response_model=List[CommentSchema])
async def get_book_comments(
    book_id: int,
    skip: int = Query(0, ge=0, description="Number of comments to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of comments to return"),
    db: Session = Depends(get_db)
):
    """Get all comments for a specific book"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    comments = db.query(Comment).options(joinedload(Comment.user)).filter(
        Comment.book_id == book_id
    ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    return comments

# @router.get("/user/{user_id}", response_model=List[CommentSchema])
# async def get_user_comments(
#     user_id: int,
#     skip: int = Query(0, ge=0, description="Number of comments to skip"),
#     limit: int = Query(10, ge=1, le=100, description="Number of comments to return"),
#     db: Session = Depends(get_db)
# ):
#     """Get all comments by a specific user"""
#     # Check if user exists
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     comments = db.query(Comment).options(joinedload(Comment.user)).filter(
#         Comment.user_id == user_id
#     ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
#     return comments

# @router.get("/my-comments", response_model=List[CommentSchema])
# async def get_my_comments(
#     current_user: User = Depends(get_current_active_user),
#     skip: int = Query(0, ge=0, description="Number of comments to skip"),
#     limit: int = Query(10, ge=1, le=100, description="Number of comments to return"),
#     db: Session = Depends(get_db)
# ):
#     """Get all comments by the current user"""
#     comments = db.query(Comment).options(joinedload(Comment.user)).filter(
#         Comment.user_id == current_user.id
#     ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
#     return comments

# @router.get("/{comment_id}", response_model=CommentSchema)
# async def get_comment(
#     comment_id: int,
#     db: Session = Depends(get_db)
# ):
#     """Get a specific comment by ID"""
#     comment = db.query(Comment).options(joinedload(Comment.user)).filter(Comment.id == comment_id).first()
#     if not comment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Comment not found"
#         )
#     return comment

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a comment - only the author can delete their own comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}
