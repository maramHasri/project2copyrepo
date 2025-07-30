from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Vacancy, VacancyAttachment, PublisherHouse
from schemas import VacancyCreate, Vacancy as VacancySchema, VacancyUpdate, VacancyAttachmentCreate
from security import check_admin_role
from routers.publisher_auth import get_current_publisher_house_from_token

router = APIRouter()

# Publisher House Vacancy Management
@router.post("/", response_model=VacancySchema)
async def create_vacancy(
    vacancy: VacancyCreate,
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Create a new vacancy for the publisher house"""
    db_vacancy = Vacancy(
        title=vacancy.title,
        description=vacancy.description,
        requirements=vacancy.requirements,
        publisher_house_id=current_publisher.id
    )
    
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    
    return db_vacancy

@router.get("/my-vacancies", response_model=List[VacancySchema])
async def get_my_vacancies(
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Get all vacancies created by the current publisher house"""
    vacancies = db.query(Vacancy).filter(
        Vacancy.publisher_house_id == current_publisher.id
    ).all()
    return vacancies

@router.get("/{vacancy_id}", response_model=VacancySchema)
async def get_vacancy(
    vacancy_id: int,
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific vacancy by ID (only if owned by current publisher)"""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    return vacancy

@router.put("/{vacancy_id}", response_model=VacancySchema)
async def update_vacancy(
    vacancy_id: int,
    vacancy_update: VacancyUpdate,
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Update a vacancy (only if owned by current publisher)"""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    # Update vacancy fields
    for field, value in vacancy_update.dict(exclude_unset=True).items():
        setattr(vacancy, field, value)
    
    db.commit()
    db.refresh(vacancy)
    return vacancy

@router.delete("/{vacancy_id}")
async def delete_vacancy(
    vacancy_id: int,
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Delete a vacancy (only if owned by current publisher)"""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    db.delete(vacancy)
    db.commit()
    return {"message": "Vacancy deleted successfully"}

# Public endpoints (no authentication required)
@router.get("/public/all", response_model=List[VacancySchema])
async def get_all_active_vacancies(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all active vacancies (public endpoint)"""
    vacancies = db.query(Vacancy).filter(
        Vacancy.is_active == True
    ).offset(skip).limit(limit).all()
    return vacancies

@router.get("/public/{vacancy_id}", response_model=VacancySchema)
async def get_public_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific active vacancy (public endpoint)"""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.is_active == True
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    return vacancy 