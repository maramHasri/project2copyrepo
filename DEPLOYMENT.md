# Deployment Guide for Render

## Changes Made for Render Deployment

### 1. Updated Requirements
- Changed `passlib[bcrypt]` to `passlib[argon2]` to avoid Rust compilation issues
- Removed `[cryptography]` from `python-jose` to use pure Python implementation
- Updated `uvicorn` to `uvicorn[standard]` for better performance
- All other dependencies remain the same

### 2. Updated Code Files
- **`security.py`**: Changed password hashing from `bcrypt` to `argon2`
- **`auth.py`**: Changed password hashing from `bcrypt` to `argon2`
- **`database.py`**: Updated to support both SQLite (development) and PostgreSQL (production)

### 3. Added Configuration Files
- `runtime.txt`: Specifies Python 3.11.7
- `render.yaml`: Render deployment configuration

## Why These Changes Fix the Rust Issue

The original error was caused by:
1. `passlib[bcrypt]` requiring Rust to compile bcrypt
2. `python-jose[cryptography]` requiring Rust for cryptographic operations
3. Code still using bcrypt even after changing requirements

**Solution**: 
- Use `passlib[argon2]` instead of bcrypt (Argon2 is more secure and doesn't need Rust)
- Use pure Python `python-jose` without cryptography extras
- Update all code to use argon2 instead of bcrypt

## Deployment Steps

### 1. Create a Render Account
- Go to [render.com](https://render.com) and create an account
- Connect your GitHub repository

### 2. Create a New Web Service
- Click "New +" → "Web Service"
- Connect your repository
- Render will automatically detect it's a Python app

### 3. Configure Environment Variables
In Render dashboard, add these environment variables:

```
DATABASE_URL=postgresql://username:password@host:port/database_name
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
```

### 4. Database Setup
- Create a PostgreSQL database in Render
- Copy the database URL to the `DATABASE_URL` environment variable
- The app will automatically create tables on first run

### 5. Build and Deploy
- Render will automatically:
  - Install dependencies from `requirements.txt`
  - Use Python 3.11.7 (specified in `runtime.txt`)
  - Start the app with `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Important Notes

1. **Password Migration**: If you have existing users with bcrypt hashed passwords, they will need to reset their passwords since we switched to argon2.

2. **File Uploads**: The `uploads` directory will be ephemeral on Render. Consider using cloud storage (AWS S3, Cloudinary) for production.

3. **Database Migrations**: If you have existing data, you'll need to run Alembic migrations:
   ```bash
   alembic upgrade head
   ```

4. **Environment Variables**: Make sure to set all required environment variables in Render dashboard.

5. **CORS**: The current CORS configuration allows all origins (`"*"`). For production, specify your frontend domain.

## Troubleshooting

- ✅ **Rust errors fixed**: The updated requirements and code changes eliminate all Rust dependencies
- If database connection fails, check the `DATABASE_URL` format
- If the app doesn't start, check the logs in Render dashboard
- If users can't login, they may need to reset passwords due to the hashing algorithm change 