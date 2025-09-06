#!/usr/bin/env python3
"""
Verify database structure and add missing columns if needed
"""
import sqlite3
import os
from sqlalchemy import text

def verify_database():
    """Verify and fix database structure"""
    db_path = "book_platform.db"
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Checking database structure...")
        
        # Check if books table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
        if not cursor.fetchone():
            print("Books table not found!")
            return False
        
        # Check books table columns
        cursor.execute("PRAGMA table_info(books)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 Books table columns: {columns}")
        
        # Check for blocking columns
        missing_columns = []
        if 'is_blocked' not in columns:
            missing_columns.append('is_blocked')
        if 'blocked_reason' not in columns:
            missing_columns.append('blocked_reason')
        if 'blocked_at' not in columns:
            missing_columns.append('blocked_at')
        
        if missing_columns:
            print(f"Missing columns: {missing_columns}")
            print("Adding missing columns...")
            
            if 'is_blocked' in missing_columns:
                cursor.execute("ALTER TABLE books ADD COLUMN is_blocked BOOLEAN DEFAULT 0")
                print("Added is_blocked column")
            
            if 'blocked_reason' in missing_columns:
                cursor.execute("ALTER TABLE books ADD COLUMN blocked_reason TEXT")
                print("Added blocked_reason column")
            
            if 'blocked_at' in missing_columns:
                cursor.execute("ALTER TABLE books ADD COLUMN blocked_at DATETIME")
                print("Added blocked_at column")
            
            conn.commit()
            print("All missing columns added successfully!")
        else:
            print("All blocking columns exist!")
        
        # Check reports table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
        if not cursor.fetchone():
            print("Creating reports table...")
            cursor.execute("""
                CREATE TABLE reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    admin_id INTEGER,
                    admin_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (book_id) REFERENCES books (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (admin_id) REFERENCES admins (id)
                )
            """)
            conn.commit()
            print("Reports table created!")
        else:
            print("Reports table exists!")
        
        conn.close()
        print("Database verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error verifying database: {e}")
        return False

if __name__ == "__main__":
    print("Starting database verification...")
    success = verify_database()
    if success:
        print("Database is ready!")
    else:
        print("Database verification failed!")
