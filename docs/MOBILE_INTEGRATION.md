# NARNA Mobile API Integration

This document describes the integration between the NARNA mobile API endpoints and the agent runtime.

## Overview

The mobile API provides a MausBot-style remote control interface for iOS/Android apps to interact with NARNA agents. The integration replaces stub implementations with real agent sessions, persistent storage, and WebSocket event forwarding.

## Architecture

```
┌─────────────────┐
│  Mobile App     │
│  (iOS/Android)  │
└────────┬────────┘
         │ HTTPS + WebSocket
         │
┌────────▼────────────────────────────────────────────┐
│  Mobile API (web/backend/app/mobile.py)             │
│  - Pairing endpoints                                │
│  - Bot management (list, thread, send message)      │
│  - Approval gates                                   │
│  - WebSocket streaming                              │
└────────┬────────────────────────────────────────────┘
         │
         ├─────────────┬──────────────┬───────────────┐
         │             │              │               │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌──────▼──────┐
    │ Redis   │   │ PostgreSQL│  │ Agent   │   │ WebSocket   │
    │ Client  │   │ (models)  │  │ Runtime │   │ Manager     │
    └─────────┘   └───────────┘  └─────────┘   └─────────────┘
```

## Components

### 1. Redis Client (`redis_client.py`)

Handles ephemeral data with automatic fallback to in-memory storage:

- **Pairing codes**: 5-minute TTL for device pairing
- **Session tracking**: WebSocket connection management

**Key Functions:**
```python
store_pairing_code(code: str, data: dict, ttl_seconds: int)
get_pairing_code(code: str) -> dict | None
```

### 2. WebSocket Manager (`websocket_manager.py`)

Manages real-time connections between mobile apps and agents:

- **Connection pooling**: Multiple devices per bot
- **Event forwarding**: Agent → Mobile
- **Session mapping**: session_id → bot_id

**Key Functions:**
```python
async def send_to_bot(bot_id: str, message: dict) -> int
async def forward_agent_event(session_id: str, event_type: str, data: dict)
async def notify_approval_required(bot_id: str, approval_id: str, ...)
```

### 3. Database Models (`models.py`)

#### MobileDevice
Stores paired mobile devices with persistent tokens:

```python
class MobileDevice(Base):
    id: int
    org_id: int
    mobile_token: str          # Unique token for auth
    device_name: str           # "John's iPhone"
    platform: str              # "ios" | "android"
    paired_at: datetime
    expires_at: datetime       # 30 days
    last_seen_at: datetime
```

#### ApprovalRequest
Stores agent action approval gates:

```python
class ApprovalRequest(Base):
    id: int
    approval_id: str           # "appr_xxx"
    org_id: int
    bot_id: str
    session_id: str
    action_type: str           # "shell_command" | "file_edit" | "web_action"
    description: str           # Human-readable description
    details_json: str          # Full action details
    status: str                # "pending" | "approved" | "denied"
    decision: str | None
    decided_at: datetime | None
```

### 4. Mobile Agent Bridge (`mobile_agent_bridge.py`)

Bridge between agent runtime and mobile API:

```python
async def request_mobile_approval(
    db: Session,
    org_id: int,
    bot_id: str,
    session_id: str,
    action_type: str,
    description: str,
    details: dict
) -> str  # Returns approval_id

def check_approval_status(db: Session, approval_id: str) -> dict | None

def wait_for_approval(
    db: Session,
    approval_id: str,
    timeout_seconds: int = 300
) -> bool
```

## API Endpoints

### Pairing Flow

#### 1. Start Pairing
```http
POST /v1/mobile/pairing/start
X-API-Key: <org_api_key>

{
  "device_name": "John's iPhone",
  "platform": "ios"
}
```

**Response:**
```json
{
  "pairing_code": "123456",
  "qr_data": "narna://pair?code=123456&org=dev",
  "expires_at": "2024-01-01T12:05:00Z"
}
```

**Implementation:**
- Generates 6-digit code
- Stores in Redis with 5-minute TTL
- Returns QR code data for scanning

#### 2. Verify Pairing
```http
POST /v1/mobile/pairing/verify

{
  "pairing_code": "123456"
}
```

**Response:**
```json
{
  "mobile_token": "narna_mobile_xxx",
  "agent_name": "dev",
  "org_id": 1
}
```

**Implementation:**
- Retrieves pairing data from Redis
- Creates MobileDevice record in PostgreSQL
- Returns 30-day token
- Deletes pairing code

#### 3. Revoke Token
```http
DELETE /v1/mobile/pairing/revoke
X-API-Key: <org_api_key>

{
  "mobile_token": "narna_mobile_xxx"
}
```

### Bot Management

#### List Bots
```http
GET /v1/mobile/bots?mobile_token=<token>
```

**Response:**
```json
[
  {
    "bot_id": "sess_abc123",
    "name": "NARNA Assistant",
    "model": "claude-3.5-sonnet",
    "status": "idle",
    "last_message_at": "2024-01-01T12:00:00Z"
  }
]
```

**Implementation:**
- Queries agent sessions from workspace
- Reads session JSON files
- Determines status from recent activity
- Returns default bot if no sessions exist

#### Get Thread
```http
GET /v1/mobile/bots/{bot_id}/thread?mobile_token=<token>&limit=50
```

**Response:**
```json
{
  "bot_id": "sess_abc123",
  "thread_id": "sess_abc123",
  "messages": [
    {
      "message_id": "msg_0_2024-01-01T12:00:00Z",
      "role": "user",
      "content": "Hello!",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

**Implementation:**
- Loads session from AgentSessionStore
- Formats messages for mobile display
- Returns last N messages

#### Send Message
```http
POST /v1/mobile/bots/{bot_id}/message?mobile_token=<token>

