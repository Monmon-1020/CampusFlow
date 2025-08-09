import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, or_, select

from ..auth import get_current_teacher, get_current_user, require_stream_role
from ..database import get_async_session
from ..models import (
    Announcement,
    AnnouncementReaction,
    AnnouncementType,
    Stream,
    StreamMembership,
    StreamRole,
    StreamType,
    User,
)

router = APIRouter(prefix="/api/streams", tags=["streams"])


@router.get("", response_model=List[dict])
async def get_my_streams(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """ユーザーが参加しているストリーム一覧を取得"""

    # ユーザーのストリームメンバーシップを取得
    statement = select(StreamMembership).where(
        StreamMembership.user_id == current_user.id
    )
    result = await session.execute(statement)
    memberships = result.scalars().all()

    streams = []
    for membership in memberships:
        # 各ストリーム情報を取得
        stream_statement = select(Stream).where(Stream.id == membership.stream_id)
        stream_result = await session.execute(stream_statement)
        stream = stream_result.scalars().first()

        if stream:
            # 最新のお知らせ数を取得
            announcement_statement = (
                select(Announcement)
                .where(Announcement.stream_id == stream.id)
                .order_by(Announcement.created_at.desc())
                .limit(5)
            )
            announcement_result = await session.execute(announcement_statement)
            recent_announcements = announcement_result.scalars().all()

            streams.append(
                {
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
                        "role": membership.role,
                        "joined_at": membership.joined_at,
                    },
                    "recent_announcements_count": len(recent_announcements),
                    "created_at": stream.created_at,
                }
            )

    return streams


@router.get("/{stream_id}/announcements")
async def get_stream_announcements(
    stream_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """ストリームのお知らせ一覧を取得（全文検索対応）"""

    # ユーザーがストリームのメンバーかチェック
    membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id,
        )
    )
    membership_result = await session.execute(membership_statement)
    membership = membership_result.scalars().first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="このストリームへのアクセス権限がありません"
        )

    # お知らせを検索
    statement = select(Announcement).where(Announcement.stream_id == stream_id)

    # 全文検索
    if search:
        search_condition = or_(
            Announcement.title.ilike(f"%{search}%"),
            Announcement.content.ilike(f"%{search}%"),
            Announcement.tags.ilike(f"%{search}%"),
        )
        statement = statement.where(search_condition)

    statement = (
        statement.order_by(
            Announcement.is_pinned.desc(), Announcement.created_at.desc()  # ピン留め優先
        )
        .offset(skip)
        .limit(limit)
    )

    result = await session.execute(statement)
    announcements = result.scalars().all()

    # 各お知らせの作成者とリアクション情報を取得
    response_data = []
    for announcement in announcements:
        # 作成者情報を取得
        creator_statement = select(User).where(User.id == announcement.created_by)
        creator_result = await session.execute(creator_statement)
        creator = creator_result.scalars().first()

        # ユーザーのリアクション情報を取得
        reaction_statement = select(AnnouncementReaction).where(
            and_(
                AnnouncementReaction.announcement_id == announcement.id,
                AnnouncementReaction.user_id == current_user.id,
            )
        )
        reaction_result = await session.execute(reaction_statement)
        user_reactions = reaction_result.scalars().all()

        # 全体のリアクション数を取得
        total_reactions_statement = select(AnnouncementReaction).where(
            AnnouncementReaction.announcement_id == announcement.id
        )
        total_reactions_result = await session.execute(total_reactions_statement)
        total_reactions = total_reactions_result.scalars().all()

        # リアクション集計
        reaction_counts = {}
        for reaction in total_reactions:
            reaction_counts[reaction.reaction_type] = (
                reaction_counts.get(reaction.reaction_type, 0) + 1
            )

        response_data.append(
            {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "announcement_type": announcement.announcement_type,
                "is_urgent": announcement.is_urgent,
                "is_pinned": announcement.is_pinned,
                "tags": json.loads(announcement.tags) if announcement.tags else [],
                "attachments": json.loads(announcement.attachments)
                if announcement.attachments
                else [],
                "creator": {
                    "id": creator.id,
                    "name": creator.name,
                    "picture_url": creator.picture_url,
                }
                if creator
                else None,
                "user_reactions": [r.reaction_type for r in user_reactions],
                "reaction_counts": reaction_counts,
                "created_at": announcement.created_at,
                "updated_at": announcement.updated_at,
            }
        )

    return response_data


