#!/usr/bin/env python3
"""
Database Clear Script
This script clears all data from the database while keeping the structure.
"""

from database import engine, Base
from sqlalchemy import text

def clear_database():
    """Clear all data from the database"""
    print("🗑️  Database Clear Script")
    print("=" * 40)
    
    # Get confirmation
    response = input("⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Database clear cancelled.")
        return
    
    try:
        with engine.connect() as conn:
            # Disable foreign key constraints temporarily
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result if row[0] != 'sqlite_sequence']
            
            print(f"📋 Found {len(tables)} tables to clear")
            
            # Clear each table
            for table in tables:
                conn.execute(text(f"DELETE FROM {table}"))
                print(f"   ✅ Cleared table: {table}")
            
            # Reset auto-increment counters
            conn.execute(text("DELETE FROM sqlite_sequence"))
            
            # Re-enable foreign key constraints
            conn.execute(text("PRAGMA foreign_keys=ON"))
            
            conn.commit()
            
        print("\n✅ Database cleared successfully!")
        print("💡 You can now run 'python seed_database.py' to populate with sample data")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

if __name__ == "__main__":
    clear_database()
