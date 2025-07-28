from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from routers import auth, users, books, categories, quotes, flashes, admin_auth, publisher_auth, publisher_vacancies
from database import engine
from models import Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Book Platform API",
    description="fikr project swagger ",
    version="1.0.0"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token here. You can get it from the /login endpoint."
        }
    }
    
    # Add security requirement to all endpoints that need authentication
    # Define public paths that don't need authentication
    public_paths = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/register",
        "/register/reader",
        "/register/writer", 
        "/login",
        "/login/reader",
        "/login/writer",
        "/admin/register",
        "/admin/login",
        "/send-otp",
        "/verify-otp",
        "/publisher/register",
        "/publisher/login",
        "/books/",
        "/books/{title}",
    }
    
    # Define public GET paths (read-only endpoints that don't need auth)
    public_get_paths = {
        "/categories/",
        "/categories/{category_id}"
    }
    
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # Skip completely public paths
                if path in public_paths:
                    continue
                
                # Skip GET requests for public read-only paths
                if method.lower() == "get" and path in public_get_paths:
                    continue
                
                # Add security requirement for all other endpoints
                if "security" not in openapi_schema["paths"][path][method]:
                    openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type"],
)

# Mount static files for serving uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, tags=["Authentication"])

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])
app.include_router(flashes.router, prefix="/flashes", tags=["Flashes"])

app.include_router(admin_auth.router, prefix="/admin", tags=["Admin Authentication"])
app.include_router(publisher_auth.router, prefix="/publisher", tags=["Publisher House"])
app.include_router(publisher_vacancies.router, prefix="/publisher/vacancies", tags=["Publisher Vacancies"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Book Platform API",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": [
            "Role-based authentication (Reader, Writer, Admin)",
            "Publisher house platform",
            "File upload support",
            "Admin dashboard and user management",
            "Book and category management",
            "Publisher house management"
        ]
    } 