{
  "message": "What's the weather?",
  "thread_id": "sess_abc123"
}
```

**Response:**
```json
{
  "thread_id": "sess_abc123",
  "message_id": "msg_1234567890",
  "status": "completed"
}
```

**Implementation:**
- Registers session with WebSocket manager
- Sends "processing" status via WebSocket
- Calls agent.ask() in thread pool
- Streams response back via WebSocket
- Returns completion status

### Approval Gates

#### List Approvals
```http
GET /v1/mobile/approvals?mobile_token=<token>
```

**Response:**
```json
[
  {
    "approval_id": "appr_abc123",
    "bot_id": "sess_abc123",
    "action_type": "shell_command",
    "description": "Run: pip install requests",
    "details": {
      "command": "pip install requests",
      "cwd": "/workspace"
    },
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

#### Allow Approval
```http
POST /v1/mobile/approvals/{approval_id}/allow?mobile_token=<token>
```

**Response:**
```json
{
  "approval_id": "appr_abc123",
  "decision": "allowed"
}
```

**Implementation:**
- Updates approval status in database
- Sends decision via WebSocket
- Agent runtime continues execution

#### Deny Approval
```http
POST /v1/mobile/approvals/{approval_id}/deny?mobile_token=<token>
```

### WebSocket Streaming

```
WS /v1/mobile/bots/{bot_id}/stream?mobile_token=<token>
```

**Client → Server:**
```json
"ping"
```

**Server → Client:**
```json
{
  "type": "connected",
  "bot_id": "sess_abc123",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Event Types:**

1. **Status Update**
```json
{
  "type": "status",
  "status": "processing",
  "message": "Processing your request...",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

2. **Message**
```json
{
  "type": "message",
  "role": "assistant",
  "content": "The weather is sunny!",
  "message_id": "msg_123",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

3. **Approval Required**
```json
{
  "type": "approval_required",
  "approval_id": "appr_abc123",
  "action_type": "shell_command",
  "description": "Run: pip install requests",
  "details": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

4. **Tool Execution**
```json
{
  "type": "tool_execution",
  "tool_name": "search_web",
  "status": "running",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

5. **Error**
```json
{
  "type": "error",
  "error": "Rate limit exceeded",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Integration with Agent Runtime

### Message Flow

```
Mobile App → API → Agent Runtime → API → Mobile App
```

1. **Mobile sends message**
   - POST /v1/mobile/bots/{bot_id}/message
   - API validates token
   - WebSocket manager sends "processing" status

2. **Agent processes**
   - agent.ask() called in thread pool
   - Tools executed
   - Approvals requested via mobile_agent_bridge

3. **Response streamed**
   - WebSocket events forwarded
   - Final response sent
   - Status updated to "completed"

### Approval Flow

```
Agent Runtime → mobile_agent_bridge → Database + WebSocket → Mobile App
```

1. **Agent needs approval**
   - Calls request_mobile_approval()
   - Creates ApprovalRequest in DB
   - Sends WebSocket event

2. **User decides on mobile**
   - POST /v1/mobile/approvals/{id}/allow or /deny
   - Updates DB
   - Sends decision via WebSocket

3. **Agent continues**
   - wait_for_approval() polls DB
   - Receives decision
   - Continues or aborts action

## Database Migration

Run migration script to create tables:

```bash
python scripts/migrate_mobile_tables.py
```

This creates:
- `mobile_devices` table
- `approval_requests` table

## Testing

### 1. Run Migration
```bash
python scripts/migrate_mobile_tables.py
```

### 2. Start Backend
```bash
cd web/backend
uvicorn app.main:app --reload --port 8000
```

### 3. Run Tests
```bash
python scripts/test_mobile_integration.py <your_api_key>
```

Test script covers:
- ✅ Pairing flow (start → verify)
- ✅ List bots
- ✅ Get thread
- ✅ Send message
- ✅ List approvals
- ✅ WebSocket connection
- ✅ Revoke token

## Environment Variables

```bash
# Redis (optional, falls back to in-memory)
REDIS_URL=redis://localhost:6379/0

# Database
UAP_DATABASE_URL=sqlite:///./uap_cloud.db
# or PostgreSQL:
# UAP_DATABASE_URL=postgresql://user:pass@localhost/narna

# Agent workspace
UAP_HOME=~/.narna
```

## Security Considerations

1. **Token Expiry**: Mobile tokens expire after 30 days
2. **Pairing TTL**: Pairing codes expire after 5 minutes
3. **Org Isolation**: All queries filtered by org_id
4. **WebSocket Auth**: Token verified on connection
5. **HTTPS Required**: Use TLS in production

## Future Enhancements

- [ ] Push notifications for approvals
- [ ] Multi-device sync
- [ ] Token refresh mechanism
- [ ] Rate limiting per device
- [ ] Audit log for mobile actions
- [ ] Biometric approval gates
- [ ] Offline message queue

## Troubleshooting

### Redis Connection Failed
- Check REDIS_URL environment variable
- Falls back to in-memory storage automatically
- Pairing codes only valid in current process

### WebSocket Disconnects
- Check network connectivity
- Implement reconnection logic in mobile app
- Events are not persisted, only real-time

### Agent Not Responding
- Verify UAP_HOME workspace exists
- Check agent runtime logs
- Ensure organization has API key configured

### Approval Timeout
- Default timeout: 5 minutes
- Mobile app must be active
- Consider push notifications for production
