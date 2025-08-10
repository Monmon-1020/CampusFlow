# Brainstorming Session Redis Data Structure

## Core Session Data
```
session:{session_id}:state → "open"|"voting"|"closed" (TTL: 2h)
session:{session_id}:stream_id → stream_id (TTL: 2h)
session:{session_id}:admin_id → user_id (TTL: 2h)
session:{session_id}:participants → Set<user_id> (TTL: 2h)
session:{session_id}:created_at → timestamp (TTL: 2h)
```

## Anonymous ID Mapping
```
session:{session_id}:anon:{user_id} → anon_id (TTL: 2h)
```
- anon_id = HMAC(server_secret, session_id + user_id)

## Ideas Management
```
session:{session_id}:ideas:list → List<idea_id> (TTL: 2h)
session:{session_id}:ideas:{idea_id} → Hash{
    text: string,
    anon_id: string,
    group_id: string|null,
    votes: int,
    created_at: timestamp
} (TTL: 2h)
```

## Groups Management
```
session:{session_id}:groups:list → List<group_id> (TTL: 2h)
session:{session_id}:groups:{group_id} → Hash{
    title: string,
    idea_ids: JSON array,
    votes: int,
    created_at: timestamp
} (TTL: 2h)
```

## Voting System
```
session:{session_id}:votes:{anon_id} → remaining_votes (TTL: 2h)
session:{session_id}:voted:{anon_id}:{target_id} → 1 (TTL: 2h)
```
- target_id can be idea_id or group_id
- Initial remaining_votes = 3

## Rate Limiting
```
session:{session_id}:rate:{user_id} → count (TTL: 30s)
```
- Max 3 ideas per 30 seconds per user

## Session Counters
```
session:{session_id}:counters → Hash{
    total_ideas: int,
    total_votes: int,
    active_users: int
} (TTL: 2h)
```