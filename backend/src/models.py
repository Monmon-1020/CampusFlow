from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AssignmentStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class EventCategory(str, Enum):
    ACADEMIC = "academic"
    CULTURAL = "cultural"
    SPORTS = "sports"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"


class AnnouncementType(str, Enum):
    GENERAL = "general"
    URGENT = "urgent"
    HOMEWORK = "homework"
    EVENT = "event"
    REMINDER = "reminder"


class LostItemStatus(str, Enum):
    LOST = "lost"
    FOUND = "found"
    CLAIMED = "claimed"


class StreamType(str, Enum):
    CLASS = "class"
    SUBJECT = "subject"
    SCHOOL = "school"


class StreamRole(str, Enum):
    STUDENT = "student"
    STREAM_ADMIN = "stream_admin"
    ADMIN = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    name: str
    picture_url: Optional[str] = None
    role: UserRole = Field(default=UserRole.STUDENT)

    # クラス・学年情報
    class_name: Optional[str] = None  # "1年A組", "2年B組" など
    grade: Optional[int] = None  # 1, 2, 3年
    student_number: Optional[str] = None  # 学籍番号

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    created_assignments: list["Assignment"] = Relationship(back_populates="creator")
    assignment_logs: list["AssignmentLog"] = Relationship(back_populates="user")
    created_events: list["Event"] = Relationship(back_populates="creator")
    created_announcements: list["Announcement"] = Relationship(back_populates="creator")
    created_streams: list["Stream"] = Relationship(back_populates="creator")
    stream_memberships: list["StreamMembership"] = Relationship(back_populates="user")
    created_lost_items: list["LostItem"] = Relationship(back_populates="creator")


class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    description: Optional[str] = None
    subject: str
    due_at: datetime
    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: User = Relationship(back_populates="created_assignments")
    assignment_logs: list["AssignmentLog"] = Relationship(back_populates="assignment")


class AssignmentLog(SQLModel, table=True):
    __tablename__ = "assignment_logs"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    assignment_id: str = Field(foreign_key="assignments.id")
    user_id: str = Field(foreign_key="users.id")
    status: AssignmentStatus = Field(default=AssignmentStatus.NOT_STARTED)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    assignment: Assignment = Relationship(back_populates="assignment_logs")
    user: User = Relationship(back_populates="assignment_logs")


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    description: Optional[str] = None
    category: EventCategory = Field(default=EventCategory.OTHER)
    start_at: datetime
    end_at: datetime
    location: Optional[str] = None
    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: User = Relationship(back_populates="created_events")


class Stream(SQLModel, table=True):
    """クラス・教科別ストリーム"""

    __tablename__ = "streams"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str  # "1年A組", "数学科", "全校" など
    description: Optional[str] = None
    stream_type: StreamType = Field(default=StreamType.CLASS)

    # クラス情報
    class_name: Optional[str] = None  # "1年A組"
    subject_name: Optional[str] = None  # "数学", "国語"
    grade: Optional[int] = None  # 1, 2, 3年

    # 設定
    is_public: bool = Field(default=True)  # 公開/非公開
    allow_student_posts: bool = Field(default=False)  # 生徒投稿許可

    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: User = Relationship(back_populates="created_streams")
    memberships: list["StreamMembership"] = Relationship(back_populates="stream")
    announcements: list["Announcement"] = Relationship(back_populates="stream")


class StreamMembership(SQLModel, table=True):
    """ストリームのメンバーシップ"""

    __tablename__ = "stream_memberships"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    stream_id: str = Field(foreign_key="streams.id")

    # ロールベース権限
    role: StreamRole = Field(default=StreamRole.STUDENT)

    joined_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="stream_memberships")
    stream: Stream = Relationship(back_populates="memberships")


class Announcement(SQLModel, table=True):
    """お知らせ・投稿"""

    __tablename__ = "announcements"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    content: str
    announcement_type: AnnouncementType = Field(default=AnnouncementType.GENERAL)

    # 配信設定
    is_urgent: bool = Field(default=False)  # 緊急フラグ
    is_pinned: bool = Field(default=False)  # ピン留め

    # メタデータ
    tags: Optional[str] = None  # JSON形式でタグ保存
    attachments: Optional[str] = None  # JSON形式で添付ファイル情報

    # 配信先
    stream_id: str = Field(foreign_key="streams.id")
    target_grades: Optional[str] = None  # JSON配列 [1,2,3]
    target_classes: Optional[str] = None  # JSON配列 ["1年A組", "2年B組"]

    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: User = Relationship(back_populates="created_announcements")
    stream: Stream = Relationship(back_populates="announcements")
    reactions: list["AnnouncementReaction"] = Relationship(
        back_populates="announcement"
    )


class AnnouncementReaction(SQLModel, table=True):
    """お知らせへのリアクション（いいね、確認済みなど）"""

    __tablename__ = "announcement_reactions"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    announcement_id: str = Field(foreign_key="announcements.id")
    user_id: str = Field(foreign_key="users.id")

    reaction_type: str  # "like", "read", "important" など
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    announcement: Announcement = Relationship(back_populates="reactions")


class LostItem(SQLModel, table=True):
    """忘れ物・落とし物掲示板"""

    __tablename__ = "lost_items"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str  # "黒い水筒", "数学の教科書"など
    description: str  # 詳細説明
    category: Optional[str] = None  # "文房具", "衣類", "教科書"など
    location_found: Optional[str] = None  # 発見場所
    location_lost: Optional[str] = None  # 紛失場所
    
    # ステータス
    status: LostItemStatus = Field(default=LostItemStatus.LOST)
    
    # 画像・添付ファイル
    image_url: Optional[str] = None
    
    # 連絡先情報
    contact_info: Optional[str] = None  # 連絡方法
    
    # 日時情報
    date_lost: Optional[datetime] = None  # 紛失日時
    date_found: Optional[datetime] = None  # 発見日時
    
    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    creator: User = Relationship(back_populates="created_lost_items")


# TODO: Phase 2 models for suggestion box
# class Suggestion(SQLModel, table=True):
#     pass
