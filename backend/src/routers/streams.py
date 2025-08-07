from datetime import datetime
from typing import List, Optional
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, or_

from ..auth import get_current_user, get_current_teacher
from ..database import get_async_session
from ..models import (
    User, Stream, StreamMembership, Announcement, AnnouncementReaction,
    StreamType, AnnouncementType
)

router = APIRouter(prefix="/api/streams", tags=["streams"])


@router.get("/", response_model=List[dict])
async def get_my_streams(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """ユーザーが参加しているストリーム一覧を取得"""
    
    # ユーザーのストリームメンバーシップを取得
    statement = select(StreamMembership).where(
        StreamMembership.user_id == current_user.id
    )
    result = await session.exec(statement)
    memberships = result.all()
    
    streams = []
    for membership in memberships:
        # 各ストリーム情報を取得
        stream_statement = select(Stream).where(Stream.id == membership.stream_id)
        stream_result = await session.exec(stream_statement)
        stream = stream_result.first()
        
        if stream:
            # 最新のお知らせ数を取得
            announcement_statement = select(Announcement).where(
                Announcement.stream_id == stream.id
            ).order_by(Announcement.created_at.desc()).limit(5)
            announcement_result = await session.exec(announcement_statement)
            recent_announcements = announcement_result.all()
            
            streams.append({
                "id": stream.id,
                "name": stream.name,
                "description": stream.description,
                "stream_type": stream.stream_type,
                "class_name": stream.class_name,
                "subject_name": stream.subject_name,
                "grade": stream.grade,
                "is_public": stream.is_public,
                "allow_student_posts": stream.allow_student_posts,
                "membership": {
                    "can_post": membership.can_post,
                    "can_moderate": membership.can_moderate,
                    "is_admin": membership.is_admin,
                    "joined_at": membership.joined_at
                },
                "recent_announcements_count": len(recent_announcements),
                "created_at": stream.created_at
            })
    
    return streams


@router.get("/{stream_id}/announcements")
async def get_stream_announcements(
    stream_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """ストリームのお知らせ一覧を取得（全文検索対応）"""
    
    # ユーザーがストリームのメンバーかチェック
    membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id
        )
    )
    membership_result = await session.exec(membership_statement)
    membership = membership_result.first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このストリームへのアクセス権限がありません"
        )
    
    # お知らせを検索
    statement = select(Announcement).where(Announcement.stream_id == stream_id)
    
    # 全文検索
    if search:
        search_condition = or_(
            Announcement.title.ilike(f"%{search}%"),
            Announcement.content.ilike(f"%{search}%"),
            Announcement.tags.ilike(f"%{search}%")
        )
        statement = statement.where(search_condition)
    
    statement = statement.order_by(
        Announcement.is_pinned.desc(),  # ピン留め優先
        Announcement.created_at.desc()
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    announcements = result.all()
    
    # 各お知らせの作成者とリアクション情報を取得
    response_data = []
    for announcement in announcements:
        # 作成者情報を取得
        creator_statement = select(User).where(User.id == announcement.created_by)
        creator_result = await session.exec(creator_statement)
        creator = creator_result.first()
        
        # ユーザーのリアクション情報を取得
        reaction_statement = select(AnnouncementReaction).where(
            and_(
                AnnouncementReaction.announcement_id == announcement.id,
                AnnouncementReaction.user_id == current_user.id
            )
        )
        reaction_result = await session.exec(reaction_statement)
        user_reactions = reaction_result.all()
        
        # 全体のリアクション数を取得
        total_reactions_statement = select(AnnouncementReaction).where(
            AnnouncementReaction.announcement_id == announcement.id
        )
        total_reactions_result = await session.exec(total_reactions_statement)
        total_reactions = total_reactions_result.all()
        
        # リアクション集計
        reaction_counts = {}
        for reaction in total_reactions:
            reaction_counts[reaction.reaction_type] = reaction_counts.get(reaction.reaction_type, 0) + 1
        
        response_data.append({
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "announcement_type": announcement.announcement_type,
            "is_urgent": announcement.is_urgent,
            "is_pinned": announcement.is_pinned,
            "tags": json.loads(announcement.tags) if announcement.tags else [],
            "attachments": json.loads(announcement.attachments) if announcement.attachments else [],
            "creator": {
                "id": creator.id,
                "name": creator.name,
                "picture_url": creator.picture_url
            } if creator else None,
            "user_reactions": [r.reaction_type for r in user_reactions],
            "reaction_counts": reaction_counts,
            "created_at": announcement.created_at,
            "updated_at": announcement.updated_at
        })
    
    return response_data


@router.post("/{stream_id}/announcements")
async def create_announcement(
    stream_id: str,
    title: str,
    content: str,
    announcement_type: AnnouncementType = AnnouncementType.GENERAL,
    is_urgent: bool = False,
    is_pinned: bool = False,
    tags: Optional[List[str]] = None,
    target_grades: Optional[List[int]] = None,
    target_classes: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """お知らせを作成"""
    
    # ユーザーがストリームに投稿権限があるかチェック
    membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id
        )
    )
    membership_result = await session.exec(membership_statement)
    membership = membership_result.first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このストリームへのアクセス権限がありません"
        )
    
    # 投稿権限をチェック
    if not membership.can_post and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="投稿権限がありません"
        )
    
    # ピン留めは管理者・教師のみ
    if is_pinned and current_user.role == "student":
        is_pinned = False
    
    # お知らせを作成
    announcement = Announcement(
        title=title,
        content=content,
        announcement_type=announcement_type,
        is_urgent=is_urgent,
        is_pinned=is_pinned,
        tags=json.dumps(tags) if tags else None,
        stream_id=stream_id,
        target_grades=json.dumps(target_grades) if target_grades else None,
        target_classes=json.dumps(target_classes) if target_classes else None,
        created_by=current_user.id
    )
    
    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)
    
    return {
        "id": announcement.id,
        "title": announcement.title,
        "content": announcement.content,
        "announcement_type": announcement.announcement_type,
        "is_urgent": announcement.is_urgent,
        "is_pinned": announcement.is_pinned,
        "created_at": announcement.created_at,
        "message": "お知らせを作成しました"
    }


