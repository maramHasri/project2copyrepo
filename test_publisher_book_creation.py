#!/usr/bin/env python3
"""
Test script to verify publisher can create books with unified authentication
"""

import requests
import json

def test_publisher_book_creation():
    """Test publisher book creation with unified authentication"""
    
    # Step 1: Login as publisher
    login_data = {
        "email": "test@publisher.com",
        "password": "testpassword123"
    }
    
    base_url = "http://localhost:8000"
    
    try:
        # Login
        login_response = requests.post(
            f"{base_url}/publisher/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        print(f"✅ Login successful! Token: {access_token[:20]}...")
        
        # Step 2: Create a book using publisher token
        book_data = {
            "title": "Test Book by Publisher",
            "description": "A test book created by publisher",
            "is_free": True,
            "category_ids": "1",  # Assuming category 1 exists
            "author_name": "John Doe"  # Publisher must provide author name
        }
        
        # Create a simple text file for testing
        files = {
            "book_file": ("test_book.pdf", b"dummy pdf content", "application/pdf"),
            "title": (None, book_data["title"]),
            "description": (None, book_data["description"]),
            "is_free": (None, str(book_data["is_free"]).lower()),
            "category_ids": (None, book_data["category_ids"]),
            "author_name": (None, book_data["author_name"])
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        book_response = requests.post(
            f"{base_url}/books/with-file",
            files=files,
            headers=headers
        )
        
        print(f"Book creation status: {book_response.status_code}")
        
        if book_response.status_code == 200:
            book_data = book_response.json()
            print("✅ Book created successfully!")
            print(f"Book ID: {book_data.get('id')}")
            print(f"Title: {book_data.get('title')}")
            print(f"Author Name: {book_data.get('author_name')}")
            print(f"Publisher House ID: {book_data.get('publisher_house_id')}")
        else:
            print(f"❌ Book creation failed: {book_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_publisher_book_creation() 