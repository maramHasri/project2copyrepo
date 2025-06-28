from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Publisher, User
from schemas import PublisherCreate, Publisher as PublisherSchema, FileUploadResponse
from security import get_current_active_user
from file_upload import save_publisher_logo, delete_file

router = APIRouter()

@router.post("/", response_model=PublisherSchema)
async def create_publisher(
    publisher: PublisherCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create publishers"
        )
    
    db_publisher = Publisher(**publisher.dict())
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

@router.post("/with-logo", response_model=PublisherSchema)
async def create_publisher_with_logo(
    name: str = Form(...),
    foundation_date: str = Form(...),  # ISO format string
    address: Optional[str] = Form(None),
    contact_info: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create publishers"
        )
    
    # Parse foundation date
    from datetime import datetime
    try:
        foundation_date_parsed = datetime.fromisoformat(foundation_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid foundation_date format. Use ISO format (YYYY-MM-DD)"
        )
    
    # Create publisher
    db_publisher = Publisher(
        name=name,
        foundation_date=foundation_date_parsed,
        address=address,
        contact_info=contact_info
    )
    
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    
    # Handle logo upload
    if logo:
        logo_url = save_publisher_logo(logo, db_publisher.id)
        db_publisher.logo = logo_url
        db.commit()
        db.refresh(db_publisher)
    
    return db_publisher

@router.post("/{publisher_id}/upload-logo", response_model=FileUploadResponse)
async def upload_publisher_logo(
    publisher_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update publishers"
        )
    
    # Check if publisher exists
    publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    
    # Delete old logo if exists
    if publisher.logo:
        delete_file(publisher.logo)
    
    # Save new logo
    logo_url = save_publisher_logo(file, publisher_id)
    publisher.logo = logo_url
    
    db.commit()
    db.refresh(publisher)
    
    return FileUploadResponse(
        filename=file.filename,
        file_url=logo_url,
        message="Publisher logo uploaded successfully"
    )

@router.get("/", response_model=List[PublisherSchema])
async def get_publishers(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    publishers = db.query(Publisher).offset(skip).limit(limit).all()
    return publishers

@router.get("/{publisher_id}", response_model=PublisherSchema)
async def get_publisher(
    publisher_id: int,
    db: Session = Depends(get_db)
):
    publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    return publisher

@router.put("/{publisher_id}", response_model=PublisherSchema)
async def update_publisher(
    publisher_id: int,
    publisher: PublisherCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update publishers"
        )
    
    db_publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not db_publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    
    for key, value in publisher.dict().items():
        setattr(db_publisher, key, value)
    
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

@router.delete("/{publisher_id}")
async def delete_publisher(
    publisher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete publishers"
        )
    
    publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    
    db.delete(publisher)
    db.commit()
    return {"message": "Publisher deleted successfully"} 