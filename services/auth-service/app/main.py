"""
Auth Service - 인증/인가 마이크로서비스
JWT 기반 인증, 회원가입, 로그인, 토큰 갱신
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

app = FastAPI(title="Auth Service", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 설정
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


# 유틸리티 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """리프레시 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """현재 사용자 가져오기"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    # 실제로는 DB에서 사용자 조회
    # user = db.query(User).filter(User.id == token_data.user_id).first()
    # if user is None:
    #     raise credentials_exception
    
    return token_data


# API Endpoints
@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    사용자 회원가입
    - username: 고유 사용자명
    - email: 이메일 주소
    - password: 비밀번호 (최소 8자)
    """
    # 실제로는 DB에 저장
    # 1. 중복 체크
    # 2. 비밀번호 해싱
    # 3. DB 저장
    
    hashed_password = get_password_hash(user.password)
    
    # Mock response
    return {
        "id": 1,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": True,
        "created_at": datetime.utcnow()
    }


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    로그인
    - username: 사용자명 또는 이메일
    - password: 비밀번호
    """
    # 실제로는 DB에서 사용자 조회 및 검증
    # user = db.query(User).filter(User.username == form_data.username).first()
    # if not user or not verify_password(form_data.password, user.password):
    #     raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Mock user
    user_id = 1
    username = form_data.username
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "username": username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user_id, "username": username}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    토큰 갱신
    - refresh_token: 리프레시 토큰
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        # 새 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user_id, "username": username},
            expires_delta=access_token_expires
        )
        
        new_refresh_token = create_refresh_token(
            data={"sub": user_id, "username": username}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    # 실제로는 DB에서 전체 정보 조회
    return {
        "id": current_user.user_id,
        "username": current_user.username,
        "email": f"{current_user.username}@example.com",
        "full_name": "Test User",
        "is_active": True,
        "created_at": datetime.utcnow()
    }


@app.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    로그아웃
    - 토큰 무효화 (Redis에 블랙리스트 추가)
    """
    # 실제로는 Redis에 토큰 블랙리스트 추가
    return {"message": "Successfully logged out"}


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "auth-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
