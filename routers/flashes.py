from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Flash, User, UserRole
from schemas import FlashCreate, Flash as FlashSchema
from security import get_current_active_user, check_writer_or_admin_role

router = APIRouter()

@router.post("/", response_model=FlashSchema)
async def create_flash(
    flash: FlashCreate,
    current_user: User = Depends(check_writer_or_admin_role()),
    db: Session = Depends(get_db)
):
    """Create a flash - only writers can create flashes"""
    # Create flash with writer's name automatically
    db_flash = Flash(
        text=flash.text,
        author_id=current_user.id,
        author_name=current_user.username  # Auto-fill writer's name
    )
    db.add(db_flash)
    db.commit()
    db.refresh(db_flash)
    return db_flash

@router.get("/", response_model=List[FlashSchema])
async def get_flashes(
    skip: int = 0,
    limit: int = 10,
    author_id: int = None,
    db: Session = Depends(get_db)
):
    """Get all flashes with optional filtering"""
    query = db.query(Flash)
    
    if author_id:
        query = query.filter(Flash.author_id == author_id)
    
    flashes = query.order_by(Flash.created_at.desc()).offset(skip).limit(limit).all()
    return flashes

@router.get("/{flash_id}", response_model=FlashSchema)
async def get_flash(
    flash_id: int,
    db: Session = Depends(get_db)
):
    """Get specific flash by ID"""
    flash = db.query(Flash).filter(Flash.id == flash_id).first()
    if not flash:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash not found"
        )
    return flash

@router.post("/{flash_id}/like")
async def like_flash(
    flash_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Like a flash"""
    flash = db.query(Flash).filter(Flash.id == flash_id).first()
    if not flash:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash not found"
        )
    
    flash.number_of_likes += 1
    db.commit()
    return {"message": "Flash liked successfully"}

@router.delete("/{flash_id}")
async def delete_flash(
    flash_id: int,
    current_user: User = Depends(check_writer_or_admin_role()),
    db: Session = Depends(get_db)
):
    """Delete flash - only the author or admin can delete"""
    flash = db.query(Flash).filter(Flash.id == flash_id).first()
    if not flash:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash not found"
        )
    
    # Only the author or admin can delete
    if flash.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the flash author or admin can delete this flash"
        )
    
    db.delete(flash)
    db.commit()
    return {"message": "Flash deleted successfully"} 