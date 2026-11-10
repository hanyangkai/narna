# NARNA Mobile Agent Bot App - Implementation Plan

## Executive Summary

Package NARNA into a MausBot-style mobile agent bot app with companion iOS/Android apps that connect to desktop/cloud agents, supporting Claude Pro, ChatGPT Pro, and API keys.

**Target**: App Store (iOS) + Google Play (Android)  
**Model**: Desktop companion (like MausBot) + optional cloud hosting  
**Timeline**: 8-12 weeks to MVP

---

## 1. Architecture Overview

### Current NARNA Stack

```
┌─────────────────────────────────────────────┐
│ NARNA Desktop (Local Agent)                 │
│ - FastAPI server on 127.0.0.1:8765         │
│ - Chat UI (browser-based)                   │
│ - BYOK: OpenAI, Anthropic, Gemini, etc.   │
│ - Tools: shell, browser, memory, skills    │
└─────────────────────────────────────────────┘
         ↕
┌─────────────────────────────────────────────┐
│ NARNA Cloud API (api.narna.org)            │
│ - FastAPI backend                           │
│ - PostgreSQL + Redis                        │
│ - Crypto billing (USDC/USDT)               │
│ - Social webhooks                           │
└─────────────────────────────────────────────┘
```

### Proposed Mobile Architecture (MausBot-style)

```
┌─────────────────────────────────────────────┐
│ NARNA Desktop Agent (Host)                  │
│ - FastAPI server (local or cloud)          │
│ - Agent runtime with ADQA                   │
│ - Tools, memory, decision log              │
│ - NEW: Mobile API endpoint                  │
│ - NEW: Pairing service (QR/code)           │
└─────────────────────────────────────────────┘
         ↕ WebSocket + REST
         ↕ (local network or Tailscale/HTTPS)
┌─────────────────────────────────────────────┐
│ NARNA Mobile Companion App                  │
│ iOS (Swift/SwiftUI) + Android (Kotlin)     │
│                                             │
│ Features:                                   │
│ - Chat with bots                            │
│ - View agent work in real-time             │
│ - Approve/deny actions (shell, edits)      │
│ - Voice calls (optional)                    │
│ - Push notifications                        │
│ - QR code pairing                           │
│ - Bot management                            │
└─────────────────────────────────────────────┘
```

---

## 2. Core Features (MVP)

### 2.1 Desktop Agent Enhancements

**New endpoints to add to `web/backend/app/main.py` or `src/uap/desktop_server.py`:**

```python
# Mobile pairing
POST   /v1/mobile/pairing/start       # Generate pairing code/QR
POST   /v1/mobile/pairing/verify      # Verify pairing token
DELETE /v1/mobile/pairing/revoke      # Revoke mobile access

# Mobile API
GET    /v1/mobile/bots                # List active bots
GET    /v1/mobile/bots/{id}/thread    # Get conversation thread
POST   /v1/mobile/bots/{id}/message   # Send message to bot
WS     /v1/mobile/bots/{id}/stream    # Real-time updates

# Approval gates
GET    /v1/mobile/approvals           # Pending approvals
POST   /v1/mobile/approvals/{id}/allow
POST   /v1/mobile/approvals/{id}/deny

# Voice (optional)
POST   /v1/mobile/voice/start         # Start voice call
WS     /v1/mobile/voice/stream        # Audio stream
```

### 2.2 Mobile App Features

#### iOS App (Swift/SwiftUI)
- 📱 Chat interface with bot threads
- 🔔 Push notifications for approvals
- 📷 QR code scanner for pairing
- 🎤 Voice calls (via OpenAI Whisper + TTS)
- 🔐 Biometric lock (Face ID/Touch ID)
- 🌐 Local network + remote (Tailscale) support

#### Android App (Kotlin/Jetpack Compose)
- Same features as iOS
- Material Design 3
- Background service for notifications

---

## 3. AI Provider Integration

### 3.1 BYOK Support (User's Own Accounts)

Users connect their existing AI subscriptions/keys:

