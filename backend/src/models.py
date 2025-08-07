from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


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


class StreamType(str, Enum):
    CLASS = "class"
    SUBJECT = "subject"
    SCHOOL = "school"


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
    
    # 権限
    can_post: bool = Field(default=False)  # 投稿権限
    can_moderate: bool = Field(default=False)  # モデレート権限
    is_admin: bool = Field(default=False)  # 管理権限
    
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
    reactions: list["AnnouncementReaction"] = Relationship(back_populates="announcement")


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


# TODO: Phase 2 models for suggestion box and lost & found
# class Suggestion(SQLModel, table=True):
#     pass
#
# class LostItem(SQLModel, table=True):
#     pass
