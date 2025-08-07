from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..auth import auth_manager
from ..database import get_async_session
from ..models import User

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
        else:
            # Update existing user info
            user.name = user_info["name"]
            user.picture_url = user_info.get("picture")
            user.updated_at = datetime.utcnow()
            session.add(user)
            await session.commit()

        # Create tokens
        access_token = auth_manager.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
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
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