@router.post("/{stream_id}/announcements/{announcement_id}/reactions")
async def add_reaction(
    stream_id: str,
    announcement_id: str,
    reaction_type: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """お知らせにリアクションを追加"""
    
    # 既存のリアクションをチェック
    existing_reaction_statement = select(AnnouncementReaction).where(
        and_(
            AnnouncementReaction.announcement_id == announcement_id,
            AnnouncementReaction.user_id == current_user.id,
            AnnouncementReaction.reaction_type == reaction_type
        )
    )
    existing_result = await session.exec(existing_reaction_statement)
    existing_reaction = existing_result.first()
    
    if existing_reaction:
        # 既存のリアクションを削除（トグル）
        await session.delete(existing_reaction)
        await session.commit()
        return {"message": "リアクションを削除しました"}
    else:
        # 新しいリアクションを追加
        reaction = AnnouncementReaction(
            announcement_id=announcement_id,
            user_id=current_user.id,
            reaction_type=reaction_type
        )
        session.add(reaction)
        await session.commit()
        return {"message": "リアクションを追加しました"}


@router.get("/search")
async def search_across_streams(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """クラス横断全文検索"""
    
    # ユーザーがアクセス可能なストリームIDを取得
    membership_statement = select(StreamMembership).where(
        StreamMembership.user_id == current_user.id
    )
    membership_result = await session.exec(membership_statement)
    memberships = membership_result.all()
    
    accessible_stream_ids = [m.stream_id for m in memberships]
    
    if not accessible_stream_ids:
        return []
    
    # 全文検索
    search_statement = select(Announcement).where(
        and_(
            Announcement.stream_id.in_(accessible_stream_ids),
            or_(
                Announcement.title.ilike(f"%{q}%"),
                Announcement.content.ilike(f"%{q}%"),
                Announcement.tags.ilike(f"%{q}%")
            )
        )
    ).order_by(Announcement.created_at.desc()).limit(50)
    
    result = await session.exec(search_statement)
    announcements = result.all()
    
    # 結果をストリーム情報と共に返す
    search_results = []
    for announcement in announcements:
        # ストリーム情報を取得
        stream_statement = select(Stream).where(Stream.id == announcement.stream_id)
        stream_result = await session.exec(stream_statement)
        stream = stream_result.first()
        
        # 作成者情報を取得
        creator_statement = select(User).where(User.id == announcement.created_by)
        creator_result = await session.exec(creator_statement)
        creator = creator_result.first()
        
        search_results.append({
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content[:200] + "..." if len(announcement.content) > 200 else announcement.content,
            "announcement_type": announcement.announcement_type,
            "stream": {
                "id": stream.id,
                "name": stream.name,
                "stream_type": stream.stream_type
            } if stream else None,
            "creator": {
                "name": creator.name
            } if creator else None,
            "created_at": announcement.created_at
        })
    
    return search_results


@router.post("/", response_model=dict)
async def create_stream(
    name: str,
    description: Optional[str] = None,
    stream_type: StreamType = StreamType.CLASS,
    class_name: Optional[str] = None,
    subject_name: Optional[str] = None,
    grade: Optional[int] = None,
    allow_student_posts: bool = False,
    current_user: User = Depends(get_current_teacher),  # 教師以上のみ
    session: AsyncSession = Depends(get_async_session)
):
    """ストリームを作成（教師・管理者のみ）"""
    
    # ストリームを作成
    stream = Stream(
        name=name,
        description=description,
        stream_type=stream_type,
        class_name=class_name,
        subject_name=subject_name,
        grade=grade,
        allow_student_posts=allow_student_posts,
        created_by=current_user.id
    )
    
    session.add(stream)
    await session.commit()
    await session.refresh(stream)
    
    # 作成者を管理者として自動登録
    membership = StreamMembership(
        user_id=current_user.id,
        stream_id=stream.id,
        can_post=True,
        can_moderate=True,
        is_admin=True
    )
    
    session.add(membership)
    await session.commit()
    
    return {
        "id": stream.id,
        "name": stream.name,
        "description": stream.description,
        "stream_type": stream.stream_type,
        "created_at": stream.created_at,
        "message": "ストリームを作成しました"
    }