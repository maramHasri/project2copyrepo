from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from database import get_db
from models import Report, Book, User, Admin, Comment
from schemas import (
    Report as ReportSchema, ReportUpdate, BookBlockRequest, BookUnblockRequest, Book as BookSchema, 
    Comment as CommentSchema
)
from security import get_current_admin
from datetime import datetime

router = APIRouter()

@router.get("/reports", response_model=List[ReportSchema])
async def get_all_reports(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all reports with optional status filtering"""
    try:
        # Check if reports table exists by trying to query it
        try:
            query = db.query(Report)
            
            if status_filter:
                query = query.filter(Report.status == status_filter)
            
            reports = query.offset(skip).limit(limit).all()
            return reports
        except Exception:
            # Reports table doesn't exist, create it
            print("Creating reports table...")
            db.execute(text("""
                CREATE TABLE reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    admin_id INTEGER,
                    admin_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (book_id) REFERENCES books (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (admin_id) REFERENCES admins (id)
                )
            """))
            db.commit()
            print("Reports table created successfully")
            
            # Now query again (should return empty list)
            query = db.query(Report)
            if status_filter:
                query = query.filter(Report.status == status_filter)
            reports = query.offset(skip).limit(limit).all()
            return reports
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting reports: {str(e)}"
        )

@router.get("/reports/{report_id}", response_model=ReportSchema)
async def get_report(
    report_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific report by ID"""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report

@router.post("/books/{book_id}/block")
async def block_book(
    book_id: int,
    block_request: BookBlockRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Block a book - admin only"""
    try:
        # Always ensure the blocking columns exist first
        print("Ensuring book blocking columns exist...")
        try:
            # Check if columns exist by querying table schema
            result = db.execute(text("PRAGMA table_info(books)")).fetchall()
            columns = [row[1] for row in result]  # Get column names
            
            if 'is_blocked' not in columns:
                print("Adding missing book blocking columns...")
                db.execute(text("ALTER TABLE books ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
                db.execute(text("ALTER TABLE books ADD COLUMN blocked_reason TEXT"))
                db.execute(text("ALTER TABLE books ADD COLUMN blocked_at DATETIME"))
                db.commit()
                print("Book blocking columns added successfully")
            else:
                print("Book blocking columns already exist")
                
        except Exception as e:
            print(f"Error checking/adding columns: {e}")
            # Try to add columns anyway
            db.execute(text("ALTER TABLE books ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
            db.execute(text("ALTER TABLE books ADD COLUMN blocked_reason TEXT"))
            db.execute(text("ALTER TABLE books ADD COLUMN blocked_at DATETIME"))
            db.commit()
            print("Book blocking columns added successfully")
        
        # Check if book exists using raw SQL
        book_result = db.execute(text("SELECT id, title FROM books WHERE id = :book_id"), {"book_id": book_id}).fetchone()
        if not book_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Check if book is already blocked using raw SQL
        blocked_result = db.execute(text("SELECT is_blocked FROM books WHERE id = :book_id"), {"book_id": book_id}).fetchone()
        if blocked_result and blocked_result[0]:  # is_blocked is True
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book is already blocked"
            )
        
        # Block the book using raw SQL
        current_time = datetime.utcnow()
        db.execute(
            text("UPDATE books SET is_blocked = :is_blocked, blocked_reason = :blocked_reason, blocked_at = :blocked_at WHERE id = :book_id"),
            {
                "is_blocked": True, 
                "blocked_reason": block_request.blocked_reason, 
                "blocked_at": current_time, 
                "book_id": book_id
            }
        )
        db.commit()
        
        return {
            "message": "Book blocked successfully",
            "book_id": book_id,
            "book_title": book_result[1],  # title from the SELECT query
            "blocked_reason": block_request.blocked_reason,
            "blocked_at": current_time.isoformat(),
            "admin_notes": block_request.admin_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error blocking book: {str(e)}"
        )

@router.post("/books/{book_id}/unblock")
async def unblock_book(
    book_id: int,
    unblock_request: BookUnblockRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Unblock a book - admin only"""
    try:
        # First, ensure the blocking columns exist
        try:
            # Try to query the is_blocked column directly
            db.execute(text("SELECT is_blocked FROM books WHERE id = :book_id LIMIT 1"), {"book_id": book_id}).fetchone()
        except Exception:
            # Columns don't exist, add them using raw SQL
            print("Adding missing book blocking columns...")
            db.execute(text("ALTER TABLE books ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
            db.execute(text("ALTER TABLE books ADD COLUMN blocked_reason TEXT"))
            db.execute(text("ALTER TABLE books ADD COLUMN blocked_at DATETIME"))
            db.commit()
            print("Book blocking columns added successfully")
        
        # Now check if book exists using raw SQL
        book_result = db.execute(text("SELECT id, title FROM books WHERE id = :book_id"), {"book_id": book_id}).fetchone()
        if not book_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Check if book is already unblocked using raw SQL
        blocked_result = db.execute(text("SELECT is_blocked FROM books WHERE id = :book_id"), {"book_id": book_id}).fetchone()
        if not blocked_result or not blocked_result[0]:  # is_blocked is False or None
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book is not blocked"
            )
        
        # Unblock the book using raw SQL
        current_time = datetime.utcnow()
        db.execute(
            text("UPDATE books SET is_blocked = :is_blocked, blocked_reason = :blocked_reason, blocked_at = :blocked_at WHERE id = :book_id"),
            {
                "is_blocked": False, 
                "blocked_reason": None, 
                "blocked_at": None, 
                "book_id": book_id
            }
        )
        db.commit()
        
        return {
            "message": "Book unblocked successfully",
            "book_id": book_id,
            "book_title": book_result[1],  # title from the SELECT query
            "unblocked_at": current_time.isoformat(),
            "admin_notes": unblock_request.admin_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unblocking book: {str(e)}"
        )

@router.get("/books/blocked")
async def get_blocked_books(
    skip: int = 0,
    limit: int = 20,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all blocked books - admin only"""
    try:
        # First, ensure the blocking columns exist
        try:
            # Try to query the is_blocked column directly
            db.execute(text("SELECT is_blocked FROM books LIMIT 1")).fetchone()
        except Exception:
            # Columns don't exist, add them using raw SQL
            print("Adding missing book blocking columns...")
            db.execute(text("ALTER TABLE books ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
            db.execute(text("ALTER TABLE books ADD COLUMN blocked_reason TEXT"))
            db.execute(text("ALTER TABLE books ADD COLUMN blocked_at DATETIME"))
            db.commit()
            print("Book blocking columns added successfully")
        
        # Query blocked books using raw SQL
        blocked_books_result = db.execute(
            text("SELECT id, title, description, is_free, price, cover_image, book_file, author_name, author_id, publisher_house_id, is_blocked, blocked_reason, blocked_at, created_at FROM books WHERE is_blocked = 1 LIMIT :limit OFFSET :skip"),
            {"limit": limit, "skip": skip}
        ).fetchall()
        
        # Convert to list of dictionaries
        blocked_books = []
        for book in blocked_books_result:
            blocked_books.append({
                "id": book[0],
                "title": book[1],
                "description": book[2],
                "is_free": bool(book[3]),
                "price": book[4],
                "cover_image": book[5],
                "book_file": book[6],
                "author_name": book[7],
                "author_id": book[8],
                "publisher_house_id": book[9],
                "is_blocked": bool(book[10]),
                "blocked_reason": book[11],
                "blocked_at": book[12],
                "created_at": book[13]
            })
        
        return blocked_books
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting blocked books: {str(e)}"
        )

@router.get("/writers")
async def get_all_writers(
    skip: int = 0,
    limit: int = 20,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all writers - admin only"""
    try:
        # Query users with writer role
        writers = db.query(User).filter(User.role == "writer").offset(skip).limit(limit).all()
        
        return [
            {
                "id": writer.id,
                "username": writer.username,
                "email": writer.email,
                "phone_number": writer.phone_number,
                "role": writer.role,
                "bio": writer.bio,
                "writer_bio": writer.writer_bio,
                "published_books_count": writer.published_books_count,
                "is_featured_writer": writer.is_featured_writer,
                "skills": writer.skills,
                "social_links": writer.social_links,
                "profile_image": writer.profile_image,
                "is_active": writer.is_active,
                "is_verified": writer.is_verified,
                "created_at": writer.created_at
            }
            for writer in writers
        ]
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting writers: {str(e)}"
        )

@router.get("/writers/{writer_id}")
async def get_writer(
    writer_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific writer by ID - admin only"""
    try:
        writer = db.query(User).filter(
            User.id == writer_id,
            User.role == "writer"
        ).first()
        
        if not writer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Writer not found"
            )
        
        return {
            "id": writer.id,
            "username": writer.username,
            "email": writer.email,
            "phone_number": writer.phone_number,
            "role": writer.role,
            "bio": writer.bio,
            "writer_bio": writer.writer_bio,
            "published_books_count": writer.published_books_count,
            "is_featured_writer": writer.is_featured_writer,
            "skills": writer.skills,
            "social_links": writer.social_links,
            "profile_image": writer.profile_image,
            "is_active": writer.is_active,
            "is_verified": writer.is_verified,
            "created_at": writer.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting writer: {str(e)}"
        )

@router.get("/writers/stats")
async def get_writers_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get writers statistics - admin only"""
    try:
        # Total writers count
        total_writers = db.query(User).filter(User.role == "writer").count()
        
        # Active writers count
        active_writers = db.query(User).filter(
            User.role == "writer",
            User.is_active == True
        ).count()
        
        # Verified writers count
        verified_writers = db.query(User).filter(
            User.role == "writer",
            User.is_verified == True
        ).count()
        
        # Featured writers count
        featured_writers = db.query(User).filter(
            User.role == "writer",
            User.is_featured_writer == True
        ).count()
        
        # Writers with published books
        writers_with_books = db.query(User).filter(
            User.role == "writer",
            User.published_books_count > 0
        ).count()
        
        return {
            "total_writers": total_writers,
            "active_writers": active_writers,
            "verified_writers": verified_writers,
            "featured_writers": featured_writers,
            "writers_with_books": writers_with_books,
            "inactive_writers": total_writers - active_writers,
            "unverified_writers": total_writers - verified_writers
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting writers statistics: {str(e)}"
        )

@router.get("/comments", response_model=List[CommentSchema])
async def get_all_comments(
    skip: int = 0,
    limit: int = 20,
    book_id: Optional[int] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users' comments with optional book filtering - admin only"""
    try:
        query = db.query(Comment)
        
        # Apply book filter if provided
        if book_id:
            query = query.filter(Comment.book_id == book_id)
        
        # Order by creation date (newest first)
        query = query.order_by(Comment.created_at.desc())
        
        # Apply pagination
        comments = query.offset(skip).limit(limit).all()
        
        return comments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting comments: {str(e)}"
        )

@router.get("/comments/{comment_id}", response_model=CommentSchema)
async def get_comment(
    comment_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific comment by ID - admin only"""
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting comment: {str(e)}"
        )

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a comment - admin only"""
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Store comment info for response
        comment_info = {
            "id": comment.id,
            "text": comment.text,
            "user_name": comment.user_name,
            "book_id": comment.book_id,
            "created_at": comment.created_at
        }
        
        # Delete the comment
        db.delete(comment)
        db.commit()
        
        return {
            "message": "Comment deleted successfully",
            "deleted_comment": comment_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting comment: {str(e)}"
        )
