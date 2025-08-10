from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..auth import get_current_teacher, get_current_user
from ..database import get_async_session
from ..models import LostItem, User
from ..schemas import LostItemCreate, LostItemResponse, LostItemUpdate

router = APIRouter(prefix="/api/lost-items", tags=["lost-items"])


@router.post("", response_model=LostItemResponse)
async def create_lost_item(
    lost_item_data: LostItemCreate,
    current_user: User = Depends(get_current_teacher),  # 教師のみ作成可能
    session: AsyncSession = Depends(get_async_session),
):
    lost_item = LostItem(**lost_item_data.model_dump(), created_by=current_user.id)
    session.add(lost_item)
    await session.commit()
    await session.refresh(lost_item)
    return lost_item


@router.get("", response_model=List[LostItemResponse])
async def get_lost_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(LostItem)

    if category:
        query = query.where(LostItem.category == category)

    if status:
        query = query.where(LostItem.status == status)

    query = query.order_by(LostItem.created_at.desc())

    result = await session.execute(query)
    lost_items = result.scalars().all()
    return lost_items


@router.get("/{lost_item_id}", response_model=LostItemResponse)
async def get_lost_item(
    lost_item_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(LostItem).where(LostItem.id == lost_item_id)
    result = await session.execute(statement)
    lost_item = result.scalars().first()

    if not lost_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lost item not found"
        )

    return lost_item


@router.put("/{lost_item_id}", response_model=LostItemResponse)
async def update_lost_item(
    lost_item_id: str,
    lost_item_data: LostItemUpdate,
    current_user: User = Depends(get_current_teacher),  # 教師のみ更新可能
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(LostItem).where(LostItem.id == lost_item_id)
    result = await session.execute(statement)
    lost_item = result.scalars().first()

    if not lost_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lost item not found"
        )

    # Check if user is the creator, admin, or super_admin
    if lost_item.created_by != current_user.id and current_user.role not in [
        "admin",
        "super_admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this lost item",
        )

    update_data = lost_item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lost_item, field, value)

    lost_item.updated_at = datetime.utcnow()
    session.add(lost_item)
    await session.commit()
    await session.refresh(lost_item)

    return lost_item


@router.delete("/{lost_item_id}")
async def delete_lost_item(
    lost_item_id: str,
    current_user: User = Depends(get_current_teacher),  # 教師のみ削除可能
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(LostItem).where(LostItem.id == lost_item_id)
    result = await session.execute(statement)
    lost_item = result.scalars().first()

    if not lost_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lost item not found"
        )

    # Check if user is the creator, admin, or super_admin
    if lost_item.created_by != current_user.id and current_user.role not in [
        "admin",
        "super_admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this lost item",
        )

    await session.delete(lost_item)
    await session.commit()

    return {"message": "Lost item deleted successfully"}


@router.get("/categories/", response_model=List[str])
async def get_lost_item_categories(current_user: User = Depends(get_current_user)):
    """Get common lost item categories"""
    categories = ["文房具", "教科書・参考書", "衣類", "水筒・お弁当箱", "体操着", "上履き", "傘", "鍵", "その他"]
    return categories
