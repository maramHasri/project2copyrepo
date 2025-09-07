from pydantic import BaseModel, HttpUrl, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, AdminRole

# User schema
class UserBase(BaseModel):
    username: str
    phone_number: str
    email: Optional[EmailStr] = None

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
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserInDB):
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    social_links: Optional[str] = None
    skills: Optional[str] = None  # JSON string of skills
    # Writer fields
    writer_bio: Optional[str] = None
    published_books_count: int = 0
    is_featured_writer: bool = False

    class Config:
        from_attributes = True

# Writer response schema (simplified for public viewing)
class WriterResponse(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    social_links: Optional[str] = None
    writer_bio: Optional[str] = None
    published_books_count: int = 0
    is_featured_writer: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

# Report schemas
class ReportBase(BaseModel):
    book_id: int
    reason: str
    description: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    status: Optional[str] = None  # pending, reviewed, resolved, dismissed
    admin_notes: Optional[str] = None

class Report(ReportBase):
    id: int
    user_id: int
    user_name: Optional[str] = None  # Username of the reporter
    status: str
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None  # Username of the admin who handled it
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Book blocking schemas
class BookBlockRequest(BaseModel):
    blocked_reason: str
    admin_notes: Optional[str] = None

class BookUnblockRequest(BaseModel):
    admin_notes: Optional[str] = None

# User skills update schema
class UserSkillsUpdate(BaseModel):
    skills: List[str]  # List of selected skill names

# Admin schema
class AdminBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: Optional[str] = None

class AdminCreate(AdminBase):
    password: str
    admin_code: str  # ADMIN2024

class AdminUpdate(BaseModel):
    phone_number: Optional[str] = None
    # Removed role field since all admins are super admins

class Admin(AdminBase):
    id: int
    role: AdminRole
    is_active: bool
    is_super_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Admin Action schemas
class AdminActionBase(BaseModel):
    action_type: str
    action_description: str
    target_entity_type: str
    target_entity_id: Optional[int] = None

class AdminAction(AdminActionBase):
    id: int
    admin_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RoleLoginRequest(BaseModel):
    username: str
    password: str
    role: UserRole

class FileUploadResponse(BaseModel):
    filename: str
    file_url: str
    message: str

# Publisher House schemas
class PublisherHouseBase(BaseModel):
    name: str
    email: EmailStr

class PublisherHouseCreate(PublisherHouseBase):
    password: str
    confirm_password: str
    license_image: Optional[str] = None
    logo_image: Optional[str] = None
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class PublisherHouseLogin(BaseModel):
    email: EmailStr
    password: str

class PublisherHouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_info: Optional[str] = None
    logo_image: Optional[str] = None

class PublisherHouse(PublisherHouseBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    license_image: Optional[str] = None
    logo_image: Optional[str] = None
    address: Optional[str] = None
    contact_info: Optional[str] = None
    foundation_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublisherHouseToken(BaseModel):
    access_token: str
    token_type: str
    publisher_house_id: int
    name: str
    email: str

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
    cover_url: Optional[str] = None
    book_file: str  # Required 

class BookCreate(BookBase):
    category_ids: List[int]
    author_name: Optional[str] = None  # Required 

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_free: Optional[bool] = None  
    price: Optional[float] = None    
    category_ids: Optional[List[int]] = None
    cover_url: Optional[str] = None
    author_name: Optional[str] = None  # Allow updating author name

class Book(BookBase):
    id: int
    author_name: Optional[str] = None  
    author_id: Optional[int] = None
    publisher_house_name: Optional[str] = None  # Changed from publisher_house_id to publisher_house_name
    created_at: datetime
    categories: List[Category]

    class Config:
        from_attributes = True

# Quote schemas
class QuoteBase(BaseModel):
    text: str
    book_name: str  # Changed from book_id to book_name

    @validator('text')
    def add_smart_quotes(cls, v):
        # Remove any existing quotes at the beginning and end
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            return v  # Already has double quotes
        elif v.startswith("'") and v.endswith("'"):
            # Convert single quotes to double quotes
            return f'"{v[1:-1]}"'
        else:
            # Add double quotes
            return f'"{v}"'

class QuoteCreate(QuoteBase):
    pass

class Quote(QuoteBase):
    id: int
    author_id: int
    user_name: Optional[str] = None
    number_of_likes: int
    created_at: datetime

    class Config:
        from_attributes = True

# Flash schemas
class FlashBase(BaseModel):
    text: str

    @validator('text')
    def add_smart_quotes(cls, v):
        """Automatically add smart quotes if not present"""
        # Remove any existing quotes at the beginning and end
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            return v  # Already has quotes
        elif v.startswith('"') and v.endswith('"'):
            return v  # Already has smart quotes
        else:
            # Add smart quotes
            return f'"{v}"'

class FlashCreate(FlashBase):
    pass

class Flash(FlashBase):
    id: int
    author_id: int
    author_name: str
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
    user_name: Optional[str] = None  # Username of the commenter
    created_at: datetime

    class Config:
        from_attributes = True


# Vacancy schemas
class VacancyBase(BaseModel):
    position: str
    description: Optional[str] = None
    requirements: Optional[str] = None

class VacancyCreate(VacancyBase):
    pass

class VacancyUpdate(BaseModel):
    position: Optional[str]
    description: Optional[str]
    requirements: Optional[str]
    is_active: Optional[bool]

class Vacancy(VacancyBase):
    id: int
    publisher_house_id: int
    is_active: bool
    created_at: datetime
    publisher_house: Optional[PublisherHouse] = None

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

# CV Application schemas
class CVApplicationBase(BaseModel):
    cover_letter: Optional[str] = None

class CVApplicationCreate(CVApplicationBase):
    pass

class CVApplicationUpdate(BaseModel):
    status: Optional[str] = None  # pending, reviewed, accepted, rejected

class CVApplication(CVApplicationBase):
    id: int
    user_id: int
    vacancy_id: int
    cv_file_path: str
    status: str
    applied_at: datetime
    user_name: Optional[str] = None
    vacancy_title: Optional[str] = None

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: UserRole
    user_id: int

class UnifiedToken(BaseModel):
    access_token: str
    token_type: str
    role: str
    entity_type: str
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
    total_publisher_houses: int
    users_by_role: dict
    recent_books: List[Book]
    recent_users: List[User]

class UserManagement(BaseModel):
    user_id: int
    action: str  # "activate", "deactivate", "change_role", "delete"

class PublisherHouseManagement(BaseModel):
    publisher_house_id: int
    action: str  # "verify", "unverify", "activate", "deactivate", "delete"

# OTP schemas
class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    
    @validator('otp')
    def validate_otp(cls, v):
        if not v or len(v) != 6 or not v.isdigit():
            raise ValueError('OTP must be a 6-digit number')
        return v

class OTPResponse(BaseModel):
    message: str
    success: bool
    otp: Optional[str] = None  # For testing only

# Password Reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetUpdate(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class PasswordResetResponse(BaseModel):
    message: str
    success: bool

# Advertisement schemas
class Advertisement(BaseModel):
    id: int
    image_url: str
    status: str  # "pending", "approved", "rejected"
    publisher_house_id: int
    publisher_house_name: Optional[str] = None
    approved_by: Optional[int] = None
    admin_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True 

# User blocking schemas
class UserBlockRequest(BaseModel):
    reason: str

class UserBlockResponse(BaseModel):
    message: str
    user_id: int
    is_blocked: bool
    blocked_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None