from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.future import select
import sys
import os
sys.path.append(os.path.dirname(__file__))
import logging

from database import async_session, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Basic logging to assist debugging token validation issues
    try:
        logging.info(f"Validating token: {str(token)[:12]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logging.warning("Token decoded but 'sub' claim is missing")
            raise credentials_exception
    except JWTError as e:
        logging.warning(f"Token validation error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logging.error(f"Unexpected error validating token: {str(e)}")
        raise credentials_exception
    return email

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate):
    try:
        hashed_password = get_password_hash(user.password)
        async with async_session() as session:
            new_user = User(email=user.email, password=hashed_password)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

        # Ensure JWT secret is configured
        if not SECRET_KEY:
            raise HTTPException(status_code=500, detail="Server configuration error: JWT secret not set")

        # Create access token so frontend can use it immediately after sign-up
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer", "email": user.email}
    except Exception as e:
        error_msg = str(e)
        # Check if it's a duplicate email error
        if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
        raise HTTPException(status_code=400, detail=f"Kayıt hatası: {error_msg}")

@router.post("/login")
async def login(user: UserLogin):
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == user.email))
            db_user = result.scalar_one_or_none()
            if not db_user:
                raise HTTPException(status_code=400, detail="Böyle bir hesap yok")
            if not verify_password(user.password, db_user.password):
                raise HTTPException(status_code=400, detail="E-posta veya şifre hatalı")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == current_user))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            return {
                "email": user.email,
                "user_type": "premium" if user.is_premium else "free",
                "language": user.language or "tr",
                "message_count": user.message_count or 0,
                "last_message_date": user.last_message_date
            }
    except Exception as e:
        # Propagate HTTPException (like 404) unchanged so caller gets correct status code.
        if isinstance(e, HTTPException):
            raise
        logging.exception("Error in get_current_user_info")
        raise HTTPException(status_code=500, detail="Internal server error")