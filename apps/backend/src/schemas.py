from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .models import AssignmentStatus, EventCategory, UserRole


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject: str
    due_at: datetime


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    due_at: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    subject: str
    due_at: datetime
    created_by: str
    created_at: datetime
    updated_at: datetime


class AssignmentLogCreate(BaseModel):
    assignment_id: str
    status: AssignmentStatus
    notes: Optional[str] = None


class AssignmentLogUpdate(BaseModel):
    status: Optional[AssignmentStatus] = None
    notes: Optional[str] = None


class AssignmentLogResponse(BaseModel):
    id: str
    assignment_id: str
    user_id: str
    status: AssignmentStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: EventCategory
    start_at: datetime
    end_at: datetime
    location: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[EventCategory] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    location: Optional[str] = None


class EventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    category: EventCategory
    start_at: datetime
    end_at: datetime
    location: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture_url: Optional[str]
    role: UserRole
    created_at: datetime
