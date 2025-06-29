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

# Deployment Guide - Fixing 502 Errors

## Common 502 Error Causes and Solutions

### 1. Host Configuration Issue ✅ FIXED
**Problem**: Using `127.0.0.1` (localhost only) prevents external connections
**Solution**: Use `0.0.0.0` to accept connections from any IP address

### 2. Port Configuration Issue ✅ FIXED
**Problem**: Hardcoded port doesn't work with Render's dynamic port assignment
**Solution**: Use `$PORT` environment variable

### 3. Missing Dependencies ✅ FIXED
**Problem**: Production dependencies missing
**Solution**: Added `gunicorn` and proper uvicorn configuration

## Files Modified for Deployment

### `run.py` - Development Server
```python
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
```

### `start.py` - Production Server (NEW)
```python
import os
import uvicorn
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        workers=1,     # Single worker for Render
        log_level="info"
    )
```

### `render.yaml` - Render Configuration
```yaml
services:
  - type: web
    name: book-platform-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python start.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.7
      - key: PORT
        value: 8000
```

## Deployment Steps

1. **Commit and Push Changes**
   ```bash
   git add .
   git commit -m "Fix 502 error: Update host and port configuration"
   git push origin main
   ```

2. **Render Deployment**
   - Render will automatically detect the `render.yaml` file
   - The service will use `python start.py` as the start command
   - Port will be automatically assigned via `$PORT` environment variable

3. **Environment Variables** (if needed)
   - Add any additional environment variables in Render dashboard
   - Database URL, API keys, etc.

## Testing Deployment

1. **Check Render Logs**
   - Go to your service in Render dashboard
   - Check "Logs" tab for any errors

2. **Test Endpoints**
   - Try accessing your API root: `https://your-app.onrender.com/`
   - Check docs: `https://your-app.onrender.com/docs`

## Common Issues and Solutions

### Still Getting 502?
1. **Check Render Logs**: Look for specific error messages
2. **Database Connection**: Ensure database URL is correct
3. **Dependencies**: Verify all packages are installed
4. **Startup Time**: Render has a 30-second startup limit

### Database Issues
- If using SQLite locally, consider switching to PostgreSQL for production
- Add `DATABASE_URL` environment variable in Render

### Memory Issues
- Reduce workers to 1 (already done)
- Optimize imports and reduce memory usage

## Local Testing

Test the production configuration locally:
```bash
# Set PORT environment variable
set PORT=8000  # Windows
export PORT=8000  # Linux/Mac

# Run production server
python start.py
```

Your API should now be accessible at `http://localhost:8000` 