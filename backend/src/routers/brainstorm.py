from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..auth import get_current_user
from ..brainstorm_service import get_brainstorm_service, BrainstormSession
from ..database import get_async_session
from ..models import User, StreamMembership, StreamRole

router = APIRouter(prefix="/api/brainstorm", tags=["brainstorm"])


# Pydantic models
class SessionCreateRequest(BaseModel):
    stream_id: str


class IdeaSubmitRequest(BaseModel):
    text: str


class GroupCreateRequest(BaseModel):
    title: str


class MoveIdeaRequest(BaseModel):
    idea_id: str
    group_id: str


class VoteRequest(BaseModel):
    target_id: str
    target_type: str  # "idea" or "group"


class SaveSummaryRequest(BaseModel):
    title: Optional[str] = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        self.active_connections[session_id][user_id] = websocket

    def disconnect(self, session_id: str, user_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_id, None)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for websocket in self.active_connections[session_id].values():
                try:
                    await websocket.send_json(message)
                except:
                    pass


manager = ConnectionManager()


# Helper function to check stream admin permission
async def verify_stream_admin(user: User, stream_id: str, db):
    from sqlmodel import select, or_
    from ..models import UserRole
    
    # Super admins have access to everything
    if user.role == UserRole.SUPER_ADMIN:
        return None  # No need to return membership for super admins
    
    statement = select(StreamMembership).where(
        StreamMembership.user_id == user.id,
        StreamMembership.stream_id == stream_id,
        or_(
            StreamMembership.role == StreamRole.STREAM_ADMIN,
            StreamMembership.role == StreamRole.ADMIN,
        )
    )
    result = await db.execute(statement)
    membership = result.scalars().first()
    
    if not membership:
        raise HTTPException(
            status_code=403, detail="User is not admin of this stream"
        )
    return membership


@router.post("/sessions")
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_async_session),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Create new brainstorming session (admin only)"""
    # Verify user is stream admin
    await verify_stream_admin(current_user, request.stream_id, db)
    
    session_id = await service.create_session(request.stream_id, current_user.id)
    
    # Broadcast session start
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "session:open",
            "session_id": session_id,
            "phase": "open",
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return {"session_id": session_id, "state": "open"}


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Get session data"""
    # Join session if not already joined
    anon_id = await service.join_session(session_id, current_user.id)
    session_data = await service.get_session_data(session_id)
    
    # Add user's anonymous ID to response
    session_data["anon_id"] = anon_id
    
    return session_data


