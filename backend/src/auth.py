import os
from datetime import datetime, timedelta
from typing import Optional

from authlib.integrations.httpx_client import AsyncOAuth2Client
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select

from .database import get_async_session
from .models import StreamMembership, StreamRole, User

# .envファイルを読み込み
load_dotenv()
# ルートディレクトリの.envも読み込み
load_dotenv("/workspaces/CampusFlow/.env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_in_production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:3001/auth/google/callback"
)

security = HTTPBearer()


class AuthManager:
    def __init__(self):
        self.google_client = AsyncOAuth2Client(
            GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, scope="openid email profile"
        )

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    def get_google_auth_url(self):
        authorization_url, state = self.google_client.create_authorization_url(
            "https://accounts.google.com/o/oauth2/auth",
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        return authorization_url

    async def exchange_code_for_token(self, code: str):
        token = await self.google_client.fetch_access_token(
            "https://oauth2.googleapis.com/token",
            code=code,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        return token

    async def get_user_info(self, access_token: str):
        self.google_client.token = {"access_token": access_token}
        resp = await self.google_client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo"
        )
        return resp.json()


auth_manager = AuthManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


async def get_current_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher, admin, or super_admin access required",
        )
    return current_user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin or super_admin access required"
        )
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required"
        )
    return current_user


async def get_stream_role(
    user_id: str, stream_id: str, session: AsyncSession = Depends(get_async_session)
) -> Optional[StreamRole]:
    """Get user's role in a specific stream"""
    statement = select(StreamMembership).where(
        (StreamMembership.user_id == user_id)
        & (StreamMembership.stream_id == stream_id)
    )
    result = await session.execute(statement)
    membership = result.scalars().first()

    if membership:
        return membership.role
    return None


def require_stream_role(allowed_roles: set[str]):
    """Dependency factory to require specific stream roles"""

    async def check_stream_role(
        stream_id: str,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session),
    ):
        # Get user's stream role
        user_role = await get_stream_role(current_user.id, stream_id, session)

        # Check if user has required role
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="このストリームへのアクセス権限がありません"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="この操作を実行する権限がありません"
            )

        return current_user

    return check_stream_role
