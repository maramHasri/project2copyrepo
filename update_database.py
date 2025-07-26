#!/usr/bin/env python3
"""
Simple database update script
"""

from models import Base
from database import engine
import sqlite3

def update_database():
    """Update database schema"""
    try:
        # Create all tables (this will add missing columns)
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema updated successfully")
        
        # Check if book_file column exists
        conn = sqlite3.connect('book_platform.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(books)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'book_file' in columns:
            print("✅ book_file column exists in books table")
        else:
            print("❌ book_file column missing from books table")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")

if __name__ == "__main__":
    update_database() 