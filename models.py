from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import enum
# Association tables
user_interests = Table(
    'user_interests',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class UserRole(str, enum.Enum):
    reader = "reader"
    writer = "writer"
    publisher = "publisher"
    admin = "admin"

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
    full_name = Column(String, nullable=True)
    phone_number = Column(String, unique=True)
    
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.reader)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_image = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    social_links = Column(String, nullable=True)
    
    
    # Relationships
    interests = relationship("Category", secondary=user_interests, back_populates="interested_users")
    books = relationship("Book", back_populates="author")
    liked_books = relationship("Book", secondary="user_liked_books", back_populates="liked_by")
    saved_books = relationship("Book", secondary="user_saved_books", back_populates="saved_by")
    comments = relationship("Comment", back_populates="user")
    quotes = relationship("Quote", back_populates="author")
    publisher = relationship("Publisher", back_populates="user", uselist=False)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    books = relationship("Book", secondary=book_categories, back_populates="categories")
    interested_users = relationship("User", secondary=user_interests, back_populates="interests")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    is_free = Column(Boolean, default=False)
    price = Column(Float, nullable=True)
    cover_url = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    publisher_id = Column(Integer, ForeignKey("publishers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    author = relationship("User", back_populates="books")
    publisher = relationship("Publisher", back_populates="books")
    categories = relationship("Category", secondary=book_categories, back_populates="books")
    liked_by = relationship("User", secondary="user_liked_books", back_populates="liked_books")
    saved_by = relationship("User", secondary="user_saved_books", back_populates="saved_books")
    comments = relationship("Comment", back_populates="book")
    quotes = relationship("Quote", back_populates="book")

class Publisher(Base):
    __tablename__ = "publishers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    logo = Column(String, nullable=True)
    foundation_date = Column(DateTime(timezone=True))
    address = Column(Text, nullable=True)
    contact_info = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="publisher")
    books = relationship("Book", back_populates="publisher")
    vacancies = relationship("Vacancy", back_populates="publisher")
    featured_writers = relationship("User", secondary="publisher_featured_writers")

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    book_id = Column(Integer, ForeignKey("books.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    number_of_likes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="quotes")
    author = relationship("User", back_populates="quotes")

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
    publisher_id = Column(Integer, ForeignKey("publishers.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    publisher = relationship("Publisher", back_populates="vacancies")
    attachments = relationship("VacancyAttachment", back_populates="vacancy")

class VacancyAttachment(Base):
    __tablename__ = "vacancy_attachments"

    id = Column(Integer, primary_key=True, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"))
    attachment_url = Column(String)
    attachment_type = Column(String)  # e.g., "google_form", "pdf", etc.
    
    # Relationships
    vacancy = relationship("Vacancy", back_populates="attachments")

# Association tables for many-to-many relationships
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
    Column('publisher_id', Integer, ForeignKey('publishers.id')),
    Column('writer_id', Integer, ForeignKey('users.id'))
) 