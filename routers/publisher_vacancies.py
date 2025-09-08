from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models import Vacancy, VacancyAttachment, PublisherHouse, CVApplication
from schemas import VacancyCreate, Vacancy as VacancySchema, VacancyUpdate, VacancyAttachmentCreate, CVApplication as CVApplicationSchema
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
        position=vacancy.position,  # Use position field as intended
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
    """Update a vacancy (only if owned by current publisher) - Partial update supported"""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    # Get the raw request data to see exactly what was sent
    raw_data = vacancy_update.dict()
    
    # Only update fields that were explicitly provided (not None and not default values)
    provided_fields = {}
    
    # Check each field individually - only update if it's not None and not a default string
    if raw_data.get('position') is not None and raw_data['position'] != "string":
        provided_fields['position'] = raw_data['position']
    
    if raw_data.get('description') is not None and raw_data['description'] != "string":
        provided_fields['description'] = raw_data['description']
    
    if raw_data.get('requirements') is not None and raw_data['requirements'] != "string":
        provided_fields['requirements'] = raw_data['requirements']
    
    if raw_data.get('is_active') is not None:
        provided_fields['is_active'] = raw_data['is_active']
    
    if not provided_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    
    # Update only the provided fields, preserving existing values for others
    for field, value in provided_fields.items():
        if hasattr(vacancy, field):
            setattr(vacancy, field, value)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid field '{field}' for vacancy update"
            )
    
    db.commit()
    db.refresh(vacancy)
    
    return vacancy

# Alternative PATCH endpoint for more reliable partial updates
@router.patch("/{vacancy_id}", response_model=VacancySchema)
async def patch_vacancy(
    vacancy_id: int,
    request: Request,
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Patch a vacancy with only the provided fields - More reliable partial update"""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    # Get the raw JSON body
    try:
        body = await request.json()
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    # Only update fields that were explicitly provided
    updated = False
    for field, value in body.items():
        if field in ['position', 'description', 'requirements', 'is_active']:
            if hasattr(vacancy, field):
                setattr(vacancy, field, value)
                updated = True
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid field '{field}' for vacancy update"
                )
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    
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

# # Public endpoints (no authentication required)
# @router.get("/public/all", response_model=List[VacancySchema])
# async def get_all_active_vacancies(
#     skip: int = 0,
#     limit: int = 10,
#     db: Session = Depends(get_db)
# ):
#     """Get all active vacancies (public endpoint)"""
#     vacancies = db.query(Vacancy).filter(
#         Vacancy.is_active == True
#     ).offset(skip).limit(limit).all()
#     return vacancies

# @router.get("/public/{vacancy_id}", response_model=VacancySchema)
# async def get_public_vacancy(
#     vacancy_id: int,
#     db: Session = Depends(get_db)
# ):
#     """Get a specific active vacancy (public endpoint)"""
#     vacancy = db.query(Vacancy).filter(
#         Vacancy.id == vacancy_id,
#         Vacancy.is_active == True
#     ).first()
    
#     if not vacancy:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Vacancy not found"
#         )
    
#     return vacancy

# Publisher CV Application Management
@router.get("/{vacancy_id}/applications", response_model=List[CVApplicationSchema])
async def get_vacancy_applications(
    vacancy_id: int,
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Get all CV applications for a specific vacancy (publisher only)"""
    # Check if vacancy exists and belongs to this publisher
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found or you don't have permission to view it"
        )
    
    # Get all applications for this vacancy
    applications = db.query(CVApplication).options(
        joinedload(CVApplication.user)
    ).filter(CVApplication.vacancy_id == vacancy_id).all()
    
    return applications

@router.get("/applications/all", response_model=List[CVApplicationSchema])
async def get_all_my_vacancy_applications(
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Get all CV applications for all vacancies of this publisher"""
    # Get all vacancy IDs for this publisher
    vacancy_ids = db.query(Vacancy.id).filter(
        Vacancy.publisher_house_id == current_publisher.id
    ).all()
    vacancy_ids = [v[0] for v in vacancy_ids]
    
    if not vacancy_ids:
        return []
    
    # Get all applications for these vacancies
    applications = db.query(CVApplication).options(
        joinedload(CVApplication.user),
        joinedload(CVApplication.vacancy)
    ).filter(CVApplication.vacancy_id.in_(vacancy_ids)).all()
    
    return applications

@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    approved: bool = Query(..., description="Application status: true=approved, false=rejected"),
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Update the status of a CV application (publisher only)
    
    - approved=true: Application is approved
    - approved=false: Application is rejected
    """
    # Convert boolean to status string
    status = "accepted" if approved else "rejected"
    
    # Get the application
    application = db.query(CVApplication).filter(CVApplication.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if the vacancy belongs to this publisher
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == application.vacancy_id,
        Vacancy.publisher_house_id == current_publisher.id
    ).first()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this application"
        )
    
    # Update status
    application.status = status
    db.commit()
    
    status_text = "approved" if approved else "rejected"
    return {"message": f"Application {status_text} successfully"}

@router.get("/vacancies-with-applications")
async def get_vacancies_with_applications(
    current_publisher: PublisherHouse = Depends(get_current_publisher_house_from_token),
    db: Session = Depends(get_db)
):
    """Get all vacancies with their application requests for this publisher house"""
    # Get all vacancies for this publisher with their applications
    vacancies = db.query(Vacancy).options(
        joinedload(Vacancy.cv_applications).joinedload(CVApplication.user)
    ).filter(Vacancy.publisher_house_id == current_publisher.id).all()
    
    # Format the response
    result = []
    for vacancy in vacancies:
        vacancy_data = {
            "vacancy": {
                "id": vacancy.id,
                "title": vacancy.title,
                "position": vacancy.position,
                "description": vacancy.description,
                "requirements": vacancy.requirements,
                "is_active": vacancy.is_active,
                "created_at": vacancy.created_at,
                "publisher_house_id": vacancy.publisher_house_id
            },
            "applications": []
        }
        
        # Add applications for this vacancy
        for application in vacancy.cv_applications:
            application_data = {
                "id": application.id,
                "user_id": application.user_id,
                "user_name": application.user.username if application.user else None,
                "cv_file_path": application.cv_file_path,
                "cover_letter": application.cover_letter,
                "status": application.status,
                "applied_at": application.applied_at
            }
            vacancy_data["applications"].append(application_data)
        
        result.append(vacancy_data)
    
    return result 