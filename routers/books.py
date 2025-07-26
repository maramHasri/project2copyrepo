from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Book, User, Category, UserRole
from schemas import BookCreate, BookUpdate, Book as BookSchema, FileUploadResponse
from security import get_current_active_user
from file_upload import save_book_cover, save_book_file, delete_file
from fastapi import Request
router = APIRouter()

# @router.post("/", response_model=BookSchema)
# async def create_book(
#     book: BookCreate,
#     db: Session = Depends(get_db)
# ):
#     # This endpoint is deprecated - use /with-file instead for proper file upload
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Please use /books/with-file endpoint to create books with file uploads"
#     )

# @router.post("/simple", response_model=BookSchema)
# async def create_book_simple(
#     book: BookCreate,
#     current_user = Depends(get_current_unified_user),
#     db: Session = Depends(get_db)
# ):
#     """Simple book creation endpoint that works with any authenticated user"""
#     # This endpoint is deprecated - use /with-file instead for proper file upload
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Please use /books/with-file endpoint to create books with file uploads"
#     )

# @router.post("/with-cover", response_model=BookSchema)
# async def create_book_with_cover(
#     title: str = Form(...),
#     description: str = Form(...),
#     is_free: bool = Form(...),
#     price: Optional[float] = Form(None),
#     category_ids: str = Form(...),  # JSON string of category IDs
#     cover_image: Optional[UploadFile] = File(None),
#     current_user = Depends(get_current_unified_user),
#     db: Session = Depends(get_db)
# ):
#     import json
    
#     # Parse category IDs
#     try:
#         category_id_list = json.loads(category_ids)
#     except json.JSONDecodeError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid category_ids format. Must be a JSON array."
#         )
    
#     # Create book data
#     book_data = {
#         "title": title,
#         "description": description,
#         "is_free": is_free,
#         "price": price,
#         "category_ids": category_id_list
#     }
    
#     # Validate book data
#     if is_free and price not in (None, 0):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Price must be null or 0 for free books"
#         )
#     elif not is_free and (price is None or price == 0):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Price is required for paid books"
#         )
    
#     # Check if book title already exists
#     if db.query(Book).filter(Book.title == title).first():
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Book title must be unique"
#         )
    
#     # Get categories
#     categories = db.query(Category).filter(Category.id.in_(category_id_list)).all()
#     if len(categories) != len(category_id_list):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="One or more categories not found"
#         )
    
#     # Create book
#     db_book = Book(
#         title=title,
#         description=description,
#         is_free=is_free,
#         price=price,
#         author_id=current_user.id,
#         categories=categories
#     )
    
#     db.add(db_book)
#     db.commit()
#     db.refresh(db_book)
    
#     # Handle cover image upload
#     if cover_image:
#         cover_url = save_book_cover(cover_image, db_book.id)
#         db_book.cover_url = cover_url
#         db.commit()
#         db.refresh(db_book)
    
#     return db_book