from pydantic import BaseModel


class AnnouncementCreateRequest(BaseModel):
    title: str
    content: str
    announcement_type: str = "general"
    is_urgent: bool = False
    is_pinned: bool = False
    tags: Optional[List[str]] = None
    target_grades: Optional[List[int]] = None
    target_classes: Optional[List[str]] = None


@router.post("/{stream_id}/announcements")
async def create_announcement(
    stream_id: str,
    request: AnnouncementCreateRequest,
    current_user: User = Depends(require_stream_role({"stream_admin", "admin"})),
    session: AsyncSession = Depends(get_async_session),
):
    """お知らせを作成"""

    # Get user's role to check for pinning permission
    membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id,
        )
    )
    membership_result = await session.execute(membership_statement)
    membership = membership_result.scalars().first()

    # ピン留めは管理者のみ
    if request.is_pinned and membership and membership.role != StreamRole.ADMIN:
        request.is_pinned = False

    # AnnouncementTypeエナムに変換
    try:
        announcement_type_enum = AnnouncementType(request.announcement_type)
    except ValueError:
        announcement_type_enum = AnnouncementType.GENERAL

    # お知らせを作成
    announcement = Announcement(
        title=request.title,
        content=request.content,
        announcement_type=announcement_type_enum,
        is_urgent=request.is_urgent,
        is_pinned=request.is_pinned,
        tags=json.dumps(request.tags) if request.tags else None,
        stream_id=stream_id,
        target_grades=json.dumps(request.target_grades)
        if request.target_grades
        else None,
        target_classes=json.dumps(request.target_classes)
        if request.target_classes
        else None,
        created_by=current_user.id,
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
        "message": "お知らせを作成しました",
    }


@router.put("/{stream_id}/announcements/{announcement_id}")
async def update_announcement(
    stream_id: str,
    announcement_id: str,
    title: str,
    content: str,
    announcement_type: Optional[AnnouncementType] = None,
    is_urgent: Optional[bool] = None,
    is_pinned: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    target_grades: Optional[List[int]] = None,
    target_classes: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """お知らせを編集 (作成者または管理者のみ)"""

    # お知らせを取得
    announcement_statement = select(Announcement).where(
        and_(Announcement.id == announcement_id, Announcement.stream_id == stream_id)
    )
    announcement_result = await session.execute(announcement_statement)
    announcement = announcement_result.scalars().first()

    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="お知らせが見つかりません"
        )

    # ユーザーのロールを取得
    membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id,
        )
    )
    membership_result = await session.execute(membership_statement)
    membership = membership_result.scalars().first()

    # 作成者または管理者のみ編集可能
    is_creator = announcement.created_by == current_user.id
    is_admin = membership and membership.role in [
        StreamRole.STREAM_ADMIN,
        StreamRole.ADMIN,
    ]

    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="この投稿を編集する権限がありません"
        )

    # ピン留めは管理者のみ
    if (
        is_pinned is not None
        and is_pinned
        and not (membership and membership.role == StreamRole.ADMIN)
    ):
        is_pinned = False

    # 更新
    announcement.title = title
    announcement.content = content
    if announcement_type is not None:
        announcement.announcement_type = announcement_type
    if is_urgent is not None:
        announcement.is_urgent = is_urgent
    if is_pinned is not None:
        announcement.is_pinned = is_pinned
    if tags is not None:
        announcement.tags = json.dumps(tags)
    if target_grades is not None:
        announcement.target_grades = json.dumps(target_grades)
    if target_classes is not None:
        announcement.target_classes = json.dumps(target_classes)
    announcement.updated_at = datetime.now()

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
        "updated_at": announcement.updated_at,
        "message": "お知らせを更新しました",
    }


