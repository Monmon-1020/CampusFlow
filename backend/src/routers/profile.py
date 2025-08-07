import os
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update
from pydantic import BaseModel

from ..auth import get_current_user
from ..database import get_async_session
from ..models import User, StreamMembership, StreamRole

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ElevateCode(BaseModel):
    code: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = None
    grade: Optional[int] = None
    student_number: Optional[str] = None


@router.post("/elevate")
async def elevate_to_stream_admin(
    elevate_request: ElevateCode,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """ユーザーをストリーム管理者に昇格"""
    
    # Get the stream admin code from environment
    stream_admin_code = os.getenv("STREAM_ADMIN_CODE")
    if not stream_admin_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stream admin code not configured"
        )
    
    # Verify the provided code
    if not secrets.compare_digest(elevate_request.code, stream_admin_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid code"
        )
    
    # Update all stream memberships for this user to stream_admin
    statement = (
        update(StreamMembership)
        .where(StreamMembership.user_id == current_user.id)
        .values(role=StreamRole.STREAM_ADMIN)
    )
    
    result = await session.exec(statement)
    await session.commit()
    
    # Check if any rows were affected
    if result.rowcount == 0:
        return {
            "status": "ok", 
            "message": "コードが確認されましたが、更新可能なストリームメンバーシップがありません"
        }
    
    return {
        "status": "ok", 
        "message": f"{result.rowcount} 個のストリームでストリーム管理者権限を取得しました",
        "updated_memberships": result.rowcount
    }


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """プロフィール情報を取得"""
    
    # Get user's stream memberships
    statement = select(StreamMembership).where(StreamMembership.user_id == current_user.id)
    result = await session.exec(statement)
    memberships = result.all()
    
    membership_info = []
    for membership in memberships:
        # Get stream info for each membership
        from ..models import Stream
        stream_statement = select(Stream).where(Stream.id == membership.stream_id)
        stream_result = await session.exec(stream_statement)
        stream = stream_result.first()
        
        if stream:
            membership_info.append({
                "stream_id": stream.id,
                "stream_name": stream.name,
                "role": membership.role,
                "joined_at": membership.joined_at
            })
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture_url": current_user.picture_url,
        "role": current_user.role,
        "class_name": current_user.class_name,
        "grade": current_user.grade,
        "student_number": current_user.student_number,
        "created_at": current_user.created_at,
        "stream_memberships": membership_info
    }


@router.put("/")
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """プロフィール情報を更新"""
    
    # 更新するフィールドをチェック
    update_data = {}
    
    if profile_update.name is not None:
        if not profile_update.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="名前は空にできません"
            )
        update_data["name"] = profile_update.name.strip()
    
    if profile_update.class_name is not None:
        update_data["class_name"] = profile_update.class_name.strip() if profile_update.class_name.strip() else None
    
    if profile_update.grade is not None:
        if profile_update.grade not in [1, 2, 3]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学年は1、2、3のいずれかである必要があります"
            )
        update_data["grade"] = profile_update.grade
    
    if profile_update.student_number is not None:
        update_data["student_number"] = profile_update.student_number.strip() if profile_update.student_number.strip() else None
    
    if not update_data:
        return {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "picture_url": current_user.picture_url,
            "role": current_user.role,
            "class_name": current_user.class_name,
            "grade": current_user.grade,
            "student_number": current_user.student_number,
            "created_at": current_user.created_at,
            "message": "更新する項目がありません"
        }
    
    # ユーザー情報を更新
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    
    # 更新されたユーザー情報を返す
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture_url": current_user.picture_url,
        "role": current_user.role,
        "class_name": current_user.class_name,
        "grade": current_user.grade,
        "student_number": current_user.student_number,
        "created_at": current_user.created_at,
        "message": "プロフィールを更新しました"
    }