from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import enum

# broken table user\book
user_interests = Table(
    'user_interests',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class UserRole(str, enum.Enum):
    reader = "reader"
    writer = "writer"


class AdminRole(str, enum.Enum):
    super_admin = "super_admin"     

book_categories = Table(
    'book_categories',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True)
    email = Column(String, unique=True, nullable=True)
    
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.reader)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verification
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_image = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    social_links = Column(String, nullable=True)
    
    # Skills field - JSON string of user skills
    skills = Column(Text, nullable=True)  # JSON string of selected skills
    
    # Writer fields
    writer_bio = Column(Text, nullable=True)
    published_books_count = Column(Integer, default=0)
    is_featured_writer = Column(Boolean, default=False)
    

    interests = relationship("Category", secondary=user_interests, back_populates="interested_users")
    books = relationship("Book", back_populates="author")
    liked_books = relationship("Book", secondary="user_liked_books", back_populates="liked_by")
    saved_books = relationship("Book", secondary="user_saved_books", back_populates="saved_by")
    comments = relationship("Comment", back_populates="user")
    quotes = relationship("Quote", back_populates="author")
    flashes = relationship("Flash", back_populates="author")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, nullable=True)
    
    hashed_password = Column(String)
    role = Column(Enum(AdminRole), default=AdminRole.super_admin) 
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=True)  # Always true for all admins
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    admin_actions = relationship("AdminAction", back_populates="admin")

class AdminAction(Base):
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"))
    action_type = Column(String)  
    action_description = Column(Text)
    target_entity_type = Column(String)  
    target_entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    admin = relationship("Admin", back_populates="admin_actions")
#publisher house
class PublisherHouse(Base):
    __tablename__ = "publisher_houses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    license_image = Column(String, nullable=True)  
    logo_image = Column(String, nullable=True)    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)   
    created_at = Column(DateTime, default=datetime.utcnow)
    address = Column(Text, nullable=True)
    contact_info = Column(Text, nullable=True)
    foundation_date = Column(DateTime, nullable=True)
    # book
    books = relationship("Book", back_populates="publisher_house")
    vacancies = relationship("Vacancy", back_populates="publisher_house")
    featured_writers = relationship("User", secondary="publisher_featured_writers")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    
    books = relationship("Book", secondary=book_categories, back_populates="categories")
    interested_users = relationship("User", secondary=user_interests, back_populates="interests")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    is_free = Column(Boolean, default=False)
    price = Column(Float, nullable=True)
    cover_image = Column(String, nullable=True) 
    book_file = Column(String, unique=True, nullable=False)  #  file (PDF only)
    author_name = Column(String, nullable=True)  # Author name 
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    publisher_house_id = Column(Integer, ForeignKey("publisher_houses.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    author = relationship("User", back_populates="books")
    publisher_house = relationship("PublisherHouse", back_populates="books")
    categories = relationship("Category", secondary=book_categories, back_populates="books")
    liked_by = relationship("User", secondary="user_liked_books", back_populates="liked_books")
    saved_by = relationship("User", secondary="user_saved_books", back_populates="saved_books")
    comments = relationship("Comment", back_populates="book")
    # Removed quotes relationship since Quote now uses book_name string

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    book_name = Column(String, index=True)  # Changed from book_id to book_name
    author_id = Column(Integer, ForeignKey("users.id"))
    number_of_likes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    author = relationship("User", back_populates="quotes")
    # Removed book relationship since we're using book_name string instead of foreign key

class Flash(Base):
    __tablename__ = "flashes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_name = Column(String, nullable=False)  # Writer's name
    number_of_likes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    author = relationship("User", back_populates="flashes")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="comments")
    user = relationship("User", back_populates="comments")

class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    position = Column(String, index=True)  # Added missing position field
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    publisher_house_id = Column(Integer, ForeignKey("publisher_houses.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    publisher_house = relationship("PublisherHouse", back_populates="vacancies")
    attachments = relationship("VacancyAttachment", back_populates="vacancy")

class VacancyAttachment(Base):
    __tablename__ = "vacancy_attachments"

    id = Column(Integer, primary_key=True, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"))
    attachment_url = Column(String)
    attachment_type = Column(String)  # e.g., "google_form", "pdf", etc.
    
    vacancy = relationship("Vacancy", back_populates="attachments")


user_liked_books = Table(
    'user_liked_books',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id'))
)

user_saved_books = Table(
    'user_saved_books',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id'))
)

publisher_featured_writers = Table(
    'publisher_featured_writers',
    Base.metadata,
    Column('publisher_house_id', Integer, ForeignKey('publisher_houses.id')),
    Column('writer_id', Integer, ForeignKey('users.id'))
) 

 