@router.delete("/{stream_id}/announcements/{announcement_id}")
async def delete_announcement(
    stream_id: str,
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """お知らせを削除 (作成者または管理者のみ)"""

    # お知らせを取得
    announcement_statement = select(Announcement).where(
        and_(Announcement.id == announcement_id, Announcement.stream_id == stream_id)
    )
    announcement_result = await session.execute(announcement_statement)
    announcement = announcement_result.scalars().first()

    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="お知らせが見つかりません"
        )

    # ユーザーのロールを取得
    membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id,
        )
    )
    membership_result = await session.execute(membership_statement)
    membership = membership_result.scalars().first()

    # 作成者または管理者のみ削除可能
    is_creator = announcement.created_by == current_user.id
    is_admin = membership and membership.role in [
        StreamRole.STREAM_ADMIN,
        StreamRole.ADMIN,
    ]

    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="この投稿を削除する権限がありません"
        )

    # 関連するリアクションも削除
    reaction_statement = select(AnnouncementReaction).where(
        AnnouncementReaction.announcement_id == announcement_id
    )
    reaction_result = await session.execute(reaction_statement)
    reactions = reaction_result.scalars().all()

    for reaction in reactions:
        await session.delete(reaction)

    # お知らせを削除
    await session.delete(announcement)
    await session.commit()

    return {"message": "お知らせを削除しました", "deleted_id": announcement_id}


@router.post("/{stream_id}/announcements/{announcement_id}/reactions")
async def add_reaction(
    stream_id: str,
    announcement_id: str,
    reaction_type: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """お知らせにリアクションを追加"""

    # 既存のリアクションをチェック
    existing_reaction_statement = select(AnnouncementReaction).where(
        and_(
            AnnouncementReaction.announcement_id == announcement_id,
            AnnouncementReaction.user_id == current_user.id,
            AnnouncementReaction.reaction_type == reaction_type,
        )
    )
    existing_result = await session.execute(existing_reaction_statement)
    existing_reaction = existing_result.scalars().first()

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
            reaction_type=reaction_type,
        )
        session.add(reaction)
        await session.commit()
        return {"message": "リアクションを追加しました"}


