from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Quote, User, Book
from schemas import QuoteCreate, Quote as QuoteSchema
from security import get_current_active_user

router = APIRouter()

@router.post("/", response_model=QuoteSchema)
async def create_quote(
    quote: QuoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a quote - any authenticated user can create quotes from any book"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == quote.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Any authenticated user can create quotes
    db_quote = Quote(
        **quote.dict(),
        author_id=current_user.id
    )
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

@router.get("/", response_model=List[QuoteSchema])
async def get_quotes(
    skip: int = 0,
    limit: int = 10,
    book_id: int = None,
    author_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(Quote)
    
    if book_id:
        query = query.filter(Quote.book_id == book_id)
    if author_id:
        query = query.filter(Quote.author_id == author_id)
    
    quotes = query.order_by(Quote.number_of_likes.desc()).offset(skip).limit(limit).all()
    return quotes

@router.get("/{quote_id}", response_model=QuoteSchema)
async def get_quote(
    quote_id: int,
    db: Session = Depends(get_db)
):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    return quote

@router.post("/{quote_id}/like")
async def like_quote(
    quote_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    quote.number_of_likes += 1
    db.commit()
    return {"message": "Quote liked successfully"}

@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    if quote.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this quote"
        )
    
    db.delete(quote)
    db.commit()
    return {"message": "Quote deleted successfully"} 