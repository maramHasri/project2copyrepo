from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from routers import auth, users, books, categories, quotes, publishers, vacancies, admin
from database import engine
from models import Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Book Platform API",
    description="A FastAPI-based backend for a book platform with Bearer token authentication and file uploads",
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
        "/register/publisher",
        "/register/admin",
        "/login",
        "/login/reader",
        "/login/writer",
        "/login/publisher",
        "/login/admin",
        "/books/",
        "/books/{title}",
        "/categories/",
        "/categories/{category_id}",
        "/publishers/",
        "/publishers/{publisher_id}"
    }
    
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # Skip public paths
                if path not in public_paths:
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
    allow_headers=["*"],
)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])
app.include_router(publishers.router, prefix="/publishers", tags=["Publishers"])
app.include_router(vacancies.router, prefix="/vacancies", tags=["Vacancies"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Book Platform API",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": [
            "Role-based authentication (Reader, Writer, Publisher, Admin)",
            "Separate registration and login for each role",
            "File upload support",
            "Admin dashboard and user management",
            "Book and category management",
            "Publisher management"
        ]
    } 