#!/usr/bin/env python3
"""
Database Rebuild Script
This script will drop the existing database and recreate it with the updated schema.
"""

import os
import sys
from pathlib import Path

# Import required modules at the top level
from database import engine, Base, SessionLocal
from models import User, Category, Admin, AdminRole, PublisherHouse, Book, Vacancy, Comment, Quote, Flash, VacancyAttachment
from security import get_password_hash
from datetime import datetime

def main():
    print("🗄️  Database Rebuild Script")
    print("=" * 50)
    
    # Check if database file exists
    db_path = Path("book_platform.db")
    if db_path.exists():
        print(f"📁 Found existing database: {db_path}")
        
        # Ask for confirmation
        response = input("⚠️  This will DELETE all existing data. Are you sure? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Database rebuild cancelled.")
            return
        
        # Remove existing database
        try:
            os.remove(db_path)
            print("✅ Existing database removed.")
        except Exception as e:
            print(f"❌ Error removing database: {e}")
            return
    else:
        print("📁 No existing database found.")
    
    # Create new database
    try:
        print("🔨 Creating new database...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database created successfully!")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return
    
    # Create some sample data
    try:
        print("🌱 Creating sample data...")
        create_sample_data()
        print("✅ Sample data created successfully!")
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return
    
    print("\n🎉 Database rebuild completed successfully!")
    print("📊 New database structure:")
    print("   - Users table with skills field")
    print("   - Admin table with super admin role")
    print("   - All other tables recreated")
    print("\n🚀 You can now start your application!")

def create_sample_data():
    """Create sample data for testing"""
    db = SessionLocal()
    
    try:
        # Create sample categories
        categories = [
            Category(name="Fiction", description="Fictional literature"),
            Category(name="Non-Fiction", description="Non-fictional literature"),
            Category(name="Science", description="Scientific books"),
            Category(name="History", description="Historical books"),
            Category(name="Technology", description="Technology and programming"),
            Category(name="Philosophy", description="Philosophical works"),
            Category(name="Poetry", description="Poetry and verse"),
            Category(name="Biography", description="Biographical works")
        ]
        
        for category in categories:
            db.add(category)
        db.commit()
        print(f"   ✅ Created {len(categories)} categories")
        
        # Create sample admin
        admin_password = get_password_hash("admin123")
        admin = Admin(
            username="admin",
            email="admin@example.com",
            phone_number="123456789",
            hashed_password=admin_password,
            role=AdminRole.super_admin,
            is_super_admin=True,
            permissions='{"can_manage_users": true, "can_manage_publishers": true, "can_manage_content": true, "can_manage_system": true}',
            can_manage_users=True,
            can_manage_publishers=True,
            can_manage_content=True,
            can_manage_system=True
        )
        db.add(admin)
        db.commit()
        print("   ✅ Created admin user (username: admin, password: admin123)")
        
        # Create sample users
        users = [
            User(
                username="reader1",
                phone_number="111111111",
                email="reader1@example.com",
                hashed_password=get_password_hash("password123"),
                role="reader",
                bio="I love reading books",
                skills='["تحرير نصوص", "مراجعة لغوية"]'
            ),
            User(
                username="writer1",
                phone_number="222222222",
                email="writer1@example.com",
                hashed_password=get_password_hash("password123"),
                role="writer",
                bio="Professional writer",
                writer_bio="I write fiction and non-fiction",
                skills='["كتابة المحتوى", "تحرير محتوى رقمي", "Photoshop"]'
            )
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        print(f"   ✅ Created {len(users)} sample users")
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
