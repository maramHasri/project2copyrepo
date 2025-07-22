# 🔐 Authentication System Overview

## **🎯 Three Distinct Authentication Systems**

This platform has **three completely separate authentication systems** to ensure proper security and role separation:

---

## **1. 👥 User Authentication (`/auth`)**
**For: Readers and Writers**

### **Token Structure:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "role": "reader|writer",
  "user_id": 123
}
```

### **Endpoints:**
- `POST /register` - User registration
- `POST /login` - General user login
- `POST /login/{role}` - Role-specific login
- `POST /send-otp` - Send OTP email
- `POST /verify-otp` - Verify OTP

### **Permissions:**
- **Readers:** Can read books, save favorites, view publishers and their works
- **Writers:** Can create books, manage their content, view publishers and their works

---

## **2. 🏢 Publisher House Authentication (`/publisher`)**
**For: Publisher Houses**

### **Token Structure:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "publisher_house_id": 456,
  "name": "Publisher Name",
  "email": "publisher@example.com"
}
```

### **Endpoints:**
- `POST /publisher/register` - Publisher registration
- `POST /publisher/login` - Publisher login
- `GET /publisher/me` - Publisher profile
- `POST /publisher/upload-license` - Upload license image
- `POST /publisher/upload-logo` - Upload logo image

### **Permissions:**
- Manage their own books
- Create and manage vacancies
- View writers and their works
- Upload license and logo images

---

## **3. 🔴 Admin Authentication (`/admin`)**
**For: System Administrators**

### **Token Structure:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "role": "super_admin|content_admin|user_admin|publisher_admin",
  "entity_type": "admin",
  "admin_id": 789,
  "username": "admin_username",
  "is_super_admin": true,
  "permissions": {
    "can_manage_users": true,
    "can_manage_publishers": true,
    "can_manage_content": true,
    "can_manage_system": true
  }
}
```

### **Endpoints:**
- `POST /admin/register` - Admin registration (with admin code)
- `POST /admin/login` - Admin login
- `GET /admin/me` - Admin profile
- `GET /admin/` - List all admins (super admin only)
- `PUT /admin/{admin_id}` - Update admin (super admin only)
- `DELETE /admin/{admin_id}` - Delete admin (super admin only)

### **Permissions:**
- **Super Admin:** Full system access
- **Content Admin:** Content moderation only
- **User Admin:** User management only
- **Publisher Admin:** Publisher management only

---

## **4. 🔄 Unified Authentication (`/unified`)**
**For: Users and Publishers ONLY (NO ADMIN)**

### **Token Structure:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "role": "reader|writer|publisher",
  "entity_type": "user|publisher",
  "user_id": 123
}
```

### **Endpoints:**
- `POST /unified/login` - Auto-detect entity type
- `POST /unified/login/user` - User-specific login
- `POST /unified/login/publisher` - Publisher-specific login
- `GET /unified/me` - Get profile (NO ADMIN)
- `GET /unified/debug` - Debug info

### **Purpose:**
- Provides a unified interface for users and publishers
- **Explicitly rejects admin tokens**
- Useful for shared functionality between users and publishers

---

## **🛡️ Security Benefits**

### **✅ Complete Separation:**
- Each entity type has its own authentication system
- No cross-contamination between admin, users, and publishers
- Distinct token structures prevent confusion

### **✅ Role-Based Permissions:**
- Clear permission boundaries
- Admin cannot access user/publisher endpoints
- Users/publishers cannot access admin endpoints

### **✅ Token Validation:**
- Each system validates its own token type
- Unified system explicitly rejects admin tokens
- Proper error messages guide users to correct endpoints

---

## **📋 Usage Examples**

### **For Readers/Writers:**
```bash
# Register as reader
POST /register
{
  "username": "reader1",
  "password": "password123",
  "role": "reader"
}

# Login as reader
POST /login
{
  "username": "reader1",
  "password": "password123"
}
```

### **For Publishers:**
```bash
# Register as publisher
POST /publisher/register
{
  "name": "Great Books Inc",
  "email": "contact@greatbooks.com",
  "password": "password123"
}

# Login as publisher
POST /publisher/login
{
  "email": "contact@greatbooks.com",
  "password": "password123"
}
```

### **For Admins:**
```bash
# Register as admin (requires admin code)
POST /admin/register
{
  "username": "admin1",
  "email": "admin@platform.com",
  "password": "password123",
  "admin_code": "ADMIN2024"
}

# Login as admin
POST /admin/login
{
  "username": "admin1",
  "password": "password123"
}
```

---

## **🎯 Key Points**

1. **Three Separate Systems:** Each entity type has its own authentication
2. **Distinct Tokens:** Different token structures for each system
3. **Clear Permissions:** Well-defined access levels for each role
4. **Security First:** No cross-system authentication allowed
5. **Proper Guidance:** Error messages direct users to correct endpoints

This architecture ensures **maximum security** and **clear role separation** while providing **flexible authentication options** for different user types. 