#!/usr/bin/env python3
"""
Database Seeding Script
This script populates the database with sample data for testing and development.
"""

import json
from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import (
    User, Category, Admin, AdminRole, PublisherHouse, 
    Book, Vacancy, Comment, Quote, Flash, VacancyAttachment
)
from security import get_password_hash
from sqlalchemy.orm import Session

def seed_database():
    """Seed the database with sample data"""
    print("🌱 Starting database seeding...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        # if db.query(User).count() > 0:
        #     print("⚠️  Database already has data. Skipping seeding.")
        #     return
        
        print("📚 Creating categories...")
        categories = create_categories(db)
        
        print("👤 Creating admin users...")
        admins = create_admins(db)
        
        print("🏢 Creating publisher houses...")
        publishers = create_publishers(db)
        
        print("👥 Creating users...")
        users = create_users(db)
        
        print("📖 Creating books...")
        books = create_books(db, users, publishers, categories)
        
        print("💼 Creating vacancies...")
        create_vacancies(db, publishers)
        
        print("💬 Creating comments...")
        create_comments(db, users, books)
        
        print("💭 Creating quotes...")
        if db.query(Quote).count() == 0:
            create_quotes(db, users, books)
        else:
            print("   ✅ Quotes already exist, skipping...")
        
        print("⚡ Creating flashes...")
        create_flashes(db, users)
        
        print("✅ Database seeding completed successfully!")
        print(f"📊 Created: {len(categories)} categories, {len(admins)} admins, {len(publishers)} publishers, {len(users)} users, {len(books)} books")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_categories(db: Session):
    """Create sample categories"""
    categories = [
        Category(name="Fiction", description="Fictional literature and novels"),
        Category(name="Non-Fiction", description="Non-fictional literature"),
        Category(name="Science", description="Scientific books and research"),
        Category(name="History", description="Historical books and documents"),
        Category(name="Technology", description="Technology and programming books"),
        Category(name="Philosophy", description="Philosophical works and theories"),
        Category(name="Poetry", description="Poetry and verse collections"),
        Category(name="Biography", description="Biographical works and memoirs"),
        Category(name="Business", description="Business and management books"),
        Category(name="Art", description="Art and design books"),
        Category(name="Literature", description="Classic literature"),
        Category(name="Children", description="Children's books and stories")
    ]
    
    for category in categories:
        db.add(category)
    db.commit()
    
    return categories

def create_admins(db: Session):
    """Create sample admin users"""
    admins = [
        Admin(
            username="admin",
            email="admin@example.com",
            phone_number="123456789",
            hashed_password=get_password_hash("admin123"),
            role=AdminRole.super_admin,
            is_super_admin=True
        ),
        Admin(
            username="superadmin",
            email="super@example.com",
            phone_number="987654321",
            hashed_password=get_password_hash("super123"),
            role=AdminRole.super_admin,
            is_super_admin=True
        )
    ]
    
    for admin in admins:
        db.add(admin)
    db.commit()
    
    return admins

def create_publishers(db: Session):
    """Create sample publisher houses"""
    publishers = [
        PublisherHouse(
            name="دار النشر العربية",
            email="info@arabic-pub.com",
            hashed_password=get_password_hash("publisher123"),
            license_image="uploads/publisher_licenses/license_1_20250719_211609_ChatGPT Image Jul 19, 2025, 08_40_33 PM.png",
            logo_image="uploads/publisher_logos/logo_1_20250719_211634_ChatGPT Image Jul 19, 2025, 08_40_33 PM.png",
            is_active=True,
            is_verified=True,
            address="شارع النشر، القاهرة، مصر",
            contact_info="+20 123 456 789",
            foundation_date=datetime(2010, 1, 1)
        ),
        PublisherHouse(
            name="مطبعة المعرفة",
            email="info@maarifa-press.com",
            hashed_password=get_password_hash("publisher123"),
            license_image="uploads/publisher_licenses/license_9_20250721_022645_be9e4c1c-ce3a-4737-a60c-81f6e3089c70.jpeg",
            logo_image="uploads/publisher_logos/logo_9_20250721_022705_bdd668f3-97f4-40bd-9c9c-e10ba1f7f458.jpeg",
            is_active=True,
            is_verified=True,
            address="شارع المعرفة، الرياض، السعودية",
            contact_info="+966 123 456 789",
            foundation_date=datetime(2015, 6, 15)
        )
    ]
    
    for publisher in publishers:
        db.add(publisher)
    db.commit()
    
    return publishers

def create_users(db: Session):
    """Create sample users"""
    users = [
        User(
            username="reader1",
            phone_number="111111111",
            email="reader1@example.com",
            hashed_password=get_password_hash("password123"),
            role="reader",
            bio="I love reading books, especially fiction and science fiction",
            skills=json.dumps(["تحرير نصوص", "مراجعة لغوية", "كتابة المحتوى"])
        ),
        User(
            username="reader2",
            phone_number="222222222",
            email="reader2@example.com",
            hashed_password=get_password_hash("password123"),
            role="reader",
            bio="Passionate about history and philosophy books",
            skills=json.dumps(["مراجعة علمية", "تحرير محتوى رقمي"])
        ),
        User(
            username="writer1",
            phone_number="333333333",
            email="writer1@example.com",
            hashed_password=get_password_hash("password123"),
            role="writer",
            bio="Professional writer specializing in fiction and poetry",
            writer_bio="I have published over 20 books and won several literary awards",
            published_books_count=25,
            is_featured_writer=True,
            skills=json.dumps(["كتابة المحتوى", "تحرير محتوى رقمي", "Photoshop", "تصميم غلاف"])
        ),
        User(
            username="writer2",
            phone_number="444444444",
            email="writer2@example.com",
            hashed_password=get_password_hash("password123"),
            role="writer",
            bio="Technical writer and researcher",
            writer_bio="Specializing in science and technology documentation",
            published_books_count=15,
            skills=json.dumps(["كتابة المحتوى", "مراجعة علمية", "إدارة المشروعات"])
        ),
        User(
            username="designer1",
            phone_number="555555555",
            email="designer@example.com",
            hashed_password=get_password_hash("password123"),
            role="writer",
            bio="Graphic designer and book illustrator",
            writer_bio="Creating beautiful book covers and illustrations for over 10 years",
            published_books_count=8,
            skills=json.dumps(["تصميم غلاف", "تصميم داخلي للكتاب", "Photoshop", "Illustrator", "رسم توضيحي"])
        )
    ]
    
    for user in users:
        db.add(user)
    db.commit()
    
    return users

def create_books(db: Session, users, publishers, categories):
    """Create sample books"""
    books = [
        Book(
            title="رحلة في عالم الخيال",
            description="رواية خيالية تأخذ القارئ في رحلة عبر عوالم مختلفة",
            is_free=False,
            price=25.99,
            cover_image="uploads/images/book_covers/book_cover_1_20250726_123549_fc8a97b2.jpeg",
            book_file="uploads/books/book_1_20250726_123549_a8c3e8de.pdf",
            author_name="أحمد الخيالي",
            author_id=users[2].id,  # writer1
            publisher_house_id=publishers[0].id
        ),
        Book(
            title="أسرار الكون",
            description="كتاب علمي يشرح أسرار الكون والفضاء",
            is_free=True,
            cover_image="uploads/images/book_covers/book_cover_2_20250726_123950_af213ffd.jpeg",
            book_file="uploads/books/book_2_20250726_123950_62415ffd.pdf",
            author_name="د. سارة العلمية",
            author_id=users[3].id,  # writer2
            publisher_house_id=publishers[1].id
        ),
        Book(
            title="قصائد من القلب",
            description="مجموعة شعرية تعبر عن مشاعر الحب والحياة",
            is_free=False,
            price=15.99,
            cover_image="uploads/images/book_covers/book_cover_3_20250726_124204_44a222e7.jpeg",
            book_file="uploads/books/book_3_20250726_124204_be3fa957.pdf",
            author_name="فاطمة الشاعرة",
            author_id=users[2].id,  # writer1
            publisher_house_id=publishers[0].id
        ),
        Book(
            title="تاريخ الحضارات",
            description="كتاب تاريخي يغطي أهم الحضارات في التاريخ",
            is_free=False,
            price=30.99,
            cover_image="uploads/images/book_covers/book_cover_4_20250726_124220_70a03636.jpeg",
            book_file="uploads/books/book_4_20250726_124220_ea8252a0.pdf",
            author_name="محمد المؤرخ",
            author_id=users[3].id,  # writer2
            publisher_house_id=publishers[1].id
        )
    ]
    
    for book in books:
        db.add(book)
    db.commit()
    
    # Add categories to books
    books[0].categories = [categories[0], categories[10]]  # Fiction, Literature
    books[1].categories = [categories[2], categories[4]]   # Science, Technology
    books[2].categories = [categories[6], categories[10]]  # Poetry, Literature
    books[3].categories = [categories[3], categories[1]]   # History, Non-Fiction
    
    db.commit()
    
    return books

def create_vacancies(db: Session, publishers):
    """Create sample job vacancies"""
    vacancies = [
        Vacancy(
            title="مصمم غرافيك",
            description="نبحث عن مصمم غرافيك موهوب لتصميم أغلفة الكتب والمواد التسويقية",
            requirements="خبرة في Photoshop و Illustrator، إبداع في التصميم",
            publisher_house_id=publishers[0].id,
            is_active=True
        ),
        Vacancy(
            title="محرر محتوى",
            description="محرر محتوى لمراجعة وتحرير الكتب قبل النشر",
            requirements="خبرة في التحرير، معرفة جيدة باللغة العربية",
            publisher_house_id=publishers[1].id,
            is_active=True
        ),
        Vacancy(
            title="مدير تسويق",
            description="مدير تسويق لإدارة الحملات الإعلانية والتسويق الرقمي",
            requirements="خبرة في التسويق الرقمي، إدارة منصات التواصل الاجتماعي",
            publisher_house_id=publishers[0].id,
            is_active=False
        )
    ]
    
    for vacancy in vacancies:
        db.add(vacancy)
    db.commit()
    
    # Add attachments to vacancies
    attachments = [
        VacancyAttachment(
            vacancy_id=vacancies[0].id,
            attachment_url="https://forms.google.com/example1",
            attachment_type="google_form"
        ),
        VacancyAttachment(
            vacancy_id=vacancies[1].id,
            attachment_url="https://forms.google.com/example2",
            attachment_type="google_form"
        )
    ]
    
    for attachment in attachments:
        db.add(attachment)
    db.commit()

def create_comments(db: Session, users, books):
    """Create sample comments on books"""
    comments = [
        Comment(
            text="كتاب رائع! أسلوب الكتابة ممتع جداً",
            book_id=books[0].id,
            user_id=users[0].id
        ),
        Comment(
            text="محتوى علمي مفيد ومكتوب بأسلوب بسيط",
            book_id=books[1].id,
            user_id=users[1].id
        ),
        Comment(
            text="قصائد جميلة تعبر عن المشاعر الإنسانية",
            book_id=books[2].id,
            user_id=users[0].id
        )
    ]
    
    for comment in comments:
        db.add(comment)
    db.commit()

def create_quotes(db: Session, users, books):
    """Create sample quotes from books"""
    quotes = [
        Quote(
            text="الخيال هو البوابة إلى عالم لا حدود له",
            book_name=books[0].title,  # Changed from book_id to book_name
            author_id=users[2].id,
            number_of_likes=15
        ),
        Quote(
            text="العلم نور والجهل ظلام",
            book_name=books[1].title,  # Changed from book_id to book_name
            author_id=users[3].id,
            number_of_likes=23
        ),
        Quote(
            text="الشعر هو لغة الروح",
            book_name=books[2].title,  # Changed from book_id to book_name
            author_id=users[2].id,
            number_of_likes=18
        )
    ]
    
    for quote in quotes:
        db.add(quote)
    db.commit()

def create_flashes(db: Session, users):
    """Create sample flash posts"""
    flashes = [
        Flash(
            text="أفكار جديدة لكتابي القادم تتدفق في ذهني!",
            author_id=users[2].id,
            author_name="أحمد الخيالي",
            number_of_likes=12
        ),
        Flash(
            text="انتهيت من تصميم غلاف كتاب جديد، أتمنى أن يعجبكم!",
            author_id=users[4].id,
            author_name="مصمم الكتب",
            number_of_likes=8
        ),
        Flash(
            text="قرأت اليوم كتاباً رائعاً عن الفلسفة، أنصح الجميع بقراءته",
            author_id=users[0].id,
            author_name="قارئ شغوف",
            number_of_likes=5
        )
    ]
    
    for flash in flashes:
        db.add(flash)
    db.commit()

if __name__ == "__main__":
    seed_database()
    print("\n🎉 Seeding completed! You can now test your application.")
    print("\n📋 Sample Login Credentials:")
    print("👤 Admin: admin@example.com / admin123")
    print("👤 Super Admin: super@example.com / super123")
    print("👥 Reader: reader1@example.com / password123")
    print("✍️ Writer: writer1@example.com / password123")
    print("🏢 Publisher: info@arabic-pub.com / publisher123")
