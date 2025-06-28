# Deployment Guide for Render

## Changes Made for Render Deployment

### 1. Updated Requirements
- Changed `passlib[bcrypt]` to `passlib[argon2]` to avoid Rust compilation issues
- Updated `uvicorn` to `uvicorn[standard]` for better performance
- All other dependencies remain the same

### 2. Database Configuration
- Updated `database.py` to support both SQLite (development) and PostgreSQL (production)
- Automatically handles Render's PostgreSQL URL format

### 3. Added Configuration Files
- `runtime.txt`: Specifies Python 3.11.7
- `render.yaml`: Render deployment configuration

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

1. **File Uploads**: The `uploads` directory will be ephemeral on Render. Consider using cloud storage (AWS S3, Cloudinary) for production.

2. **Database Migrations**: If you have existing data, you'll need to run Alembic migrations:
   ```bash
   alembic upgrade head
   ```

3. **Environment Variables**: Make sure to set all required environment variables in Render dashboard.

4. **CORS**: The current CORS configuration allows all origins (`"*"`). For production, specify your frontend domain.

## Troubleshooting

- If you get Rust-related errors, the updated requirements should fix this
- If database connection fails, check the `DATABASE_URL` format
- If the app doesn't start, check the logs in Render dashboard 