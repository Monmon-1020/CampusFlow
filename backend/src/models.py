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


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    name: str
    picture_url: Optional[str] = None
    role: UserRole = Field(default=UserRole.STUDENT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    created_assignments: list["Assignment"] = Relationship(back_populates="creator")
    assignment_logs: list["AssignmentLog"] = Relationship(back_populates="user")
    created_events: list["Event"] = Relationship(back_populates="creator")


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


# TODO: Phase 2 models for suggestion box and lost & found
# class Suggestion(SQLModel, table=True):
#     pass
#
# class LostItem(SQLModel, table=True):
#     pass
