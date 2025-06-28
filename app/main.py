from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, books, categories, quotes, publishers, vacancies
from database import engine
from models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Book Platform API",
    description="A FastAPI-based backend for a book platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])
app.include_router(publishers.router, prefix="/publishers", tags=["Publishers"])
app.include_router(vacancies.router, prefix="/vacancies", tags=["Vacancies"]) 