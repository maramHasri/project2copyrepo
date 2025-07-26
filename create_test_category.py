#!/usr/bin/env python3
"""
Script to create a test category for book creation testing
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Category

def create_test_category():
    """Create a test category in the database"""
    
    # Create engine
    engine = create_engine("sqlite:///./book_platform.db")
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if test category already exists
        existing_category = db.query(Category).filter(
            Category.name == "Test Category"
        ).first()
        
        if existing_category:
            print("✅ Test category already exists")
            print(f"ID: {existing_category.id}")
            print(f"Name: {existing_category.name}")
            return
        
        # Create test category
        test_category = Category(
            name="Test Category",
            description="A test category for book creation"
        )
        
        db.add(test_category)
        db.commit()
        db.refresh(test_category)
        
        print("✅ Test category created successfully!")
        print(f"ID: {test_category.id}")
        print(f"Name: {test_category.name}")
        
    except Exception as e:
        print(f"❌ Error creating test category: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_category() 