@router.get("/search")
async def search_across_streams(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """クラス横断全文検索"""

    # ユーザーがアクセス可能なストリームIDを取得
    membership_statement = select(StreamMembership).where(
        StreamMembership.user_id == current_user.id
    )
    membership_result = await session.execute(membership_statement)
    memberships = membership_result.scalars().all()

    accessible_stream_ids = [m.stream_id for m in memberships]

    if not accessible_stream_ids:
        return []

    # 全文検索
    search_statement = (
        select(Announcement)
        .where(
            and_(
                Announcement.stream_id.in_(accessible_stream_ids),
                or_(
                    Announcement.title.ilike(f"%{q}%"),
                    Announcement.content.ilike(f"%{q}%"),
                    Announcement.tags.ilike(f"%{q}%"),
                ),
            )
        )
        .order_by(Announcement.created_at.desc())
        .limit(50)
    )

    result = await session.execute(search_statement)
    announcements = result.scalars().all()

    # 結果をストリーム情報と共に返す
    search_results = []
    for announcement in announcements:
        # ストリーム情報を取得
        stream_statement = select(Stream).where(Stream.id == announcement.stream_id)
        stream_result = await session.execute(stream_statement)
        stream = stream_result.scalars().first()

        # 作成者情報を取得
        creator_statement = select(User).where(User.id == announcement.created_by)
        creator_result = await session.execute(creator_statement)
        creator = creator_result.scalars().first()

        search_results.append(
            {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content[:200] + "..."
                if len(announcement.content) > 200
                else announcement.content,
                "announcement_type": announcement.announcement_type,
                "stream": {
                    "id": stream.id,
                    "name": stream.name,
                    "stream_type": stream.stream_type,
                }
                if stream
                else None,
                "creator": {"name": creator.name} if creator else None,
                "created_at": announcement.created_at,
            }
        )

    return search_results


@router.post("", response_model=dict)
async def create_stream(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    stream_type: StreamType = Form(StreamType.CLASS),
    class_name: Optional[str] = Form(None),
    subject_name: Optional[str] = Form(None),
    grade: Optional[int] = Form(None),
    allow_student_posts: bool = Form(False),
    current_user: User = Depends(get_current_teacher),  # 教師以上のみ
    session: AsyncSession = Depends(get_async_session),
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
        created_by=current_user.id,
    )

    session.add(stream)
    await session.commit()
    await session.refresh(stream)

    # 作成者を管理者として自動登録
    membership = StreamMembership(
        user_id=current_user.id, stream_id=stream.id, role=StreamRole.ADMIN
    )

    session.add(membership)
    await session.commit()

    return {
        "id": stream.id,
        "name": stream.name,
        "description": stream.description,
        "stream_type": stream.stream_type,
        "created_at": stream.created_at,
        "message": "ストリームを作成しました",
    }


@router.post("/{stream_id}/invite", response_model=dict)
async def invite_user_to_stream(
    stream_id: str,
    email: str = Form(...),
    role: StreamRole = Form(StreamRole.STUDENT),
    current_user: User = Depends(require_stream_role({"stream_admin", "admin"})),
    session: AsyncSession = Depends(get_async_session),
):
    """ストリームにユーザーを招待（ストリーム管理者以上のみ）"""

    # ストリーム存在確認
    stream_statement = select(Stream).where(Stream.id == stream_id)
    stream_result = await session.execute(stream_statement)
    stream = stream_result.scalars().first()

    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ストリームが見つかりません"
        )

    # ユーザー検索（メールアドレスで）
    user_statement = select(User).where(User.email == email)
    user_result = await session.execute(user_statement)
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="指定されたメールアドレスのユーザーが見つかりません"
        )

    # 既存のメンバーシップをチェック
    existing_membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == user.id, StreamMembership.stream_id == stream_id
        )
    )
    existing_result = await session.execute(existing_membership_statement)
    existing_membership = existing_result.scalars().first()

    if existing_membership:
        return {
            "message": f"{user.name}さんは既にこのストリームのメンバーです",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": existing_membership.role,
            },
        }

    # 新しいメンバーシップを作成
    membership = StreamMembership(user_id=user.id, stream_id=stream_id, role=role)

    session.add(membership)
    await session.commit()
    await session.refresh(membership)

    return {
        "message": f"{user.name}さんを{stream.name}に招待しました",
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": role},
        "stream": {"id": stream.id, "name": stream.name},
    }


@router.get("/{stream_id}/members", response_model=List[dict])
async def get_stream_members(
    stream_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """ストリームのメンバー一覧を取得"""

    # ユーザーがこのストリームのメンバーかチェック
    user_membership_statement = select(StreamMembership).where(
        and_(
            StreamMembership.user_id == current_user.id,
            StreamMembership.stream_id == stream_id,
        )
    )
    user_membership_result = await session.execute(user_membership_statement)
    user_membership = user_membership_result.scalars().first()

    if not user_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="このストリームへのアクセス権限がありません"
        )

    # ストリームのすべてのメンバーシップを取得
    memberships_statement = select(StreamMembership).where(
        StreamMembership.stream_id == stream_id
    )
    memberships_result = await session.execute(memberships_statement)
    memberships = memberships_result.scalars().all()

    members = []
    for membership in memberships:
        # ユーザー情報を取得
        user_statement = select(User).where(User.id == membership.user_id)
        user_result = await session.execute(user_statement)
        user = user_result.scalars().first()

        if user:
            members.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": membership.role,
                    "joined_at": membership.joined_at,
                }
            )

    return members