| Provider | Connection Method | Notes |
|----------|------------------|-------|
| **Claude Pro** | API key or OAuth | Via Anthropic API (`ANTHROPIC_API_KEY`) |
| **ChatGPT Plus/Pro** | API key | Via OpenAI API (`OPENAI_API_KEY`) |
| **Gemini** | API key | Via Google AI (`GOOGLE_API_KEY`) |
| **DeepSeek** | API key | Self-hosted or cloud |
| **Ollama** | Local | Desktop only, no mobile control |

**Setup flow in mobile app:**
1. User opens Settings → AI Providers
2. Selects provider (Claude/ChatGPT/Gemini)
3. Enters API key or OAuth login
4. Key stored securely on desktop agent (not on phone)
5. Mobile app just triggers agent via desktop

### 3.2 OAuth Flow (for Pro Accounts)

For Claude Pro / ChatGPT Pro account login (not API):

```
Mobile App → Desktop Agent → Provider OAuth
                ↓
         Redirect to provider login
                ↓
         Get access token
                ↓
         Store in desktop keychain
                ↓
         Mobile app confirms success
```

**Note**: Most AI providers prefer API keys over OAuth for agent access. Pro accounts typically get higher rate limits.

---

## 4. Security & Pairing

### 4.1 Pairing Flow (Similar to MausBot)

```
Desktop Agent                     Mobile App
     |                                |
     | Generate pairing code          |
     | (6-digit + expiry)            |
     |-------------------------------->|
     |      Show QR code              | Scan QR or
     |                                | enter code
     |<--------------------------------|
     | Verify code                    |
     |-------------------------------->|
     | Issue JWT token                |
     | (valid 30 days)                |
     |-------------------------------->|
     | Store token                    |
     |                                |
```

**Security:**
- Pairing codes expire in 5 minutes
- JWT tokens valid for 30 days (renewable)
- End-to-end encryption for sensitive data
- User can revoke mobile access anytime

### 4.2 Connection Modes

| Mode | When | How |
|------|------|-----|
| **Local network** | Same WiFi | mDNS discovery + HTTP |
| **Tailscale** | Remote access | MagicDNS name |
| **NARNA Cloud** | Optional hosted | HTTPS to cloud instance |

---

## 5. App Store Submission

### 5.1 iOS App Store

**Requirements:**
- Apple Developer account ($99/year)
- App binary built with Xcode
- Privacy policy & terms of service
- App screenshots & description
- TestFlight beta testing (2 weeks)

**Timeline:**
- Build: 4 weeks
- Testing: 2 weeks
- Review: 1-2 weeks

**Estimated cost**: $99/year

### 5.2 Google Play Store

**Requirements:**
- Google Play Developer account ($25 one-time)
- Android app APK/AAB
- Privacy policy
- Screenshots & description
- Internal/closed testing (1 week)

**Timeline:**
- Build: 4 weeks
- Testing: 1 week
- Review: 1-3 days (faster than iOS)

**Estimated cost**: $25 one-time

---

## 6. Development Roadmap

### Week 1-2: Backend API
- [ ] Add mobile pairing endpoints to NARNA backend
- [ ] Implement JWT-based mobile auth
- [ ] Add WebSocket support for real-time updates
- [ ] Add approval gate endpoints
- [ ] Test with Postman/curl

### Week 3-4: iOS App (MVP)
- [ ] SwiftUI project setup
- [ ] QR code scanning + pairing flow
- [ ] Chat UI with bot threads
- [ ] WebSocket connection to desktop
- [ ] Approval cards (Allow/Deny)
- [ ] Settings: AI provider keys

### Week 5-6: Android App (MVP)
- [ ] Kotlin + Jetpack Compose setup
- [ ] Port iOS features to Android
- [ ] Background service for notifications
- [ ] Material Design UI

### Week 7-8: Testing & Polish
- [ ] TestFlight beta (iOS)
- [ ] Internal testing (Android)
- [ ] Bug fixes
- [ ] UI/UX improvements

### Week 9-10: Advanced Features
- [ ] Voice calls (OpenAI Realtime API)
- [ ] Push notifications (FCM/APNs)
- [ ] Tailscale integration
- [ ] Biometric lock

### Week 11-12: App Store Submission
- [ ] Prepare store listings
- [ ] Screenshots & videos
- [ ] Privacy policy
- [ ] Submit to App Store
- [ ] Submit to Google Play

---

