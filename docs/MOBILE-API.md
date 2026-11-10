# NARNA Mobile API Specification

## Overview

RESTful API + WebSocket for NARNA Mobile companion apps (iOS & Android).

**Base URL**: `http://127.0.0.1:8765` (local) or `https://api.narna.org` (cloud)

---

## Authentication

### Desktop Agent API Key

Desktop-side endpoints require existing NARNA API key:

```bash
Authorization: Bearer uap_live_...
```

### Mobile Token

Mobile-side endpoints require mobile token obtained from pairing:

```bash
?mobile_token=narna_mobile_...
```

Or in request body:
```json
{
  "mobile_token": "narna_mobile_..."
}
```

---

## Pairing Flow

### 1. Start Pairing (Desktop)

**Request**:
```http
POST /v1/mobile/pairing/start
Authorization: Bearer uap_live_...
Content-Type: application/json

{
  "device_name": "iPhone 15 Pro",
  "platform": "ios"
}
```

**Response**:
```json
{
  "pairing_code": "123456",
  "qr_data": "narna://pair?code=123456&org=dev",
  "expires_at": "2026-11-10T13:00:00Z"
}
```

Desktop app displays:
- 6-digit code: `123456`
- QR code with deep link: `narna://pair?code=123456&org=dev`

### 2. Verify Pairing (Mobile)

Mobile app scans QR or enters code, then calls:

**Request**:
```http
POST /v1/mobile/pairing/verify
Content-Type: application/json

{
  "pairing_code": "123456"
}
```

**Response**:
```json
{
  "mobile_token": "narna_mobile_abc123...",
  "agent_name": "dev",
  "org_id": 1
}
```

Mobile app stores `mobile_token` securely (Keychain/Keystore).

### 3. Revoke Pairing (Desktop)

**Request**:
```http
DELETE /v1/mobile/pairing/revoke
Authorization: Bearer uap_live_...
Content-Type: application/json

{
  "mobile_token": "narna_mobile_abc123..."
}
```

**Response**:
```json
{
  "ok": true,
  "revoked_at": "2026-11-10T13:05:00Z"
}
```

---

## Bot Management

### List Bots

**Request**:
```http
GET /v1/mobile/bots?mobile_token=narna_mobile_abc123...
```

**Response**:
```json
[
  {
    "bot_id": "bot_1",
    "name": "NARNA Assistant",
    "model": "claude-3.5-sonnet",
    "status": "idle",
    "last_message_at": "2026-11-10T12:00:00Z"
  },
  {
    "bot_id": "bot_2",
    "name": "Research Bot",
    "model": "gpt-4o",
    "status": "working",
    "last_message_at": "2026-11-10T12:30:00Z"
  }
]
```

**Status values**:
- `idle` - waiting for user input
- `working` - processing request
- `waiting_approval` - pending user approval

### Get Bot Thread

**Request**:
```http
GET /v1/mobile/bots/bot_1/thread?mobile_token=narna_mobile_abc123...&limit=50
```

**Response**:
```json
{
  "bot_id": "bot_1",
  "thread_id": "thread_1",
  "messages": [
    {
      "message_id": "msg_1",
      "role": "user",
      "content": "Hello, NARNA!",
      "created_at": "2026-11-10T12:00:00Z"
    },
    {
      "message_id": "msg_2",
      "role": "assistant",
      "content": "Hello! How can I help you today?",
      "created_at": "2026-11-10T12:00:01Z"
    }
  ]
}
```

### Send Message to Bot

**Request**:
```http
POST /v1/mobile/bots/bot_1/message?mobile_token=narna_mobile_abc123...
Content-Type: application/json

{
  "message": "What's the weather?",
  "thread_id": "thread_1"
}
```

**Response**:
```json
{
  "thread_id": "thread_1",
  "message_id": "msg_3",
  "status": "processing"
}
```

---

## Approval Gates

### List Pending Approvals

**Request**:
```http
GET /v1/mobile/approvals?mobile_token=narna_mobile_abc123...
```

**Response**:
```json
[
  {
    "approval_id": "approval_1",
    "bot_id": "bot_1",
    "action_type": "shell_command",
    "description": "Run: git pull origin main",
    "details": {
      "command": "git pull origin main",
      "working_dir": "/workspace"
    },
    "created_at": "2026-11-10T12:05:00Z"
  },
  {
    "approval_id": "approval_2",
    "bot_id": "bot_2",
    "action_type": "file_edit",
    "description": "Edit: README.md",
    "details": {
      "file_path": "/workspace/README.md",
      "old_content": "...",
      "new_content": "..."
    },
    "created_at": "2026-11-10T12:06:00Z"
  }
]
```

**Action types**:
- `shell_command` - terminal command execution
- `file_edit` - file modification
- `web_action` - browser action (click, type, etc.)

### Allow Approval

**Request**:
```http
POST /v1/mobile/approvals/approval_1/allow?mobile_token=narna_mobile_abc123...
```

**Response**:
```json
{
  "approval_id": "approval_1",
  "decision": "allowed"
}
```

### Deny Approval