@router.post("/sessions/{session_id}/ideas")
async def submit_idea(
    session_id: str,
    request: IdeaSubmitRequest,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Submit new idea"""
    idea_id = await service.submit_idea(session_id, current_user.id, request.text)
    
    # Get idea data for broadcast
    session_data = await service.get_session_data(session_id)
    new_idea = None
    for idea in session_data["ideas"]:
        if idea["id"] == idea_id:
            new_idea = idea
            break
    
    # Broadcast new idea if found
    if new_idea:
        await manager.broadcast_to_session(
            session_id,
            {
                "type": "idea:new",
                "idea": new_idea,
                "timestamp": str(__import__("datetime").datetime.utcnow()),
            },
        )
    
    return {"idea_id": idea_id, "success": True}


@router.post("/sessions/{session_id}/groups")
async def create_group(
    session_id: str,
    request: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Create new group (admin only)"""
    group_id = await service.create_group(session_id, current_user.id, request.title)
    
    # Get group data for broadcast
    session_data = await service.get_session_data(session_id)
    new_group = None
    for group in session_data["groups"]:
        if group["id"] == group_id:
            new_group = group
            break
    
    # Broadcast new group if found
    if new_group:
        await manager.broadcast_to_session(
            session_id,
            {
                "type": "group:new",
                "group": new_group,
                "timestamp": str(__import__("datetime").datetime.utcnow()),
            },
        )
    
    return {"group_id": group_id, "success": True}


@router.post("/sessions/{session_id}/move")
async def move_idea_to_group(
    session_id: str,
    request: MoveIdeaRequest,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Move idea to group (admin only)"""
    await service.move_idea_to_group(
        session_id, current_user.id, request.idea_id, request.group_id
    )
    
    # Broadcast idea update
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "idea:update",
            "idea_id": request.idea_id,
            "patch": {"group_id": request.group_id},
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return {"success": True}


@router.post("/sessions/{session_id}/start-voting")
async def start_voting(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Start voting phase (admin only)"""
    await service.start_voting(session_id, current_user.id)
    
    # Broadcast phase change
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "session:phase",
            "phase": "voting",
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return {"success": True, "phase": "voting"}


@router.post("/sessions/{session_id}/vote")
async def vote(
    session_id: str,
    request: VoteRequest,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Cast vote"""
    remaining_votes = await service.cast_vote(
        session_id, current_user.id, request.target_id, request.target_type
    )
    
    # Broadcast vote cast
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "vote:cast",
            "target_id": request.target_id,
            "target_type": request.target_type,
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return {"remaining_votes": remaining_votes}


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """End session and generate summary (admin only)"""
    summary = await service.end_session(session_id, current_user.id)
    
    # Broadcast session end with summary
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "session:summary",
            "summary": summary,
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return summary


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Delete brainstorm session (admin only)"""
    await service.delete_session(session_id, current_user.id)
    
    # Broadcast session deletion
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "session:deleted",
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return {"success": True, "message": "Session deleted"}


@router.post("/sessions/{session_id}/save")
async def save_summary(
    session_id: str,
    request: SaveSummaryRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_async_session),
    service: BrainstormSession = Depends(get_brainstorm_service),
):
    """Save summary to stream (admin only)"""
    from sqlmodel import select
    from ..models import Announcement, AnnouncementType
    
    summary = await service.generate_summary(session_id)
    
    # Get stream ID
    stream_id = await service._get_redis_value(f"session:{session_id}:stream_id")
    if not stream_id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify admin permission
    await verify_stream_admin(current_user, stream_id, db)
    
    # Get session data for representative ideas
    session_data = await service.get_session_data(session_id)
    
    # Generate markdown content
    title = request.title or "ブレスト結果"
    content = f"# {title}\n\n"
    
    if summary["type"] == "groups":
        content += f"**参加者数**: {summary['participants']}人\n"
        content += f"**総アイデア数**: {summary['total_ideas']}件\n"
        content += f"**総投票数**: {summary['total_votes']}票\n\n"
        content += "## 上位グループ\n\n"
        
        for i, group in enumerate(summary["top_groups"], 1):
            content += f"{i}. **{group['title']}** (票: {group['votes']})\n"
            # Get representative ideas from the group
            group_ideas = [
                idea for idea in session_data.get("ideas", [])
                if idea.get("group_id") == group["id"]
            ]
            if group_ideas:
                top_idea = max(group_ideas, key=lambda x: int(x.get("votes", 0)))
                content += f"   - 代表アイデア: 「{top_idea['text']}」\n"
            content += "\n"
    else:
        content += f"**参加者数**: {summary['participants']}人\n"
        content += f"**総アイデア数**: {summary['total_ideas']}件\n\n"
        content += "## 上位アイデア\n\n"
        
        for i, idea in enumerate(summary["top_items"], 1):
            content += f"{i}. 「{idea['text']}」 (票: {idea['votes']})\n"
    
    # Create announcement directly
    new_announcement = Announcement(
        title=title,
        content=content,
        announcement_type=AnnouncementType.GENERAL,
        stream_id=stream_id,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_announcement)
    await db.commit()
    await db.refresh(new_announcement)
    
    # Delete the brainstorm session after saving
    await service.delete_session(session_id, current_user.id)
    
    # Broadcast session deletion and save completion
    await manager.broadcast_to_session(
        session_id,
        {
            "type": "session:saved_and_deleted",
            "announcement_id": new_announcement.id,
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        },
    )
    
    return {
        "success": True,
        "announcement_id": new_announcement.id,
        "summary": summary,
        "message": "ブレスト結果がストリームに投稿されました",
    }


@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str,
):
    """WebSocket endpoint for real-time updates"""
    try:
        # Verify token
        from jose import JWTError, jwt
        from ..auth import JWT_SECRET_KEY, JWT_ALGORITHM
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return
        except JWTError:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await manager.connect(websocket, session_id, user_id)
        
        try:
            while True:
                # Keep connection alive, listen for client messages if needed
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(session_id, user_id)
    except Exception as e:
        await websocket.close(code=1011, reason=f"Internal error: {str(e)}")