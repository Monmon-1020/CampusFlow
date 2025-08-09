from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, or_, select

from ..auth import get_current_teacher, get_current_user
from ..database import get_async_session
from ..models import Assignment, AssignmentLog, User
from ..schemas import (
    AssignmentCreate,
    AssignmentLogCreate,
    AssignmentLogResponse,
    AssignmentLogUpdate,
    AssignmentResponse,
    AssignmentUpdate,
)

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session),
):
    assignment = Assignment(**assignment_data.model_dump(), created_by=current_user.id)
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment


@router.get("", response_model=List[AssignmentResponse])
async def get_assignments(
    mine: bool = Query(False, description="Get assignments for current user"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    due_soon: bool = Query(False, description="Get assignments due within 7 days"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Assignment)

    if mine:
        # Get assignments for current user (through assignment logs)
        user_assignments = select(AssignmentLog.assignment_id).where(
            AssignmentLog.user_id == current_user.id
        )
        query = query.where(Assignment.id.in_(user_assignments))

    if subject:
        query = query.where(Assignment.subject == subject)

    if due_soon:
        week_from_now = datetime.utcnow() + timedelta(days=7)
        query = query.where(Assignment.due_at <= week_from_now)

    query = query.order_by(Assignment.due_at)

    result = await session.execute(query)
    assignments = result.scalars().all()
    return assignments


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Assignment).where(Assignment.id == assignment_id)
    result = await session.execute(statement)
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    assignment_data: AssignmentUpdate,
    current_user: User = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Assignment).where(Assignment.id == assignment_id)
    result = await session.execute(statement)
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check if user is the creator or admin
    if assignment.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this assignment",
        )

    update_data = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    assignment.updated_at = datetime.utcnow()
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)

    return assignment


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_teacher),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Assignment).where(Assignment.id == assignment_id)
    result = await session.execute(statement)
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check if user is the creator or admin
    if assignment.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this assignment",
        )

    await session.delete(assignment)
    await session.commit()

    return {"message": "Assignment deleted successfully"}


# Assignment Log routes
@router.post("/logs/", response_model=AssignmentLogResponse)
async def create_assignment_log(
    log_data: AssignmentLogCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Check if assignment exists
    statement = select(Assignment).where(Assignment.id == log_data.assignment_id)
    result = await session.execute(statement)
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check if log already exists for this user and assignment
    existing_log_statement = select(AssignmentLog).where(
        and_(
            AssignmentLog.assignment_id == log_data.assignment_id,
            AssignmentLog.user_id == current_user.id,
        )
    )
    result = await session.execute(existing_log_statement)
    existing_log = result.scalars().first()

    if existing_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment log already exists for this user",
        )

    log = AssignmentLog(**log_data.model_dump(), user_id=current_user.id)
    session.add(log)
    await session.commit()
    await session.refresh(log)

    return log


@router.put("/logs/{log_id}", response_model=AssignmentLogResponse)
async def update_assignment_log(
    log_id: str,
    log_data: AssignmentLogUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(AssignmentLog).where(AssignmentLog.id == log_id)
    result = await session.execute(statement)
    log = result.scalars().first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment log not found"
        )

    # Check if user owns this log
    if log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this assignment log",
        )

    update_data = log_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)

    log.updated_at = datetime.utcnow()
    session.add(log)
    await session.commit()
    await session.refresh(log)

    return log


@router.get("/logs/", response_model=List[AssignmentLogResponse])
async def get_assignment_logs(
    assignment_id: Optional[str] = Query(None, description="Filter by assignment ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(AssignmentLog).where(AssignmentLog.user_id == current_user.id)

    if assignment_id:
        query = query.where(AssignmentLog.assignment_id == assignment_id)

    query = query.order_by(AssignmentLog.updated_at.desc())

    result = await session.execute(query)
    logs = result.scalars().all()
    return logs
