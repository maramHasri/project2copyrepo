from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl, validator
from datetime import datetime
from fastapi import UploadFile
from models import UserRole

# User schemas
class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    phone_number: str

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.reader

class UserUpdate(BaseModel):
    bio: Optional[str] = None
    social_links: Optional[str] = None

class UserUpdateWithImage(BaseModel):
    bio: Optional[str] = None
    social_links: Optional[str] = None

class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserInDB):
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    social_links: Optional[str] = None
    publisher_id: Optional[int] = None
    has_publisher_record: Optional[bool] = None

# Login schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class RoleLoginRequest(BaseModel):
    username: str
    password: str
    role: UserRole

# File upload schemas
class FileUploadResponse(BaseModel):
    filename: str
    file_url: str
    message: str

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# Book schemas
class BookBase(BaseModel):
    title: str
    description: str
    is_free: bool
    price: Optional[float] = None
    cover_url: Optional[HttpUrl] = None

class BookCreate(BookBase):
    category_ids: List[int]

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_free: Optional[bool] = None
    price: Optional[float] = None
    category_ids: Optional[List[int]] = None
    cover_url: Optional[HttpUrl] = None

class Book(BookBase):
    id: int
    author_id: int
    publisher_id: Optional[int] = None
    created_at: datetime
    categories: List[Category]

    class Config:
        from_attributes = True

# Publisher schemas
class PublisherBase(BaseModel):
    name: str
    foundation_date: datetime
    address: Optional[str] = None
    contact_info: str

class PublisherCreate(PublisherBase):
    logo: Optional[HttpUrl] = None

class PublisherUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[HttpUrl] = None
    address: Optional[str] = None
    contact_info: Optional[str] = None

class Publisher(PublisherBase):
    id: int
    user_id: int
    logo: Optional[HttpUrl] = None

    class Config:
        from_attributes = True

# Quote schemas
class QuoteBase(BaseModel):
    text: str
    book_id: int

    @validator('text')
    def must_be_in_smart_quotes(cls, v):
        if not (v.startswith('"') and v.endswith('"')):
            raise ValueError('Quote text must be wrapped in smart quotes (""')
        return v

class QuoteCreate(QuoteBase):
    pass

class Quote(QuoteBase):
    id: int
    author_id: int
    number_of_likes: int
    created_at: datetime

    class Config:
        from_attributes = True

# Comment schemas
class CommentBase(BaseModel):
    text: str
    book_id: int

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Vacancy schemas
class VacancyBase(BaseModel):
    title: str

class VacancyCreate(VacancyBase):
    pass

class VacancyUpdate(BaseModel):
    title: Optional[str] = None

class Vacancy(VacancyBase):
    id: int
    publisher_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class VacancyAttachmentBase(BaseModel):
    attachment_url: HttpUrl
    attachment_type: str

class VacancyAttachmentCreate(VacancyAttachmentBase):
    pass

class VacancyAttachment(VacancyAttachmentBase):
    id: int
    vacancy_id: int

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: UserRole
    user_id: int

class TokenData(BaseModel):
    username: Optional[str] = None

# Interest schemas
class UserInterests(BaseModel):
    category_ids: List[int]

# Admin schemas
class AdminStats(BaseModel):
    total_users: int
    total_books: int
    total_categories: int
    total_publishers: int
    users_by_role: dict
    recent_books: List[Book]
    recent_users: List[User]

class UserManagement(BaseModel):
    user_id: int
    action: str  # "activate", "deactivate", "change_role", "delete"

# OTP schemas
class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

class OTPResponse(BaseModel):
    message: str
    otp: Optional[str] = None  # Only for testing, remove in production 