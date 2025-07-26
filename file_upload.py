import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
import uuid
from datetime import datetime

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create subdirectories for different file types
IMAGES_DIR = UPLOAD_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

PROFILE_IMAGES_DIR = IMAGES_DIR / "profiles"
PROFILE_IMAGES_DIR.mkdir(exist_ok=True)

BOOK_COVERS_DIR = IMAGES_DIR / "book_covers"
BOOK_COVERS_DIR.mkdir(exist_ok=True)

BOOK_FILES_DIR = UPLOAD_DIR / "books"
BOOK_FILES_DIR.mkdir(exist_ok=True)

PUBLISHER_LOGOS_DIR = IMAGES_DIR / "publisher_logos"
PUBLISHER_LOGOS_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/gif",
    "image/webp"
}

ALLOWED_BOOK_TYPES = {
    "application/pdf"  # Only PDF files are allowed for books
}

# Maximum file size (5MB for images, 50MB for books)
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_BOOK_SIZE = 50 * 1024 * 1024

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.content_type in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size {file_size} bytes exceeds maximum allowed size of {MAX_IMAGE_SIZE} bytes"
        )

def validate_book_file(file: UploadFile) -> None:
    """Validate uploaded book file"""
    if not file.content_type in ALLOWED_BOOK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_BOOK_TYPES)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_BOOK_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size {file_size} bytes exceeds maximum allowed size of {MAX_BOOK_SIZE} bytes"
        )



def save_profile_image(file: UploadFile, user_id: int) -> str:
    """Save profile image and return the file URL"""
    validate_image_file(file)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"profile_{user_id}_{timestamp}_{unique_id}{file_extension}"
    
    file_path = PROFILE_IMAGES_DIR / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return relative URL
    return f"/uploads/images/profiles/{filename}"

def save_book_cover(file: UploadFile, book_id: int) -> str:
    """Save book cover image and return the file URL"""
    validate_image_file(file)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"book_cover_{book_id}_{timestamp}_{unique_id}{file_extension}"
    
    file_path = BOOK_COVERS_DIR / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return relative URL
    return f"/uploads/images/book_covers/{filename}"

def save_publisher_logo(file: UploadFile, publisher_id: int) -> str:
    """Save publisher logo and return the file URL"""
    validate_image_file(file)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"publisher_logo_{publisher_id}_{timestamp}_{unique_id}{file_extension}"
    
    file_path = PUBLISHER_LOGOS_DIR / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return relative URL
    return f"/uploads/images/publisher_logos/{filename}"

def save_book_file(file: UploadFile, book_id: int) -> str:
    """Save book file and return the file URL"""
    validate_book_file(file)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = Path(file.filename).suffix if file.filename else ".pdf"
    filename = f"book_{book_id}_{timestamp}_{unique_id}{file_extension}"
    
    file_path = BOOK_FILES_DIR / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return relative URL
    return f"/uploads/books/{filename}"

def delete_file(file_url: str) -> bool:
    """Delete a file by its URL"""
    try:
        if file_url and file_url.startswith("/uploads/"):
            file_path = UPLOAD_DIR / file_url[9:]  # Remove "/uploads/" prefix
            if file_path.exists():
                file_path.unlink()
                return True
    except Exception:
        pass
    return False 