#!/usr/bin/env python3
"""
Safe database setup that preserves existing data
"""
import sqlite3
import os

def safe_setup_database():
    """Setup database structure without deleting existing data"""
    db_path = "book_platform.db"
    
    if not os.path.exists(db_path):
        print("Database file not found, creating new one...")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Checking advertisements table structure...")
        
        # Check if advertisements table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='advertisements'")
        if not cursor.fetchone():
            print("Creating advertisements table...")
            cursor.execute("""
                CREATE TABLE advertisements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'pending',
                    publisher_house_id INTEGER NOT NULL,
                    approved_by INTEGER,
                    approved_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (publisher_house_id) REFERENCES publisher_houses(id),
                    FOREIGN KEY (approved_by) REFERENCES admins(id)
                )
            """)
            conn.commit()
            print("Advertisements table created successfully!")
        else:
            print("Advertisements table already exists, checking structure...")
            
            # Check current columns
            cursor.execute("PRAGMA table_info(advertisements)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # Add missing columns if they don't exist
            if 'status' not in columns:
                cursor.execute("ALTER TABLE advertisements ADD COLUMN status VARCHAR DEFAULT 'pending'")
                print("Added status column")
            
            if 'publisher_house_id' not in columns:
                cursor.execute("ALTER TABLE advertisements ADD COLUMN publisher_house_id INTEGER")
                print("Added publisher_house_id column")
            
            if 'approved_by' not in columns:
                cursor.execute("ALTER TABLE advertisements ADD COLUMN approved_by INTEGER")
                print("Added approved_by column")
            
            if 'approved_at' not in columns:
                cursor.execute("ALTER TABLE advertisements ADD COLUMN approved_at DATETIME")
                print("Added approved_at column")
            
            if 'created_at' not in columns:
                cursor.execute("ALTER TABLE advertisements ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("Added created_at column")
            
            # Remove unnecessary columns if they exist (but only if they're not needed)
            unnecessary_columns = ['title', 'description', 'link_url', 'position', 'rejection_reason', 'updated_at']
            for col in unnecessary_columns:
                if col in columns:
                    print(f"Note: Column '{col}' exists but will be ignored (not deleted to preserve data)")
            
            conn.commit()
            print("Database structure updated successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    success = safe_setup_database()
    if success:
        print("✅ Database setup completed successfully!")
    else:
        print("❌ Database setup failed!")
