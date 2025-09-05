from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Report, Book, User
from schemas import ReportCreate, Report as ReportSchema
from security import get_current_active_user

router = APIRouter()

@router.post("/", response_model=ReportSchema)
async def create_report(
    report: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a report for a book"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == report.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check if user already reported this book
    existing_report = db.query(Report).filter(
        Report.book_id == report.book_id,
        Report.user_id == current_user.id
    ).first()
    
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reported this book"
        )
    
    # Create new report
    db_report = Report(
        book_id=report.book_id,
        user_id=current_user.id,
        reason=report.reason,
        description=report.description
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report