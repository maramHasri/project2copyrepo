from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole
from schemas import TokenData
import random
import string

# Security configuration
SECRET_KEY = "N93qNdu1uEX7oKM3ZQnHdV02TIuRt4umLG07eV4JhzI"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

# Admin configuration
ADMIN_CODE = "ADMIN2024"  # Change this in production

# OTP storage (in production, use Redis or database)
otp_storage = {}

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# OTP Functions
def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email: str, otp: str) -> None:
    """Store OTP with expiration time"""
    otp_storage[email] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }

def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP for given email"""
    if email not in otp_storage:
        return False
    
    stored_data = otp_storage[email]
    if datetime.utcnow() > stored_data["expires_at"]:
        del otp_storage[email]
        return False
    
    if stored_data["otp"] == otp:
        del otp_storage[email]
        return True
    
    return False

async def get_bearer_token(authorization: Optional[str] = Header(None, include_in_schema=False)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

async def get_current_user(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_user_role(required_role: UserRole):
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role.value} role"
            )
        return current_user
    return role_checker

def check_admin_role():
    async def admin_checker(current_user: User = Depends(get_current_active_user)) -> User:
        print(f"DEBUG: Checking admin role for user {current_user.username}")
        print(f"DEBUG: User role is: {current_user.role} (type: {type(current_user.role)})")
        print(f"DEBUG: Expected role: {UserRole.admin}")
        if current_user.role != UserRole.admin:
            print(f"DEBUG: Role mismatch! User has {current_user.role}, expected {UserRole.admin}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires admin role. Current role: {current_user.role}"
            )
        print("DEBUG: Admin role check passed")
        return current_user
    return admin_checker

def check_writer_or_publisher_role():
    async def writer_publisher_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [UserRole.writer, UserRole.publisher]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation requires writer or publisher role"
            )
        return current_user
    return writer_publisher_checker 