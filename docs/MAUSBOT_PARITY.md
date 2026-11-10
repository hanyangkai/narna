# NARNA Mobile ↔ MausBot / GrokBot Parity

**Target**: Companion-app experience comparable to MausBot (chat, approvals, inbox, routines, voice, remote, connected apps).

## Feature matrix

| Feature | MausBot | NARNA Mobile | Status |
|---------|---------|--------------|--------|
| QR / code pairing | ✅ | ✅ | Done |
| Bot list + chat | ✅ | ✅ | Done |
| Approval Allow/Deny | ✅ | ✅ | Done |
| Cross-bot Inbox | ✅ | ✅ | API + UI (agents) |
| Routines / schedule | ✅ | ✅ | API + UI (agents) |
| Voice / Live call | ✅ | ✅ | Session API + UI shell (Realtime key BYOK) |
| Remote (Tailscale / HTTPS) | ✅ | ✅ | Config API + Settings |
| Connected apps | ✅ | ✅ | Placeholder connect (OAuth later) |
| Push approvals | ✅ | ✅ | Device register API (APNs/FCM wire later) |
| Multi-bot channels | ✅ | 🟡 | Multi-bot list; channel rooms TBD |

## New APIs (`web/backend/app/mobile_parity.py`)

- `GET /v1/mobile/inbox`
- `GET|POST /v1/mobile/routines`, `POST .../toggle`, `DELETE ...`
- `POST /v1/mobile/voice/start|stop`
- `GET|PUT /v1/mobile/remote/status|config`
- `GET /v1/mobile/connected-apps`, `POST .../connect|disconnect`
- `POST /v1/mobile/push/register`
- `GET /v1/mobile/parity`

All require `mobile_token` query param from pairing.

## Remaining production hardening

1. Persist routines/remote/apps in Postgres (not in-memory)
2. Real OAuth for Gmail/Slack/GitHub/Notion/Linear
3. OpenAI Realtime audio bridge on client
4. APNs + FCM delivery for approval pushes
5. Visual QA against MausBot screenshots on device
