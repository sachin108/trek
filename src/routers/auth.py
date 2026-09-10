from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session
from src.database import get_db
from src.dependencies import get_current_user
from src.models import User
from src.schemas import UserProfileResponse, UserCreate, Token
from src.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def signup(user:UserCreate, db:Annotated[Session, Depends(get_db)]):
    # check if username or email already exists
    existing_user = db.scalar(select(User).where(or_(User.username == user.username, User.email == user.email)))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username or email already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        available_funds=Decimal("10000000.00"),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(db:Annotated[Session, Depends(get_db)], form_data:Annotated[OAuth2PasswordRequestForm, Depends()]):
    # When a route uses OAuth2PasswordRequestForm, FastAPI strictly expects the incoming request to be form data
    try:
        user = db.scalar(
            select(User).where(
                or_(
                    User.username.ilike(form_data.username),
                    User.email.ilike(form_data.username)
                )
            )
        )
        if not user or not verify_password(form_data.password, str(user.password)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect username or password",
                                headers={"WWW-Authenticate": "Bearer"},)

        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token, token_type="bearer")
    except Exception as e:
        print(f"Exception occurred in login API: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,)

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user:Annotated[User, Depends(get_current_user)]):
    return current_user