**Request**:
```http
POST /v1/mobile/approvals/approval_1/deny?mobile_token=narna_mobile_abc123...
```

**Response**:
```json
{
  "approval_id": "approval_1",
  "decision": "denied"
}
```

---

## Real-time Updates (WebSocket)

### Connect to Bot Stream

**WebSocket URL**:
```
ws://127.0.0.1:8765/v1/mobile/bots/bot_1/stream?mobile_token=narna_mobile_abc123...
```

**Connection established**:
```json
{
  "type": "connected",
  "bot_id": "bot_1",
  "timestamp": "2026-11-10T12:00:00Z"
}
```

**Event types**:

#### Bot Status Update
```json
{
  "type": "status",
  "bot_id": "bot_1",
  "status": "working",
  "timestamp": "2026-11-10T12:00:05Z"
}
```

#### New Message
```json
{
  "type": "message",
  "bot_id": "bot_1",
  "message_id": "msg_4",
  "role": "assistant",
  "content": "The weather is sunny, 25°C.",
  "timestamp": "2026-11-10T12:00:10Z"
}
```

#### Approval Required
```json
{
  "type": "approval_required",
  "approval_id": "approval_3",
  "bot_id": "bot_1",
  "action_type": "shell_command",
  "description": "Run: npm install",
  "details": {
    "command": "npm install",
    "working_dir": "/workspace"
  },
  "timestamp": "2026-11-10T12:00:15Z"
}
```

#### Tool Execution
```json
{
  "type": "tool_execution",
  "bot_id": "bot_1",
  "tool_name": "shell",
  "status": "running",
  "details": {
    "command": "ls -la"
  },
  "timestamp": "2026-11-10T12:00:20Z"
}
```

#### Error
```json
{
  "type": "error",
  "bot_id": "bot_1",
  "error": "Command failed: npm install",
  "details": {},
  "timestamp": "2026-11-10T12:00:25Z"
}
```

---

## Health Check

**Request**:
```http
GET /v1/mobile/health
```

**Response**:
```json
{
  "ok": true,
  "service": "narna-mobile-api",
  "version": "0.1.0",
  "timestamp": "2026-11-10T12:00:00Z"
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Invalid or expired mobile token"
}
```

**HTTP Status Codes**:
- `200` - OK
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (not authorized for resource)
- `404` - Not found
- `410` - Gone (pairing code expired)
- `422` - Validation error
- `500` - Internal server error

---

## Rate Limiting

- Pairing: 10 attempts per 5 minutes per org
- Messages: 60 per minute per mobile token
- Approvals: No limit (time-sensitive)
- WebSocket: 1 connection per bot per mobile token

---

## Security Notes

1. **Pairing codes** expire in 5 minutes
2. **Mobile tokens** valid for 30 days (renewable)
3. **WebSocket** requires valid mobile token
4. **HTTPS required** for remote access (local can use HTTP)
5. **End-to-end encryption** for sensitive data (future)

---

## Example Flow: Send Message from Mobile

```
1. Mobile app: POST /v1/mobile/bots/bot_1/message
   {"message": "Deploy to production"}

2. Backend: Forwards to NARNA agent runtime
   Agent starts processing...

3. Agent needs approval: Sends event via WebSocket
   {"type": "approval_required", "action_type": "shell_command", ...}

4. Mobile app: Shows approval card
   User taps "Allow"

5. Mobile app: POST /v1/mobile/approvals/approval_1/allow

6. Backend: Forwards approval to agent
   Agent executes command

7. Agent completes: Sends event via WebSocket
   {"type": "message", "content": "Deployed successfully!", ...}

8. Mobile app: Shows response in chat
```

---

## Next Steps

- [ ] Implement bot session management (replace stub data)
- [ ] Connect to NARNA agent runtime (`src/uap/desktop_server.py`)
- [ ] Add JWT-based mobile auth (replace in-memory tokens)
- [ ] Implement approval gate queue
- [ ] Add push notifications (FCM/APNs)
- [ ] Voice call support (OpenAI Realtime API)
- [ ] E2E encryption for sensitive data

---

## Testing

```bash
# Start backend
cd web/backend
uvicorn app.main:app --reload --port 8765

# Test pairing (desktop side)
curl -X POST http://localhost:8765/v1/mobile/pairing/start \
  -H "Authorization: Bearer uap_live_dev_local_key_change_in_prod" \
  -H "Content-Type: application/json" \
  -d '{"device_name":"Test iPhone","platform":"ios"}'

# Test pairing verification (mobile side)
curl -X POST http://localhost:8765/v1/mobile/pairing/verify \
  -H "Content-Type: application/json" \
  -d '{"pairing_code":"123456"}'

# Test list bots
curl "http://localhost:8765/v1/mobile/bots?mobile_token=narna_mobile_..."

# Test WebSocket
wscat -c "ws://localhost:8765/v1/mobile/bots/bot_1/stream?mobile_token=narna_mobile_..."
```

---

## Integration with iOS/Android

See:
- `apps/mobile-ios/README.md` - iOS implementation
- `apps/mobile-android/README.md` - Android implementation
