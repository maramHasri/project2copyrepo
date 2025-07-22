from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Book, User, Category
from schemas import BookCreate, BookUpdate, Book as BookSchema, FileUploadResponse
from unified_auth import get_current_unified_user
from file_upload import save_book_cover, delete_file

router = APIRouter()

@router.post("/", response_model=BookSchema)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db)
):
    # Enforce unique book title
    if db.query(Book).filter(Book.title == book.title).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book title must be unique"
        )
    
    # is_free/price validation
    if book.is_free:
        if book.price not in (None, 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be null or 0 for free books"
            )
    else:
        if book.price is None or book.price == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price is required for paid books"
            )
    
    # Get categories
    categories = db.query(Category).filter(Category.id.in_(book.category_ids)).all()
    if len(categories) != len(book.category_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more categories not found"
        )
    
    # For public book creation, we'll set author_id to None since no user is authenticated
    db_book = Book(
        title=book.title,
        description=book.description,
        is_free=book.is_free,
        price=book.price,
        author_id=None,  # No specific author for public creation
        categories=categories
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.post("/simple", response_model=BookSchema)
async def create_book_simple(
    book: BookCreate,
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    """Simple book creation endpoint that works with any authenticated user"""
    # Enforce unique book title
    if db.query(Book).filter(Book.title == book.title).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book title must be unique"
        )
    
    # is_free/price validation
    if book.is_free:
        if book.price not in (None, 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be null or 0 for free books"
            )
    else:
        if book.price is None or book.price == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price is required for paid books"
            )
    
    # Get categories
    categories = db.query(Category).filter(Category.id.in_(book.category_ids)).all()
    if len(categories) != len(book.category_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more categories not found"
        )
    
    db_book = Book(
        title=book.title,
        description=book.description,
        is_free=book.is_free,
        price=book.price,
        author_id=current_user.id,
        categories=categories
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.post("/with-cover", response_model=BookSchema)
async def create_book_with_cover(
    title: str = Form(...),
    description: str = Form(...),
    is_free: bool = Form(...),
    price: Optional[float] = Form(None),
    category_ids: str = Form(...),  # JSON string of category IDs
    cover_image: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    import json
    
    # Parse category IDs
    try:
        category_id_list = json.loads(category_ids)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category_ids format. Must be a JSON array."
        )
    
    # Create book data
    book_data = {
        "title": title,
        "description": description,
        "is_free": is_free,
        "price": price,
        "category_ids": category_id_list
    }
    
    # Validate book data
    if is_free and price not in (None, 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be null or 0 for free books"
        )
    elif not is_free and (price is None or price == 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price is required for paid books"
        )
    
    # Check if book title already exists
    if db.query(Book).filter(Book.title == title).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book title must be unique"
        )
    
    # Get categories
    categories = db.query(Category).filter(Category.id.in_(category_id_list)).all()
    if len(categories) != len(category_id_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more categories not found"
        )
    
    # Create book
    db_book = Book(
        title=title,
        description=description,
        is_free=is_free,
        price=price,
        author_id=current_user.id,
        categories=categories
    )
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Handle cover image upload
    if cover_image:
        cover_url = save_book_cover(cover_image, db_book.id)
        db_book.cover_url = cover_url
        db.commit()
        db.refresh(db_book)
    
    return db_book

@router.post("/{book_id}/upload-cover", response_model=FileUploadResponse)
async def upload_book_cover(
    book_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    # Check if book exists and user has permission
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if book.author_id != current_user.id and current_user.role != "publisher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Delete old cover if exists
    if book.cover_url:
        delete_file(book.cover_url)
    
    # Save new cover
    cover_url = save_book_cover(file, book_id)
    book.cover_url = cover_url
    
    db.commit()
    db.refresh(book)
    
    return FileUploadResponse(
        filename=file.filename,
        file_url=cover_url,
        message="Book cover uploaded successfully"
    )

@router.get("/", response_model=List[BookSchema])
async def get_books(
    title: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Book)
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    books = query.offset(skip).limit(limit).all()
    return books

@router.get("/recommended", response_model=List[BookSchema])
async def get_recommended_books(
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    # Recommend books based on user interests
    if not current_user.interests:
        return []
    category_ids = [cat.id for cat in current_user.interests]
    books = db.query(Book).join(Book.categories).filter(Category.id.in_(category_ids)).all()
    return books

@router.get("/{title}", response_model=BookSchema)
async def get_book_by_title(
    title: str,
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.title == title).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book

@router.put("/{title}", response_model=BookSchema)
async def update_book_by_title(
    title: str,
    book_update: BookUpdate,
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    db_book = db.query(Book).filter(Book.title == title).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if db_book.author_id != current_user.id and current_user.role != "publisher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # is_free/price validation
    if book_update.is_free is not None:
        if book_update.is_free:
            if book_update.price not in (None, 0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price must be null or 0 for free books"
                )
        else:
            if book_update.price is None or book_update.price == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price is required for paid books"
                )
    
    # Update book fields
    for field, value in book_update.dict(exclude_unset=True, exclude={'category_ids'}).items():
        setattr(db_book, field, value)
    
    # Update categories if provided
    if book_update.category_ids:
        categories = db.query(Category).filter(Category.id.in_(book_update.category_ids)).all()
        if len(categories) != len(book_update.category_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more categories not found"
            )
        db_book.categories = categories
    
    db.commit()
    db.refresh(db_book)
    return db_book

@router.delete("/{book_id}")
async def delete_book(
    book_id: int,
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if db_book.author_id != current_user.id and current_user.role != "publisher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this book"
        )
    
    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully"}

@router.post("/{book_id}/like")
async def like_book(
    book_id: int,
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if book in current_user.liked_books:
        current_user.liked_books.remove(book)
        message = "Book unliked"
    else:
        current_user.liked_books.append(book)
        message = "Book liked"
    
    db.commit()
    return {"message": message}

@router.post("/{book_id}/save")
async def save_book(
    book_id: int,
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if book in current_user.saved_books:
        current_user.saved_books.remove(book)
        message = "Book unsaved"
    else:
        current_user.saved_books.append(book)
        message = "Book saved"
    
    db.commit()
    return {"message": message}
