from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..auth import auth_manager, get_current_user
from ..database import get_async_session
from ..models import User
from ..sample_data import ensure_user_has_sample_data

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/google/login")
async def google_login():
    authorization_url = auth_manager.get_google_auth_url()
    return {"url": authorization_url}


@router.get("/google/callback")
async def google_callback(
    code: str, session: AsyncSession = Depends(get_async_session)
):
    try:
        # Exchange code for token
        token = await auth_manager.exchange_code_for_token(code)

        # Get user info from Google
        user_info = await auth_manager.get_user_info(token["access_token"])

        # Check if user exists
        statement = select(User).where(User.email == user_info["email"])
        result = await session.exec(statement)
        user = result.first()

        is_new_user = False
        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                name=user_info["name"],
                picture_url=user_info.get("picture"),
                role="student",  # Default role
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            is_new_user = True
        else:
            # Update existing user info
            user.name = user_info["name"]
            user.picture_url = user_info.get("picture")
            user.updated_at = datetime.utcnow()
            session.add(user)
            await session.commit()

        # 全ユーザーに対してサンプルデータを保証（新規・既存問わず）
        try:
            await ensure_user_has_sample_data(session, user)
        except Exception as e:
            # サンプルデータ作成に失敗してもログインは継続
            print(f"サンプルデータ作成エラー: {e}")

        # Create tokens
        access_token = auth_manager.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        refresh_token = auth_manager.create_refresh_token(data={"sub": user.id})

        # In production, you would redirect to frontend with tokens
        # For now, return tokens directly
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "picture_url": user.picture_url,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str, session: AsyncSession = Depends(get_async_session)
):
    try:
        payload = auth_manager.verify_token(refresh_token)
        user_id = payload.get("sub")

        # Get user from database
        statement = select(User).where(User.id == user_id)
        result = await session.exec(statement)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Create new access token
        access_token = auth_manager.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """現在のユーザー情報を取得"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "picture_url": current_user.picture_url,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }


@router.post("/dev/login")
async def dev_login(session: AsyncSession = Depends(get_async_session)):
    """開発用：認証なしでテストユーザーとしてログイン"""
    # 既存のテストユーザーを取得
    statement = select(User).where(User.email == "test@example.com")
    result = await session.execute(statement)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テストユーザーが見つかりません。先にサンプルデータを作成してください。",
        )

    # JWTトークンを作成
    access_token = auth_manager.create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "picture_url": user.picture_url,
        },
    }
