# backend/app/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 🔧 Используем bcrypt с явной настройкой, чтобы избежать проблем с версией
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",  # Явно указываем версию bcrypt
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # 🔧 Обрезаем пароль до 72 байт (ограничение bcrypt)
    # Кодируем в bytes, чтобы точно посчитать байты, а не символы
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def create_access_token( dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)