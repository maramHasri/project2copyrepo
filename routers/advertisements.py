from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from models import Advertisement, PublisherHouse, Admin, User
from schemas import Advertisement as AdvertisementSchema
from security import get_current_admin, get_current_active_user
from routers.publisher_auth import get_current_publisher_house_from_token
from datetime import datetime
import os
import uuid

router = APIRouter()

# Publisher House - Upload Advertisement
@router.post("/upload", response_model=AdvertisementSchema)
async def upload_advertisement(
    image: UploadFile = File(...),
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Upload advertisement image - publisher house only"""
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (max 5MB)
        if image.size and image.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/advertisements"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        unique_filename = f"ad_{current_publisher.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Create advertisement record
        advertisement = Advertisement(
            image_url=f"/uploads/advertisements/{unique_filename}",
            publisher_house_id=current_publisher.id,
            status="pending"
        )
        
        db.add(advertisement)
        db.commit()
        db.refresh(advertisement)
        
        return advertisement
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading advertisement: {str(e)}"
        )

# Publisher House - Get My Advertisements
@router.get("/my", response_model=List[AdvertisementSchema])
async def get_my_advertisements(
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Get all advertisements for current publisher house"""
    try:
        advertisements = db.query(Advertisement).filter(
            Advertisement.publisher_house_id == current_publisher.id
        ).order_by(Advertisement.created_at.desc()).all()
        
        return advertisements
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting advertisements: {str(e)}"
        )

# Admin - Get All Advertisements for Review
@router.get("/admin", response_model=List[AdvertisementSchema])
async def get_all_advertisements(
    status_filter: Optional[str] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all advertisements for admin review - admin only"""
    try:
        query = db.query(Advertisement).options(
            joinedload(Advertisement.publisher_house),
            joinedload(Advertisement.admin)
        )
        
        if status_filter:
            query = query.filter(Advertisement.status == status_filter)
        
        advertisements = query.order_by(Advertisement.created_at.desc()).all()
        return advertisements
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting advertisements: {str(e)}"
        )

# Admin - Approve Advertisement
@router.put("/admin/{advertisement_id}/approve")
async def approve_advertisement(
    advertisement_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve an advertisement - admin only"""
    try:
        advertisement = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
        
        if not advertisement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Advertisement not found"
            )
        
        advertisement.status = "approved"
        advertisement.approved_by = current_admin.id
        advertisement.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Advertisement approved successfully",
            "advertisement_id": advertisement_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving advertisement: {str(e)}"
        )

# Admin - Reject Advertisement
@router.put("/admin/{advertisement_id}/reject")
async def reject_advertisement(
    advertisement_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reject an advertisement - admin only"""
    try:
        advertisement = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
        
        if not advertisement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Advertisement not found"
            )
        
        advertisement.status = "rejected"
        advertisement.approved_by = current_admin.id
        advertisement.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Advertisement rejected successfully",
            "advertisement_id": advertisement_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting advertisement: {str(e)}"
        )

# Users - Get Approved Advertisements
@router.get("/", response_model=List[AdvertisementSchema])
async def get_approved_advertisements(
    db: Session = Depends(get_db)
):
    """Get approved advertisements for users"""
    try:
        advertisements = db.query(Advertisement).filter(
            Advertisement.status == "approved"
        ).order_by(Advertisement.created_at.desc()).all()
        
        return advertisements
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting advertisements: {str(e)}"
        )