## 7. Monetization (Optional)

Following MausBot model (free app + optional cloud):

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Desktop agent + mobile companion, BYOK only |
| **NARNA Cloud** | $15-20/mo | Hosted agent (computer stays off), unlimited bots |
| **NARNA Pro** | $99/mo | Team features, priority support, white-label |

---

## 8. Tech Stack Summary

### Desktop Agent (Backend)
- Python 3.11+
- FastAPI
- WebSockets
- SQLite (local) or PostgreSQL (cloud)
- JWT auth

### iOS App
- Swift 5.9+
- SwiftUI
- Combine
- URLSession + WebSocket
- Keychain for secure storage

### Android App
- Kotlin 1.9+
- Jetpack Compose
- Coroutines + Flow
- Ktor or Retrofit
- Android Keystore

---

## 9. Comparison with MausBot

| Feature | MausBot | NARNA Mobile (Proposed) |
|---------|---------|-------------------------|
| Desktop agent | Claude/Codex CLI | NARNA agent runtime |
| Mobile apps | iOS + Android | iOS + Android |
| AI providers | Claude, OpenAI, Grok | Claude, OpenAI, Gemini, DeepSeek, Qwen |
| Pairing | QR code | QR code |
| Voice | OpenAI Realtime | OpenAI Realtime (optional) |
| Open source | Yes | Yes (MIT license) |
| App Store | Yes (live) | Planned |
| Cloud hosting | Optional ($15/mo) | Optional (via narna.org) |
| **Unique to NARNA** | — | **ADQA scoring**, Decision Memory, Social channels |

---

## 10. Next Steps

### Immediate Actions (This Week)

1. **Create mobile API branch**
   ```bash
   git checkout -b mobile-api-endpoints
   ```

2. **Prototype mobile endpoints** in `web/backend/app/mobile.py`

3. **Design pairing flow** UI/UX mockups

4. **Set up iOS Xcode project** (Swift/SwiftUI)

5. **Set up Android Studio project** (Kotlin/Compose)

### Questions to Resolve

- [ ] Should we support Ollama (local models) on mobile? (likely desktop-only)
- [ ] Voice calls: OpenAI Realtime API ($0.06/min) or cheaper alternative?
- [ ] Push notifications: self-hosted or use Firebase?
- [ ] Tailscale: require users to set up or provide simpler alternative?

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| App Store rejection | Follow guidelines strictly, have privacy policy |
| Desktop agent compatibility | Test on Windows/Mac/Linux |
| Network connectivity | Support local + remote modes |
| AI provider rate limits | BYOK model shifts cost to users |
| Security vulnerabilities | End-to-end encryption, regular audits |

---

## Appendix: File Structure

```
narna/
├── apps/
│   ├── mobile-ios/              # NEW: iOS app (SwiftUI)
│   │   ├── NARNA.xcodeproj
│   │   ├── NARNA/
│   │   │   ├── Views/
│   │   │   ├── Models/
│   │   │   ├── Services/
│   │   │   └── NARNAApp.swift
│   │   └── README.md
│   └── mobile-android/          # NEW: Android app (Kotlin)
│       ├── app/
│       │   ├── src/main/
│       │   │   ├── kotlin/
│       │   │   └── res/
│       │   └── build.gradle.kts
│       └── README.md
├── web/backend/app/
│   ├── mobile.py                # NEW: Mobile API endpoints
│   ├── pairing.py               # NEW: Pairing service
│   └── main.py                  # Import mobile routes
├── docs/
│   ├── MOBILE-APP-PLAN.md       # This doc
│   ├── MOBILE-API.md            # API specs
│   └── MOBILE-PAIRING.md        # Pairing protocol
└── scripts/
    ├── build_mobile_backend.sh  # Prepare mobile API
    └── test_mobile_api.sh       # E2E tests
```

---

## Conclusion

This plan transforms NARNA into a MausBot-style mobile agent bot app while preserving its unique ADQA decision quality features. The companion app model keeps bots running on powerful desktop/cloud hardware while giving users mobile access.

**Estimated timeline**: 8-12 weeks to MVP  
**Estimated cost**: $124 (Apple $99 + Google $25) + developer time

Ready to proceed with Phase 1: Backend API implementation?
