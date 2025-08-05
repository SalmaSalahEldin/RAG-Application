from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from models.db_schemes.minirag.schemes import User
from routes.schemes.auth import UserCreate, User as UserSchema, Token
from utils.auth import get_password_hash, verify_password, create_access_token, get_current_active_user
from utils.error_handler import ErrorHandler, handle_auth_error
from helpers.config import get_settings
from database import get_db

auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

# Database dependency will be imported from main

@auth_router.post("/register", response_model=UserSchema)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return handle_auth_error("USER_ALREADY_EXISTS", {
                "email": user.email,
                "message": "An account with this email already exists"
            })
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return ErrorHandler.create_success_response(
            message="User registered successfully",
            data={
                "user_id": db_user.user_id,
                "email": db_user.email,
                "is_active": db_user.is_active
            },
            status_code=200
        )
        
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="user", user_id=None)

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    try:
        # Find user by email
        stmt = select(User).where(User.email == form_data.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return handle_auth_error("USER_NOT_FOUND", {
                "email": form_data.username,
                "message": "No account found with this email address"
            })
        
        if not verify_password(form_data.password, user.hashed_password):
            return handle_auth_error("INVALID_CREDENTIALS", {
                "email": form_data.username,
                "message": "Incorrect password"
            })
        
        if not user.is_active:
            return handle_auth_error("INACTIVE_USER", {
                "user_id": user.user_id,
                "email": user.email,
                "message": "Account is inactive"
            })
        
        # Create access token
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.user_id)}, expires_delta=access_token_expires
        )
        
        return ErrorHandler.create_success_response(
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "email": user.email
            },
            status_code=200
        )
        
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="user", user_id=None)

@auth_router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    try:
        return ErrorHandler.create_success_response(
            message="User information retrieved successfully",
            data={
                "user_id": current_user.user_id,
                "email": current_user.email,
                "is_active": current_user.is_active
            },
            status_code=200
        )
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="user", user_id=current_user.user_id) 