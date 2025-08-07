from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, select

from ..auth import get_current_admin, get_current_user
from ..database import get_async_session
from ..models import Event, User
from ..schemas import EventCreate, EventResponse, EventUpdate

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session),
):
    # Validate that end_at is after start_at
    if event_data.end_at <= event_data.start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    event = Event(**event_data.model_dump(), created_by=current_user.id)
    session.add(event)
    await session.commit()
    await session.refresh(event)

    return event


@router.get("/", response_model=List[EventResponse])
async def get_events(
    week: bool = Query(False, description="Get events for current week"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(
        None, description="Filter events starting from this date"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter events ending before this date"
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Event)

    if week:
        # Get current week (Monday to Sunday)
        today = datetime.utcnow().date()
        days_since_monday = today.weekday()
        week_start = datetime.combine(
            today - timedelta(days=days_since_monday), datetime.min.time()
        )
        week_end = week_start + timedelta(days=7)

        query = query.where(
            and_(Event.start_at >= week_start, Event.start_at < week_end)
        )

    if category:
        query = query.where(Event.category == category)

    if start_date:
        query = query.where(Event.start_at >= start_date)

    if end_date:
        query = query.where(Event.end_at <= end_date)

    query = query.order_by(Event.start_at)

    result = await session.exec(query)
    events = result.all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Event).where(Event.id == event_id)
    result = await session.exec(statement)
    event = result.first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Event).where(Event.id == event_id)
    result = await session.exec(statement)
    event = result.first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Check if user is the creator or admin
    if event.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event",
        )

    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    # Validate that end_at is after start_at if both are provided
    if event.end_at <= event.start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    event.updated_at = datetime.utcnow()
    session.add(event)
    await session.commit()
    await session.refresh(event)

    return event


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Event).where(Event.id == event_id)
    result = await session.exec(statement)
    event = result.first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Check if user is the creator or admin
    if event.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this event",
        )

    await session.delete(event)
    await session.commit()

    return {"message": "Event deleted successfully"}


@router.get("/categories/", response_model=List[str])
async def get_event_categories(current_user: User = Depends(get_current_user)):
    """Get all available event categories"""
    from ..models import EventCategory

    return [category.value for category in EventCategory]
