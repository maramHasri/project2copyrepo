from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from routers import auth, users, books, categories, quotes, flashes, admin_auth, publisher_auth, publisher_vacancies
from database import engine
from models import Base
import os

# Create database 
Base.metadata.create_all(bind=engine)

# Create uploads folder
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
    
    #   token security in swagger
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token here. You can get it from the /login endpoint."
        }
    }
    
    # Ensure proper multipart form data handling for file uploads
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # Add explicit multipart form data schema for better browser compatibility
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() == "post" and "requestBody" in openapi_schema["paths"][path][method]:
                request_body = openapi_schema["paths"][path][method]["requestBody"]
                if "content" in request_body and "multipart/form-data" in request_body["content"]:
                    # Ensure proper encoding for file uploads
                    multipart_content = request_body["content"]["multipart/form-data"]
                    if "encoding" not in multipart_content:
                        multipart_content["encoding"] = {}
                    
                    # Add encoding for file fields to ensure proper handling
                    if "schema" in multipart_content and "properties" in multipart_content["schema"]:
                        for prop_name, prop_schema in multipart_content["schema"]["properties"].items():
                            if prop_schema.get("format") == "binary":
                                multipart_content["encoding"][prop_name] = {
                                    "contentType": "application/octet-stream"
                                }
    
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
    
    # read-only endpoints 
    public_get_paths = {
        "/categories/",
        "/categories/{category_id}"
    }
    
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() in ["get", "post", "put", "delete", "patch"]:

                if path in public_paths:
                    continue
                
                if method.lower() == "get" and path in public_get_paths:
                    continue
                
                if "security" not in openapi_schema["paths"][path][method]:
                    openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# define cors for browser 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type"],
)

# create upload files inside the folder
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, tags=["Authentication"])

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])
app.include_router(flashes.router, prefix="/flashes", tags=["Flashes writer quotes"])

app.include_router(admin_auth.router, prefix="/admin", tags=["Admin Authentication"])
app.include_router(publisher_auth.router, prefix="/publisher", tags=["Publisher House"])
app.include_router(publisher_vacancies.router, prefix="/publisher/vacancies", tags=["Publisher Vacancies"])
#never get 404
@app.get("/")
async def root():
    return {
    } 