@router.post("/with-file", response_model=BookSchema)
async def create_book_with_file(
    title: str = Form(...),
    description: str = Form(...),
    is_free: bool = Form(...),
    price: Optional[float] = Form(None),
    category_ids: str = Form(
        ..., 
        description="Category IDs. Accepts: [1,2,3] (JSON array), 1,2,3 (comma-separated), or 1 (single value)",
        example="1,2,3"
    ),
    book_file: UploadFile = File(..., description="PDF file of the book (required)"),
    cover_image: Optional[UploadFile] = File(None, description="Cover image file (optional)"),
    author_name: Optional[str] = Form(None, description="Author name (required for publishers, auto-filled for writers)"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a book with PDF file upload (required) and optional cover image.
    
    Category IDs can be provided as:
    - JSON array: [1,2,3]
    - Comma-separated: 1,2,3
    - Single value: 1
    """
    import json
    
    # Validate book file is PDF
    if book_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book file must be a PDF file. Only PDF files are allowed."
        )
    
    # Parse category IDs (accepts JSON array, comma-separated, or single int)
    try:
        try:
            # Try JSON array first
            category_id_list = json.loads(category_ids)
            if isinstance(category_id_list, int):
                category_id_list = [category_id_list]
            elif not isinstance(category_id_list, list):
                raise ValueError
        except (json.JSONDecodeError, ValueError, TypeError):
            # Fallback: comma-separated or single value
            category_id_list = [int(x.strip()) for x in category_ids.split(',') if x.strip()]
        if not category_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one category must be selected."
            )
        if not all(isinstance(cat_id, int) for cat_id in category_id_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All category IDs must be integers."
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category_ids format: '{category_ids}'. Accepts: [1,2,3], 1,2,3, or 1."
        )
    
    # Handle price logic based on is_free status
    if is_free:
        # If book is free, automatically set price to 0 regardless of what user entered
        price = 0
    else:
        # If book is not free, price is required
        if price is None or price == 0:
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
        found_ids = [cat.id for cat in categories]
        missing_ids = [cat_id for cat_id in category_id_list if cat_id not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categories not found: {missing_ids}"
        )
    
    # Handle author_name logic based on user type
    if hasattr(current_user, 'role') and current_user.role == UserRole.writer:
        # If user is a writer, automatically set author_name to their username
        final_author_name = current_user.username
        author_id = current_user.id
        publisher_house_id = None
    else:
        # If user is a publisher or admin, require author_name to be provided
        if not author_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Author name is required "
            )
        final_author_name = author_name
        author_id = None
        publisher_house_id = current_user.id if hasattr(current_user, 'id') else None
    
    # Create book first (without file URL initially)
    db_book = Book(
        title=title,
        description=description,
        is_free=is_free,
        price=price,
        author_name=final_author_name,
        author_id=author_id,
        publisher_house_id=publisher_house_id,
        book_file="",  # Temporary empty string
        categories=categories
    )
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Now save the book file with the correct book ID
    book_file_url = save_book_file(book_file, db_book.id)
    db_book.book_file = book_file_url
    
    # Handle cover image upload if provided
    if cover_image:
        cover_path = save_book_cover(cover_image, db_book.id)
        db_book.cover_image = cover_path
    
    db.commit()
    db.refresh(db_book)

    return db_book

@router.post("/{book_id}/upload-cover", response_model=FileUploadResponse)
async def upload_book_cover(
    book_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if book exists and user has permission
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if book.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Delete old cover if exists
    if book.cover_image:
        delete_file(book.cover_image)
    
    # Save new cover
    cover_path = save_book_cover(file, book_id)
    book.cover_image = cover_path
    
    db.commit()
    db.refresh(book)
    
    return FileUploadResponse(
        filename=file.filename,
        file_url=cover_path,
        message="Book cover uploaded successfully"
    )

@router.post("/{book_id}/upload-file", response_model=FileUploadResponse)
async def upload_book_file(
    book_id: int,
    file: UploadFile = File(..., description="PDF file of the book (required)"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Validate book file is PDF
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book file must be a PDF file. Only PDF files are allowed."
        )
    
    # Check if book exists and user has permission
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if book.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Delete old book file if exists
    if book.book_file:
        delete_file(book.book_file)
    
    # Save new book file
    book_file_url = save_book_file(file, book_id)
    book.book_file = book_file_url
    
    db.commit()
    db.refresh(book)
    
    return FileUploadResponse(
        filename=file.filename,
        file_url=book_file_url,
        message="Book file uploaded successfully"
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
    current_user = Depends(get_current_active_user),
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
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_book = db.query(Book).filter(Book.title == title).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if db_book.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Handle price logic based on is_free status
    if book_update.is_free is not None:
        if book_update.is_free:
            # If book is being set to free, automatically set price to 0
            book_update.price = 0
        else:
            # If book is being set to paid, price is required
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
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if db_book.author_id != current_user.id and current_user.role != UserRole.admin:
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
    current_user = Depends(get_current_active_user),
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
    current_user = Depends(get_current_active_user),
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
