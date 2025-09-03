from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
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
    # Book validation is now optional - users can create quotes for any book name
    # No need to check if book exists in database
    
    # Any authenticated user can create quotes
    db_quote = Quote(
        **quote.dict(),
        author_id=current_user.id
    )
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    
    # Load the author relationship to populate author_name
    db_quote = db.query(Quote).options(joinedload(Quote.author)).filter(Quote.id == db_quote.id).first()
    
    return db_quote

@router.get("/", response_model=List[QuoteSchema])
async def get_quotes(
    skip: int = 0,
    limit: int = 10,
    book_name: str = None,
    author_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(Quote)
    
    if book_name:
        query = query.filter(Quote.book_name == book_name)
    if author_id:
        query = query.filter(Quote.author_id == author_id)
    
    quotes = query.order_by(Quote.number_of_likes.desc()).offset(skip).limit(limit).all()
    return quotes

@router.get("/liked", response_model=List[QuoteSchema])
async def get_liked_quotes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all quotes that the current user has liked"""
    # Get all quotes that the current user has liked
    liked_quotes = db.query(Quote).options(joinedload(Quote.author)).filter(
        Quote.liked_by.any(User.id == current_user.id)
    ).all()
    
    return liked_quotes

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
    
    # Check if user already liked this quote
    if quote in current_user.liked_quotes:
        # Unlike the quote
        current_user.liked_quotes.remove(quote)
        quote.number_of_likes -= 1
        message = "Quote unliked"
    else:
        # Like the quote
        current_user.liked_quotes.append(quote)
        quote.number_of_likes += 1
        message = "Quote liked"
    
    db.commit()
    return {"message": message}

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