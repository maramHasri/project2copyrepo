from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Book, User, Category, UserRole
from schemas import BookCreate, BookUpdate, Book as BookSchema, FileUploadResponse
from security import get_current_active_user, get_current_unified_user
from file_upload import save_book_cover, save_book_file, delete_file
from fastapi import Request
from routers.publisher_auth import get_current_publisher_house_from_token
router = APIRouter()

@router.post("/with-file", response_model=BookSchema)
async def create_writer_book_with_file(
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
    current_user = Depends(get_current_unified_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a book with PDF file upload (required) and optional cover image.
    
    This endpoint is EXCLUSIVELY for writers to create books.
    - Readers and admins are NOT allowed to create books
    - Publisher houses must use their own endpoint
    - Author name is automatically set to the writer's username
    
    Category IDs can be provided as:
    - JSON array: [1,2,3]
    - Comma-separated: 1,2,3
    - Single value: 1
    """
    import json
    
    # Validate that only writers can use this endpoint
    if not hasattr(current_user, 'role') or current_user.role != UserRole.writer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is exclusively for writers. Only users with 'writer' role can create books through this endpoint."
        )
    
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
    
    # Handle author_name logic - user is guaranteed to be a writer at this point
    final_author_name = current_user.username
    author_id = current_user.id
    publisher_house_id = None
    
    # Create book first (without file URL initially)
    # Generate a temporary unique filename for the book
    import uuid
    temp_filename = f"temp_book_{uuid.uuid4().hex[:8]}.pdf"
    
    db_book = Book(
        title=title,
        description=description,
        is_free=is_free,
        price=price,
        author_name=final_author_name,
        author_id=author_id,
        publisher_house_id=publisher_house_id,
        book_file=temp_filename,  # Use temporary unique filename
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

    # Populate publisher_house_name before returning
    if db_book.publisher_house:
        db_book.publisher_house_name = db_book.publisher_house.name
    else:
        db_book.publisher_house_name = None

    return db_book

@router.post("/publisher/books/create", response_model=BookSchema)
async def create_publisher_book_with_file(
    title: str = Form(..., description="Book title (required)"),
    description: str = Form(..., description="Book description (required)"),
    is_free: bool = Form(..., description="Whether the book is free (required)"),
    price: Optional[float] = Form(None, description="Book price (required if not free)"),
    category_ids: str = Form(
        ..., 
        description="Category IDs. Accepts: [1,2,3] (JSON array), 1,2,3 (comma-separated), or 1 (single value)",
        example="1,2,3"
    ),
    book_file: UploadFile = File(..., description="PDF file of the book (required)"),
    cover_image: Optional[UploadFile] = File(None, description="Cover image file (optional)"),
    author_name: str = Form(..., description="Author name (required)"),
    current_publisher = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db),
    request: Request = None
):
    import json
    
    # Validate book file is PDF
    if not book_file or book_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book file must be a PDF file. Only PDF files are allowed."
        )
    
    # Validate cover image if provided
    if cover_image and cover_image.filename:
        allowed_image_types = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
        if cover_image.content_type not in allowed_image_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cover image must be one of: {', '.join(allowed_image_types)}. Got: {cover_image.content_type}"
            )
    # Parse category IDs
    try:
        try:
            category_id_list = json.loads(category_ids)
            if isinstance(category_id_list, int):
                category_id_list = [category_id_list]
            elif not isinstance(category_id_list, list):
                raise ValueError
        except (json.JSONDecodeError, ValueError, TypeError):
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
    # Handle price logic
    if is_free:
        price = 0
    else:
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
    # Create book
    # Generate a temporary unique filename for the book
    import uuid
    temp_filename = f"temp_book_{uuid.uuid4().hex[:8]}.pdf"
    
    db_book = Book(
        title=title,
        description=description,
        is_free=is_free,
        price=price,
        author_name=author_name,
        author_id=None,
        publisher_house_id=current_publisher.id,
        book_file=temp_filename,  # Use temporary unique filename
        categories=categories
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    # Save the book file
    book_file_url = save_book_file(book_file, db_book.id)
    db_book.book_file = book_file_url
    # Handle cover image upload if provided
    if cover_image:
        cover_path = save_book_cover(cover_image, db_book.id)
        db_book.cover_image = cover_path
    db.commit()
    db.refresh(db_book)
    
    # Populate publisher_house_name before returning
    if db_book.publisher_house:
        db_book.publisher_house_name = db_book.publisher_house.name
    else:
        db_book.publisher_house_name = None
    
    return db_book


@router.get("/", response_model=List[BookSchema])
async def get_books(
    title: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Book).join(Book.publisher_house, isouter=True).filter(Book.is_blocked == False)
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    books = query.offset(skip).limit(limit).all()
    
    # Populate publisher_house_name for each book
    for book in books:
        if book.publisher_house:
            book.publisher_house_name = book.publisher_house.name
        else:
            book.publisher_house_name = None
    
    return books

@router.get("/recommended", response_model=List[BookSchema])
async def get_recommended_books(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    #  based on user interests
    if not current_user.interests:
        return []
    category_ids = [cat.id for cat in current_user.interests]
    books = db.query(Book).join(Book.categories).filter(
        Category.id.in_(category_ids),
        Book.is_blocked == False
    ).all()
    
    # Populate publisher_house_name for each book
    for book in books:
        if book.publisher_house:
            book.publisher_house_name = book.publisher_house.name
        else:
            book.publisher_house_name = None
    
    return books

# Get saved/liked books - MUST come before /{title} route
@router.get("/saved", response_model=List[BookSchema])
async def get_saved_books(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all books liked by the current user"""
    books = [book for book in current_user.liked_books if not book.is_blocked]
    
    # Populate publisher_house_name for each book
    for book in books:
        if book.publisher_house:
            book.publisher_house_name = book.publisher_house.name
        else:
            book.publisher_house_name = None
    
    return books

@router.get("/{title}", response_model=BookSchema)
async def get_book_by_title(
    title: str,
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.title == title, Book.is_blocked == False).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Populate publisher_house_name
    if book.publisher_house:
        book.publisher_house_name = book.publisher_house.name
    else:
        book.publisher_house_name = None
    
    return book

@router.put("/{book_id}", response_model=BookSchema)
async def update_book_by_id(
    book_id: int,
    book_update: BookUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if db_book.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Handle price logic based on is_free status
    if book_update.is_free is not None:
        if book_update.is_free:
            # If book is being set to free, automatically set price to 0
            # Only set price if it wasn't explicitly provided in the request
            if book_update.price is None:
                book_update.price = 0
        else:
            # If book is being set to paid, price is required
            if book_update.price is None or book_update.price == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price is required for paid books"
                )
    
    # Update only the fields that are explicitly provided (partial update)
    update_data = book_update.dict(exclude_unset=True, exclude={'category_ids', 'cover_url'})
    
    # Handle cover_url specially - it maps to cover_image in the database
    if book_update.cover_url is not None:
        db_book.cover_image = book_update.cover_url
    
    # Update only the fields that were explicitly provided in the request
    for field, value in update_data.items():
        if value is not None:  # Only update if value is not None
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
    
    # Populate publisher_house_name before returning
    if db_book.publisher_house:
        db_book.publisher_house_name = db_book.publisher_house.name
    else:
        db_book.publisher_house_name = None
    
    return db_book

@router.patch("/{book_id}", response_model=BookSchema)
async def patch_book_by_id(
    book_id: int,
    book_update: BookUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Partial update of a book - only updates provided fields"""
    # Convert to dict and exclude unset fields
    request_data = book_update.dict(exclude_unset=True)
    
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if db_book.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Handle price logic based on is_free status
    if 'is_free' in request_data:
        if request_data['is_free']:
            # If book is being set to free, automatically set price to 0
            # Only set price if it wasn't explicitly provided in the request
            if 'price' not in request_data:
                request_data['price'] = 0
        else:
            # If book is being set to paid, price is required
            if 'price' not in request_data or request_data.get('price') == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price is required for paid books"
                )
    
    # PATCH: Only update fields that are explicitly provided in the request
    fields_to_exclude = {'category_ids', 'cover_url', 'id', 'author_id', 'created_at', 'publisher_house_name'}
    
    # Handle cover_url specially - it maps to cover_image in the database
    if 'cover_url' in request_data and request_data['cover_url'] is not None:
        db_book.cover_image = request_data['cover_url']
    
    # Update only the fields that were explicitly provided in the request
    for field, value in request_data.items():
        if field not in fields_to_exclude and value is not None:
            setattr(db_book, field, value)
    
    # Update categories if provided
    if 'category_ids' in request_data and request_data['category_ids']:
        categories = db.query(Category).filter(Category.id.in_(request_data['category_ids'])).all()
        if len(categories) != len(request_data['category_ids']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more categories not found"
            )
        db_book.categories = categories
    
    db.commit()
    db.refresh(db_book)
    
    # Populate publisher_house_name before returning
    if db_book.publisher_house:
        db_book.publisher_house_name = db_book.publisher_house.name
    else:
        db_book.publisher_house_name = None
    
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
    
    if db_book.author_id != current_user.id:
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