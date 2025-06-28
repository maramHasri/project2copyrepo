from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Vacancy, VacancyAttachment, Publisher, User, UserRole
from schemas import VacancyCreate, Vacancy as VacancySchema, VacancyAttachmentCreate
from security import get_current_active_user, check_user_role

router = APIRouter()

@router.post("/", response_model=VacancySchema)
async def create_vacancy(
    vacancy: VacancyCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user has publisher role
    if current_user.role != UserRole.publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only publishers can create job vacancies"
        )
    
    # Fetch the Publisher record for the current user
    publisher = db.query(Publisher).filter(Publisher.user_id == current_user.id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not registered as a publisher"
        )
    
    # Create vacancy with the publisher_id from the database
    db_vacancy = Vacancy(
        title=vacancy.title,
        publisher_id=publisher.id  # Use the publisher_id from the database
    )
    
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    
    return db_vacancy

@router.get("/", response_model=List[VacancySchema])
async def get_vacancies(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    vacancies = db.query(Vacancy).offset(skip).limit(limit).all()
    return vacancies

@router.get("/{vacancy_id}", response_model=VacancySchema)
async def get_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db)
):
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    return vacancy

@router.put("/{vacancy_id}", response_model=VacancySchema)
async def update_vacancy(
    vacancy_id: int,
    vacancy_update: VacancyCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user has publisher role
    if current_user.role != UserRole.publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only publishers can update job vacancies"
        )
    
    # Fetch the Publisher record for the current user
    publisher = db.query(Publisher).filter(Publisher.user_id == current_user.id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not registered as a publisher"
        )
    
    # Get the vacancy and check ownership
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if vacancy.publisher_id != publisher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own vacancies"
        )
    
    # Update vacancy
    for field, value in vacancy_update.dict(exclude_unset=True).items():
        setattr(vacancy, field, value)
    
    db.commit()
    db.refresh(vacancy)
    return vacancy

@router.delete("/{vacancy_id}")
async def delete_vacancy(
    vacancy_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user has publisher role
    if current_user.role != UserRole.publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only publishers can delete job vacancies"
        )
    
    # Fetch the Publisher record for the current user
    publisher = db.query(Publisher).filter(Publisher.user_id == current_user.id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not registered as a publisher"
        )
    
    # Get the vacancy and check ownership
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if vacancy.publisher_id != publisher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own vacancies"
        )
    
    db.delete(vacancy)
    db.commit()
    return {"message": "Vacancy deleted successfully"}

@router.post("/{vacancy_id}/attachments", response_model=VacancyAttachmentCreate)
async def add_vacancy_attachment(
    vacancy_id: int,
    attachment: VacancyAttachmentCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user has publisher role
    if current_user.role != UserRole.publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only publishers can add attachments to job vacancies"
        )
    
    # Fetch the Publisher record for the current user
    publisher = db.query(Publisher).filter(Publisher.user_id == current_user.id).first()
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not registered as a publisher"
        )
    
    # Get the vacancy and check ownership
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if vacancy.publisher_id != publisher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add attachments to your own vacancies"
        )
    
    # Create attachment
    db_attachment = VacancyAttachment(
        vacancy_id=vacancy_id,
        attachment_url=attachment.attachment_url,
        attachment_type=attachment.attachment_type
    )
    
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    
    return db_attachment 