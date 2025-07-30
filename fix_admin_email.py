import sqlite3

# Connect to database
conn = sqlite3.connect('book_platform.db')
cursor = conn.cursor()

# Fix invalid admin email
cursor.execute("UPDATE admins SET email = 'admin@gmail.com' WHERE id = 2")

conn.commit()
print("✅ Fixed admin email: admin@gmail,com → admin@gmail.com")

# Verify the fix
cursor.execute("SELECT id, username, email FROM admins WHERE id = 2")
row = cursor.fetchone()
print(f"📋 Updated admin: ID: {row[0]}, Username: {row[1]}, Email: {row[2]}")

conn.close()
print("✅ Database update completed!") 