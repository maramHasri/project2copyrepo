# Book Platform API

A FastAPI-based backend for a book platform that handles user roles, book management, and publisher features.

## Features

- User authentication and authorization
- Book management (CRUD operations)
- Category management
- Publisher management
- Job vacancies posting
- Quote management
- Admin dashboard

## Tech Stack

- FastAPI
- SQLAlchemy
- Alembic (for database migrations)
- JWT Authentication
- SQLite Database

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
alembic upgrade head
```

5. Run the application:
```bash
python run.py
```

The API will be available at http://localhost:3000
API documentation will be available at http://localhost:3000/docs

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./book_platform.db
```

## API Endpoints

- `/auth` - Authentication endpoints
- `/users` - User management
- `/books` - Book management
- `/categories` - Category management
- `/publishers` - Publisher management
- `/vacancies` - Job vacancies
- `/quotes` - Book quotes

## Development

- The application uses hot-reload, so changes will be reflected immediately
- Database migrations can be created using Alembic
- API documentation is automatically generated using Swagger UI 