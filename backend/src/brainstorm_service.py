import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import redis.asyncio as redis
from fastapi import HTTPException



class BrainstormSession:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 7200  # 2 hours
    
    async def _get_redis_value(self, key: str) -> Optional[str]:
        """Helper to get and decode Redis value"""
        value = await self.redis.get(key)
        return value.decode() if value else None

    def _get_anon_id(self, session_id: str, user_id: str) -> str:
        """Generate anonymous ID for user in session"""
        server_secret = "brainstorm_secret_key_2024"  # TODO: Move to env
        message = f"{session_id}:{user_id}"
        return hmac.new(
            server_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()[:16]

    async def create_session(self, stream_id: str, admin_id: str) -> str:
        """Create new brainstorming session"""
        session_id = str(uuid.uuid4())
        
        # Set session data
        await self.redis.setex(f"session:{session_id}:state", self.ttl, "open")
        await self.redis.setex(f"session:{session_id}:stream_id", self.ttl, stream_id)
        await self.redis.setex(f"session:{session_id}:admin_id", self.ttl, admin_id)
        await self.redis.setex(
            f"session:{session_id}:created_at", self.ttl, str(datetime.utcnow())
        )
        
        # Initialize counters
        counters = {"total_ideas": 0, "total_votes": 0, "active_users": 0}
        await self.redis.hset(
            f"session:{session_id}:counters", mapping=counters
        )
        await self.redis.expire(f"session:{session_id}:counters", self.ttl)
        
        return session_id

    async def get_session_state(self, session_id: str) -> Optional[str]:
        """Get current session state"""
        return await self._get_redis_value(f"session:{session_id}:state")

    async def join_session(self, session_id: str, user_id: str) -> str:
        """User joins session and gets anonymous ID"""
        state = await self.get_session_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add to participants
        await self.redis.sadd(f"session:{session_id}:participants", user_id)
        await self.redis.expire(f"session:{session_id}:participants", self.ttl)
        
        # Generate and cache anonymous ID
        anon_id = self._get_anon_id(session_id, user_id)
        await self.redis.setex(
            f"session:{session_id}:anon:{user_id}", self.ttl, anon_id
        )
        
        # Initialize voting allowance
        if state == "voting":
            await self.redis.setex(f"session:{session_id}:votes:{anon_id}", self.ttl, 3)
        
        # Update active users counter
        await self.redis.hincrby(f"session:{session_id}:counters", "active_users", 1)
        
        return anon_id

    async def submit_idea(self, session_id: str, user_id: str, text: str) -> str:
        """Submit new idea to session"""
        state = await self.get_session_state(session_id)
        if state != "open":
            raise HTTPException(status_code=400, detail="Session not in open state")
        
        # Rate limiting check
        rate_key = f"session:{session_id}:rate:{user_id}"
        current_rate = await self.redis.get(rate_key) or 0
        if int(current_rate) >= 3:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Increment rate counter
        await self.redis.incr(rate_key)
        await self.redis.expire(rate_key, 30)
        
        # Get anonymous ID
        anon_id = await self._get_redis_value(f"session:{session_id}:anon:{user_id}")
        if not anon_id:
            anon_id = await self.join_session(session_id, user_id)
        
        # Create idea
        idea_id = str(uuid.uuid4())
        idea_data = {
            "text": text[:50],  # Max 50 chars
            "anon_id": anon_id,
            "group_id": "",
            "votes": 0,
            "created_at": str(datetime.utcnow()),
        }
        
        # Store idea
        await self.redis.hset(f"session:{session_id}:ideas:{idea_id}", mapping=idea_data)
        await self.redis.expire(f"session:{session_id}:ideas:{idea_id}", self.ttl)
        
        # Add to ideas list
        await self.redis.lpush(f"session:{session_id}:ideas:list", idea_id)
        await self.redis.expire(f"session:{session_id}:ideas:list", self.ttl)
        
        # Update counter
        await self.redis.hincrby(f"session:{session_id}:counters", "total_ideas", 1)
        
        return idea_id

    async def create_group(self, session_id: str, admin_id: str, title: str) -> str:
        """Create new group (admin only)"""
        # Verify admin
        session_admin = await self._get_redis_value(f"session:{session_id}:admin_id")
        if session_admin != admin_id:
            raise HTTPException(status_code=403, detail="Only admin can create groups")
        
        group_id = str(uuid.uuid4())
        group_data = {
            "title": title,
            "idea_ids": "[]",
            "votes": 0,
            "created_at": str(datetime.utcnow()),
        }
        
        await self.redis.hset(f"session:{session_id}:groups:{group_id}", mapping=group_data)
        await self.redis.expire(f"session:{session_id}:groups:{group_id}", self.ttl)
        
        # Add to groups list
        await self.redis.lpush(f"session:{session_id}:groups:list", group_id)
        await self.redis.expire(f"session:{session_id}:groups:list", self.ttl)
        
        return group_id

    async def move_idea_to_group(
        self, session_id: str, admin_id: str, idea_id: str, group_id: str
    ):
        """Move idea to group (admin only)"""
        # Verify admin
        session_admin = await self._get_redis_value(f"session:{session_id}:admin_id")
        if session_admin != admin_id:
            raise HTTPException(status_code=403, detail="Only admin can move ideas")
        
        # Update idea group
        await self.redis.hset(f"session:{session_id}:ideas:{idea_id}", "group_id", group_id)
        
        # Update group's idea list
        group_data = await self.redis.hgetall(f"session:{session_id}:groups:{group_id}")
        idea_ids = json.loads(group_data.get("idea_ids", "[]"))
        if idea_id not in idea_ids:
            idea_ids.append(idea_id)
            await self.redis.hset(
                f"session:{session_id}:groups:{group_id}",
                "idea_ids",
                json.dumps(idea_ids),
            )

    async def start_voting(self, session_id: str, admin_id: str):
        """Switch session to voting phase"""
        session_admin = await self._get_redis_value(f"session:{session_id}:admin_id")
        if session_admin != admin_id:
            raise HTTPException(status_code=403, detail="Only admin can start voting")
        
        await self.redis.setex(f"session:{session_id}:state", self.ttl, "voting")
        
        # Initialize votes for all participants
        participants = await self.redis.smembers(f"session:{session_id}:participants")
        for user_id_bytes in participants:
            user_id = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes
            anon_id = await self._get_redis_value(f"session:{session_id}:anon:{user_id}")
            if anon_id:
                await self.redis.setex(f"session:{session_id}:votes:{anon_id}", self.ttl, 3)

    async def cast_vote(self, session_id: str, user_id: str, target_id: str, target_type: str):
        """Cast vote on idea or group"""
        state = await self.get_session_state(session_id)
        if state != "voting":
            raise HTTPException(status_code=400, detail="Session not in voting state")
        
        anon_id = await self._get_redis_value(f"session:{session_id}:anon:{user_id}")
        if not anon_id:
            raise HTTPException(status_code=400, detail="User not in session")
        
        # Check remaining votes
        remaining_votes = await self._get_redis_value(f"session:{session_id}:votes:{anon_id}")
        if not remaining_votes or int(remaining_votes) <= 0:
            raise HTTPException(status_code=400, detail="No votes remaining")
        
        # Check if already voted for this target
        voted_key = f"session:{session_id}:voted:{anon_id}:{target_id}"
        if await self._get_redis_value(voted_key):
            raise HTTPException(status_code=400, detail="Already voted for this item")
        
        # Cast vote
        await self.redis.setex(voted_key, self.ttl, 1)
        await self.redis.decr(f"session:{session_id}:votes:{anon_id}")
        
        # Update target vote count
        if target_type == "idea":
            await self.redis.hincrby(f"session:{session_id}:ideas:{target_id}", "votes", 1)
        elif target_type == "group":
            await self.redis.hincrby(f"session:{session_id}:groups:{target_id}", "votes", 1)
        
        # Update total votes counter
        await self.redis.hincrby(f"session:{session_id}:counters", "total_votes", 1)
        
        # Return remaining votes
        remaining = await self._get_redis_value(f"session:{session_id}:votes:{anon_id}")
        return int(remaining or 0)

    async def get_session_data(self, session_id: str) -> Dict:
        """Get all session data for client"""
        state = await self.get_session_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get ideas
        idea_ids = await self.redis.lrange(f"session:{session_id}:ideas:list", 0, -1)
        ideas = []
        for idea_id_bytes in idea_ids:
            idea_id = idea_id_bytes.decode() if isinstance(idea_id_bytes, bytes) else idea_id_bytes
            idea_data = await self.redis.hgetall(f"session:{session_id}:ideas:{idea_id}")
            if idea_data:
                # Decode Redis bytes to strings
                decoded_data = {
                    k.decode() if isinstance(k, bytes) else k: 
                    v.decode() if isinstance(v, bytes) else v 
                    for k, v in idea_data.items()
                }
                ideas.append({"id": idea_id, **decoded_data})
        
        # Get groups
        group_ids = await self.redis.lrange(f"session:{session_id}:groups:list", 0, -1)
        groups = []
        for group_id_bytes in group_ids:
            group_id = group_id_bytes.decode() if isinstance(group_id_bytes, bytes) else group_id_bytes
            group_data = await self.redis.hgetall(f"session:{session_id}:groups:{group_id}")
            if group_data:
                # Decode Redis bytes to strings
                decoded_data = {
                    k.decode() if isinstance(k, bytes) else k: 
                    v.decode() if isinstance(v, bytes) else v 
                    for k, v in group_data.items()
                }
                decoded_data["idea_ids"] = json.loads(decoded_data.get("idea_ids", "[]"))
                groups.append({"id": group_id, **decoded_data})
        
        # Get counters
        counters_raw = await self.redis.hgetall(f"session:{session_id}:counters")
        counters = {
            k.decode() if isinstance(k, bytes) else k: 
            v.decode() if isinstance(v, bytes) else v 
            for k, v in counters_raw.items()
        }
        
        return {
            "session_id": session_id,
            "state": state,
            "ideas": ideas,
            "groups": groups,
            "counters": counters,
        }

    async def end_session(self, session_id: str, admin_id: str):
        """End session and generate summary"""
        session_admin = await self._get_redis_value(f"session:{session_id}:admin_id")
        if session_admin != admin_id:
            raise HTTPException(status_code=403, detail="Only admin can end session")
        
        await self.redis.setex(f"session:{session_id}:state", self.ttl, "closed")
        
        # Generate and return summary
        return await self.generate_summary(session_id)

    async def generate_summary(self, session_id: str) -> Dict:
        """Generate session summary"""
        session_data = await self.get_session_data(session_id)
        
        # Sort groups by votes (descending)
        top_groups = sorted(
            session_data["groups"], key=lambda g: int(g.get("votes", 0)), reverse=True
        )[:3]
        
        # If no groups, use top individual ideas
        if not top_groups:
            top_ideas = sorted(
                [idea for idea in session_data["ideas"] if not idea.get("group_id")],
                key=lambda i: int(i.get("votes", 0)),
                reverse=True,
            )[:5]
            return {
                "type": "ideas",
                "top_items": top_ideas,
                "total_votes": session_data["counters"].get("total_votes", 0),
                "total_ideas": session_data["counters"].get("total_ideas", 0),
                "participants": session_data["counters"].get("active_users", 0),
            }
        
        return {
            "type": "groups",
            "top_groups": top_groups,
            "total_votes": session_data["counters"].get("total_votes", 0),
            "total_ideas": session_data["counters"].get("total_ideas", 0),
            "participants": session_data["counters"].get("active_users", 0),
        }

    async def delete_session(self, session_id: str, admin_id: str):
        """Delete brainstorm session and all its data"""
        session_admin = await self._get_redis_value(f"session:{session_id}:admin_id")
        if session_admin != admin_id:
            raise HTTPException(status_code=403, detail="Only admin can delete session")
        
        # Get all session keys to delete
        keys_to_delete = []
        
        # Session metadata
        keys_to_delete.extend([
            f"session:{session_id}:state",
            f"session:{session_id}:stream_id",
            f"session:{session_id}:admin_id",
            f"session:{session_id}:created_at",
            f"session:{session_id}:participants",
            f"session:{session_id}:counters",
        ])
        
        # Ideas
        idea_ids = await self.redis.lrange(f"session:{session_id}:ideas:list", 0, -1)
        keys_to_delete.append(f"session:{session_id}:ideas:list")
        for idea_id in idea_ids:
            keys_to_delete.append(f"session:{session_id}:ideas:{idea_id}")
        
        # Groups
        group_ids = await self.redis.lrange(f"session:{session_id}:groups:list", 0, -1)
        keys_to_delete.append(f"session:{session_id}:groups:list")
        for group_id in group_ids:
            keys_to_delete.append(f"session:{session_id}:groups:{group_id}")
        
        # Anonymous IDs and votes
        participants = await self.redis.smembers(f"session:{session_id}:participants")
        for user_id_bytes in participants:
            user_id = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes
            anon_id = await self._get_redis_value(f"session:{session_id}:anon:{user_id}")
            keys_to_delete.append(f"session:{session_id}:anon:{user_id}")
            if anon_id:
                keys_to_delete.append(f"session:{session_id}:votes:{anon_id}")
                # Delete voted keys pattern
                voted_keys = await self.redis.keys(f"session:{session_id}:voted:{anon_id}:*")
                keys_to_delete.extend(voted_keys)
            
            # Delete rate limiting keys
            keys_to_delete.append(f"session:{session_id}:rate:{user_id}")
        
        # Delete all keys
        if keys_to_delete:
            await self.redis.delete(*keys_to_delete)


# Global instance
brainstorm_service = None


async def get_brainstorm_service() -> BrainstormSession:
    global brainstorm_service
    if brainstorm_service is None:
        redis_client = redis.from_url("redis://localhost:6379/0")
        brainstorm_service = BrainstormSession(redis_client)
    return brainstorm_service