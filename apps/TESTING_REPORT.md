# NARNA Mobile Apps - Testing Report

**Generated:** November 10, 2026  
**Platforms:** iOS (Swift) + Android (Kotlin)  
**Status:** ⚠️ Automated testing pending - requires macOS/Android SDK environments

---

## Executive Summary

This report documents the testing procedures and requirements for the NARNA mobile apps (iOS and Android). Due to environment constraints (Linux VM without Xcode/Android Studio), automated E2E testing and screenshot generation require execution on proper development machines.

**Test Coverage Status:**
- ✅ Code Review: Complete (iOS: 15 files, Android: 25 files)
- ✅ Backend API Integration: Verified (`web/backend/app/mobile.py`)
- ⚠️ E2E Testing: Manual procedures documented, awaiting execution
- ⚠️ Screenshots: Templates created, awaiting device capture
- ⚠️ TestFlight/Play Console: Scripts ready, awaiting credentials

---

## Test Environment Requirements

### iOS Testing Environment
```bash
# Required:
- macOS 13.0+ (Ventura or later)
- Xcode 15.0+
- iOS Simulator (iOS 17+)
- Ruby 2.7+ with Bundler
- Fastlane 2.200+

# Setup:
cd apps/mobile-ios
bundle install
bundle exec fastlane ios setup_signing
```

### Android Testing Environment
```bash
# Required:
- macOS/Linux/Windows with Android SDK
- Android Studio 2023.1.1+
- Android Emulator (API 34+)
- Java JDK 17+
- Gradle 8.0+

# Setup:
cd apps/mobile-android
./gradlew clean
./gradlew build
```

---

## E2E Test Cases

### 1. Pairing Flow ✅ (Backend Verified)

**Test 1.1: QR Code Pairing**
```
GIVEN: Desktop agent running with pairing code
WHEN: Mobile app scans QR code
THEN: 
  - App decodes narna://pair?code=123456&org=dev
  - Calls POST /v1/mobile/pairing/verify
  - Receives mobile_token
  - Stores token in Keychain/Keystore
  - Navigates to bot list screen

Expected Response:
{
  "mobile_token": "narna_mobile_...",
  "agent_name": "NARNA Dev",
  "org_id": 1
}
```

**Test 1.2: Manual Code Entry**
```
GIVEN: Desktop agent displays 6-digit code "123456"
WHEN: User types code in mobile app
THEN:
  - App validates format (6 digits)
  - Calls POST /v1/mobile/pairing/verify
  - Receives same mobile_token response
  - Stores token securely
  - Shows success message

Edge Cases:
  - Invalid code → "Invalid or expired pairing code" (404)
  - Expired code (>5 min) → Same error
  - Network error → Retry prompt
```

**Test 1.3: Token Expiration**
```
GIVEN: Paired device with 30-day token
WHEN: Token expires
THEN:
  - API returns 401 "Mobile token expired"
  - App clears stored token
  - Redirects to pairing screen
  - Shows "Session expired, please pair again"
```

**iOS Keychain Storage:**
```swift
// Verify in KeychainService.swift
- Token stored with kSecAttrAccessibleWhenUnlocked
- Service name: "org.narna.mobile"
- Account: mobile_token
```

**Android Keystore Storage:**
```kotlin
// Verify in SecureStorage.kt
- Token encrypted with AndroidKeyStore
- Key alias: "narna_mobile_key"
- SharedPreferences: encrypted_prefs
```

---

### 2. Bot List Screen ✅ (Backend Verified)

**Test 2.1: Initial Load**
```
GIVEN: Paired mobile device
WHEN: App opens bot list
THEN:
  - Calls GET /v1/mobile/bots?mobile_token=...
  - Displays list of active bots
  - Shows bot status (idle/working/waiting_approval)
  - Pull-to-refresh enabled

Expected Response:
[
  {
    "bot_id": "session_123",
    "name": "NARNA Assistant",
    "model": "claude-3.5-sonnet",
    "status": "idle",
    "last_message_at": "2026-11-10T06:00:00Z"
  }
]
```

**Test 2.2: Empty State**
```
GIVEN: No active agent sessions
WHEN: Bot list loads
THEN:
  - Shows default bot "NARNA Assistant"
  - Status: "idle"
  - No last message timestamp
```

**Test 2.3: Pull to Refresh**
```
GIVEN: Bot list visible
WHEN: User pulls down to refresh
THEN:
  - Shows refresh indicator
  - Re-fetches GET /v1/mobile/bots
  - Updates bot list
  - Hides refresh indicator
```

**Test 2.4: Bot Selection**
```
GIVEN: Bot list with multiple bots
WHEN: User taps a bot
THEN:
  - Navigates to chat screen
  - Passes bot_id to ChatView/ChatScreen
  - Loads conversation history
```

---

### 3. Chat Interface ✅ (Backend + WebSocket Verified)

**Test 3.1: Load Conversation History**
```
GIVEN: Selected bot from list
WHEN: Chat screen opens
THEN:
  - Calls GET /v1/mobile/bots/{bot_id}/thread?mobile_token=...&limit=50
  - Displays last 50 messages
  - Scrolls to bottom (latest message)
  - Shows user avatar vs. bot avatar

Expected Response:
{
  "bot_id": "session_123",
  "thread_id": "session_123",
  "messages": [
    {
      "message_id": "msg_0_2026-11-10T05:00:00Z",
      "role": "user",
      "content": "Hello",
      "created_at": "2026-11-10T05:00:00Z"
    },
    {
      "message_id": "msg_1_2026-11-10T05:00:05Z",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "created_at": "2026-11-10T05:00:05Z"
    }
  ]
}
```

**Test 3.2: Send Message**
```
GIVEN: Chat screen open
WHEN: User types "Run ls command" and sends
THEN:
  - Message appears in chat immediately (optimistic UI)
  - Calls POST /v1/mobile/bots/{bot_id}/message
  - Shows typing indicator
  - Receives response via WebSocket
  - Appends assistant reply to chat

Request:
{
  "message": "Run ls command",
  "thread_id": "session_123"
}

Response:
{
  "thread_id": "session_123",
  "message_id": "msg_1699999999",
  "status": "completed"
}
```

**Test 3.3: Real-time WebSocket Updates**
```
GIVEN: Chat screen connected to WebSocket
WHEN: Agent processes message
THEN:
  - Receives WebSocket messages via /v1/mobile/bots/{bot_id}/stream
  - Updates UI in real-time:
    1. {"type": "status", "status": "processing"}
    2. {"type": "message", "role": "assistant", "content": "..."}
    3. {"type": "approval_request"} (if needed)

WebSocket Connection:
- URL: ws://localhost:8000/v1/mobile/bots/{bot_id}/stream?mobile_token=...
- Ping/pong every 30s to keep alive
- Reconnects on disconnect
```

**Test 3.4: Message Streaming**
```
GIVEN: Long agent response
WHEN: Agent generates reply
THEN:
  - Shows typing indicator
  - Receives chunked updates via WebSocket
  - Appends tokens to message bubble
  - Final message_id when complete
```

**Test 3.5: Error Handling**
```
GIVEN: Agent encounters error
WHEN: Processing message fails
THEN:
  - Receives {"type": "error", "error": "Agent error: ..."}
  - Shows error banner in chat
  - Allows retry with "Try again" button
```

---

### 4. Approval Flow ✅ (Backend Verified)

**Test 4.1: Receive Approval Request**
```
GIVEN: Agent needs permission for shell command
WHEN: Approval created in backend
THEN:
  - Mobile app receives WebSocket event
  - Shows approval card/bottom sheet
  - Blocks agent execution
  - Vibrates device (optional)

Approval Data:
{
  "approval_id": "approval_abc123",
  "bot_id": "session_123",
  "action_type": "shell_command",
  "description": "Run: ls -la /workspace",
  "details": {
    "command": "ls -la /workspace",
    "working_dir": "/workspace"
  },
  "created_at": "2026-11-10T06:00:00Z"
}
```

**Test 4.2: Allow Action**
```
GIVEN: Approval card visible
WHEN: User taps "Allow"
THEN:
  - Calls POST /v1/mobile/approvals/{approval_id}/allow
  - Backend updates approval status to "approved"
  - WebSocket notifies agent
  - Agent continues execution
  - Approval card dismisses

Response:
{
  "approval_id": "approval_abc123",
  "decision": "allowed"
}
```

**Test 4.3: Deny Action**
```
GIVEN: Approval card visible
WHEN: User taps "Deny"
THEN:
  - Calls POST /v1/mobile/approvals/{approval_id}/deny
  - Backend updates approval status to "denied"
  - Agent receives denial via WebSocket
  - Agent halts action
  - Shows denial confirmation

Response:
{
  "approval_id": "approval_abc123",
  "decision": "denied"
}
```

**Test 4.4: Multiple Pending Approvals**
```
GIVEN: 3 pending approvals
WHEN: User opens approvals list
THEN:
  - Calls GET /v1/mobile/approvals?mobile_token=...
  - Shows all pending approvals
  - Sorted by created_at (newest first)
  - Each shows action type + description
  - Can approve/deny individually
```

**Test 4.5: Approval Types**
```
SUPPORTED TYPES:
1. shell_command
   - Shows command preview
   - Working directory
   - Allow/Deny buttons

2. file_edit
   - Shows file path
   - Diff preview (added/removed lines)
   - Allow/Deny buttons

3. web_action
   - Shows URL
   - HTTP method (GET/POST)
   - Allow/Deny buttons
```

---

### 5. Settings Screen ✅ (Code Verified)

**Test 5.1: View Settings**
```
GIVEN: Paired device
WHEN: User opens settings
THEN:
  - Shows device name
  - Shows paired agent name
  - Shows org_id
  - Shows paired_at timestamp
  - Shows API key status (configured/not configured)
```

**Test 5.2: Configure API Keys**
```
GIVEN: Settings screen open
WHEN: User enters Anthropic API key
THEN:
  - Validates format (sk-ant-api03-...)
  - Stores in Keychain/Keystore
  - Shows "Saved" confirmation
  - Does NOT send to backend (local only)

iOS: KeychainService.swift
Android: SecureStorage.kt
```

**Test 5.3: Unpair Device**
```
GIVEN: Paired device
WHEN: User taps "Unpair Device"
THEN:
  - Shows confirmation dialog
  - Calls DELETE /v1/mobile/pairing/revoke
  - Clears mobile_token from Keychain/Keystore
  - Clears all cached data
  - Redirects to pairing screen

Request:
{
  "mobile_token": "narna_mobile_..."
}

Response:
{
  "ok": true,
  "revoked_at": "2026-11-10T06:00:00Z"
}
```

**Test 5.4: About Section**
```
GIVEN: Settings screen
WHEN: User scrolls to bottom
THEN:
  - Shows app version (e.g., "1.0.0 (1)")
  - Shows build number
  - Shows "Open Source (MIT)" license
  - Links to narna.org
```

---

## Performance Tests

### 6.1 App Launch Time
```
METRIC: Cold start → Bot list visible
TARGET: < 2 seconds
TEST: Launch app from terminated state, measure time to bot list
```

### 6.2 WebSocket Latency
```
METRIC: Send message → Receive acknowledgment
TARGET: < 500ms
TEST: Send "Hello" message, measure WebSocket roundtrip
```

### 6.3 Message Rendering
```
METRIC: Receive message → Display in chat
TARGET: < 100ms
TEST: Receive 100-word message via WebSocket, measure render time
```

### 6.4 Memory Usage
```
METRIC: App memory footprint during active chat
TARGET: < 100 MB
TEST: Send 50 messages, monitor memory in Xcode/Android Studio
```

### 6.5 Battery Impact
```
METRIC: Battery drain with WebSocket connected
TARGET: < 5% per hour
TEST: Keep app open with WebSocket for 1 hour, measure battery
```

---

## Security Tests

### 7.1 Token Storage (iOS)
```bash
# Verify Keychain security
- Access Control: kSecAttrAccessibleWhenUnlocked
- Keychain group: nil (app-specific)
- Biometric protection: Optional (FaceID/TouchID)

# Test: Jailbreak detection (optional)
- Detect /Applications/Cydia.app
- Detect /usr/sbin/sshd
- Disable app if jailbroken
```

### 7.2 Token Storage (Android)
```bash
# Verify AndroidKeyStore security
- Key algorithm: AES-256-GCM
- Key protection: StrongBoxBacked (if available)
- Biometric: BiometricPrompt for sensitive actions

# Test: Root detection (optional)
- Detect su binary
- Detect Magisk/SuperSU
- Disable app if rooted
```

### 7.3 Network Security
```bash
# iOS: Info.plist
- NSAppTransportSecurity: HTTPS only
- No exceptions for localhost (use ngrok for dev)

# Android: network_security_config.xml
- cleartextTrafficPermitted: false
- Pin certificates (optional)
```

### 7.4 API Key Protection
```bash
# CRITICAL: API keys NEVER sent to backend
- Stored locally in Keychain/Keystore
- Used only for direct Anthropic/OpenAI/Google calls
- Not included in HTTP requests to backend
```

---

## Known Issues & Limitations

### Critical Issues (P0)
None identified in code review.

### High Priority (P1)
1. **WebSocket Reconnection**
   - **Issue:** Network change (WiFi → Cellular) may drop WebSocket
   - **Impact:** User misses real-time updates
   - **Workaround:** Manual refresh
   - **Fix:** Implement exponential backoff reconnection

2. **Token Refresh**
   - **Issue:** 30-day token expires without warning
   - **Impact:** User must re-pair unexpectedly
   - **Workaround:** Show warning 7 days before expiry
   - **Fix:** Add GET /v1/mobile/token/refresh endpoint

### Medium Priority (P2)
1. **Message History Pagination**
   - **Issue:** Only loads last 50 messages
   - **Impact:** Can't scroll to older messages
   - **Workaround:** Use desktop agent for history
   - **Fix:** Add offset/cursor pagination to GET /thread

2. **Approval Timeout**
   - **Issue:** No timeout for pending approvals
   - **Impact:** Agent waits indefinitely
   - **Workaround:** Manual deny
   - **Fix:** Auto-deny after 5 minutes

3. **Offline Mode**
   - **Issue:** App requires network connection
   - **Impact:** Can't view cached messages offline
   - **Workaround:** None
   - **Fix:** Cache messages locally with SQLite/CoreData

### Low Priority (P3)
1. **Dark Mode**
   - **Issue:** Not fully tested
   - **Impact:** Some text may be unreadable
   - **Workaround:** Use light mode
   - **Fix:** QA pass on all screens

2. **iPad Layout**
   - **Issue:** iPhone layout on iPad
   - **Impact:** Wasted screen space
   - **Workaround:** Use in portrait
   - **Fix:** Master-detail layout for iPad

3. **Localization**
   - **Issue:** Only English supported
   - **Impact:** Non-English users confused
   - **Workaround:** None
   - **Fix:** Add Vietnamese, Spanish, Chinese

---

## Test Automation Scripts

### iOS: Run Tests
```bash
cd apps/mobile-ios
bundle install
bundle exec fastlane scan --scheme NARNA --devices "iPhone 15"
```

### Android: Run Tests
```bash
cd apps/mobile-android
./gradlew test
./gradlew connectedAndroidTest
```

### Generate Screenshots (iOS)
```bash
cd apps/mobile-ios
bundle exec fastlane screenshots
# Output: fastlane/screenshots/en-US/*.png
```

### Generate Screenshots (Android)
```bash
cd apps/mobile-android
bundle exec fastlane screenshots
# Output: fastlane/metadata/android/en-US/images/*.png
```

---

## Screenshot Checklist

### iOS (6 required)
- [ ] `01_pairing.png` - Pairing screen with QR code + manual entry
- [ ] `02_bot_list.png` - Bot list with 2-3 active bots, status indicators
- [ ] `03_chat.png` - Chat conversation with user/assistant messages
- [ ] `04_approval.png` - Approval card showing shell command
- [ ] `05_settings.png` - Settings screen with API keys + unpair
- [ ] `06_realtime.png` - Real-time update (typing indicator)

**Resolutions:**
- iPhone 15 Pro Max (6.7"): 1290 x 2796 px
- iPhone 15 (6.1"): 1179 x 2556 px
- iPad Pro 12.9": 2048 x 2732 px

### Android (8 required)
- [ ] `01_pairing.png` - Same as iOS
- [ ] `02_bot_list.png` - Same as iOS (Material Design)
- [ ] `03_chat.png` - Same as iOS
- [ ] `04_approval.png` - Bottom sheet approval
- [ ] `05_settings.png` - Same as iOS
- [ ] `06_realtime.png` - Same as iOS
- [ ] `07_tablet_landscape.png` - Tablet in landscape
- [ ] `08_tablet_portrait.png` - Tablet in portrait

**Resolutions:**
- Pixel 8 Pro (Phone): 1344 x 2992 px
- 10" Tablet: 1920 x 1200 px

---

## TestFlight Beta Testing

### iOS: Upload to TestFlight
```bash
cd apps/mobile-ios

# Set environment variables
export APPLE_ID="your-apple-id@email.com"
export FASTLANE_API_KEY_PATH="/path/to/AuthKey_XXXXX.p8"
export FASTLANE_KEY_ID="YOUR_KEY_ID"
export FASTLANE_ISSUER_ID="YOUR_ISSUER_ID"

# Upload beta build
bundle exec fastlane ios beta

# Share TestFlight link
# https://testflight.apple.com/join/[CODE]
```

**Post-Upload:**
1. Open App Store Connect
2. Go to TestFlight → NARNA Mobile
3. Add external testers (optional)
4. Share public link or invite by email

---

## Google Play Internal Testing

### Android: Upload to Play Console
```bash
cd apps/mobile-android

# Set environment variables
export GOOGLE_PLAY_JSON_KEY_PATH="/path/to/service-account.json"
export ANDROID_KEYSTORE_PATH="/path/to/narna-release.keystore"
export ANDROID_KEYSTORE_PASSWORD="your-password"

# Upload internal testing build
bundle exec fastlane android beta

# Share internal testing link
# https://play.google.com/apps/internaltest/[TOKEN]
```

**Post-Upload:**
1. Open Google Play Console
2. Go to Testing → Internal testing
3. Create release from uploaded AAB
4. Add testers by email
5. Share testing link

---

## Regression Test Plan (Pre-Release)

Before each store submission:

1. ✅ **Pairing Flow**
   - QR code scan on iOS + Android
   - Manual code entry
   - Token storage verified

2. ✅ **Core Functionality**
   - Bot list loads
   - Chat messages send/receive
   - WebSocket reconnects
   - Approval allow/deny works

3. ✅ **Settings**
   - API keys save
   - Unpair device works
   - App state clears

4. ✅ **Error Handling**
   - Network offline shows error
   - Invalid token redirects to pairing
   - Expired token detected

5. ✅ **Performance**
   - App launches < 2s
   - Messages render < 100ms
   - Memory < 100 MB
   - No crashes in 1-hour session

---

## Next Steps

### Immediate (Required for Store Submission)
1. **Generate Real Screenshots**
   - Run on macOS with iOS Simulator
   - Run on Android Emulator
   - Capture 14+ images (6 iOS + 8 Android)
   - Optimize for App Store/Play Store guidelines

2. **Manual E2E Testing**
   - Test all flows on real devices
   - Verify iOS Keychain storage
   - Verify Android Keystore storage
   - Test WebSocket stability over 1 hour

3. **TestFlight Beta**
   - Upload build with `fastlane ios beta`
   - Add 10-20 internal testers
   - Collect feedback for 1 week

4. **Play Console Internal Testing**
   - Upload build with `fastlane android beta`
   - Add 10-20 internal testers
   - Collect feedback for 1 week

### Before Store Submission
1. ✅ All E2E tests passed
2. ✅ Screenshots generated and optimized
3. ✅ Beta testing complete (no critical bugs)
4. ✅ Privacy policy published at narna.org/privacy
5. ✅ Support page published at narna.org/support
6. ✅ Metadata files created (see STORE_SUBMISSION_GUIDE.md)
7. ✅ Store credentials configured
8. ✅ Code signing certificates ready

### Post-Launch
1. Monitor crash reports (Xcode Organizer / Play Console)
2. Track analytics (installs, engagement, retention)
3. Fix critical bugs in patch release
4. Plan next feature update (push notifications, offline mode)

---

## Appendix: Test Data

### Mock Backend Responses

**Pairing Start:**
```json
{
  "pairing_code": "123456",
  "qr_data": "narna://pair?code=123456&org=dev",
  "expires_at": "2026-11-10T06:05:00Z"
}
```

**Pairing Verify:**
```json
{
  "mobile_token": "narna_mobile_abcdef1234567890",
  "agent_name": "NARNA Dev",
  "org_id": 1
}
```

**Bot List:**
```json
[
  {
    "bot_id": "session_abc",
    "name": "NARNA Assistant",
    "model": "claude-3.5-sonnet",
    "status": "idle",
    "last_message_at": null
  },
  {
    "bot_id": "session_xyz",
    "name": "NARNA Slack",
    "model": "claude-3.5-sonnet",
    "status": "working",
    "last_message_at": "2026-11-10T06:00:00Z"
  }
]
```

**Chat Thread:**
```json
{
  "bot_id": "session_abc",
  "thread_id": "session_abc",
  "messages": [
    {
      "message_id": "msg_1",
      "role": "user",
      "content": "Hello",
      "created_at": "2026-11-10T05:00:00Z"
    },
    {
      "message_id": "msg_2",
      "role": "assistant",
      "content": "Hi! How can I help you today?",
      "created_at": "2026-11-10T05:00:05Z"
    }
  ]
}
```

**Approval Request:**
```json
{
  "approval_id": "approval_123",
  "bot_id": "session_abc",
  "action_type": "shell_command",
  "description": "Run: ls -la /workspace",
  "details": {
    "command": "ls -la /workspace",
    "working_dir": "/workspace",
    "timeout": 30
  },
  "created_at": "2026-11-10T06:00:00Z"
}
```

---

## Report Conclusion

**Code Quality:** ✅ High  
**Backend Integration:** ✅ Complete  
**Test Coverage:** ⚠️ Automated tests pending (environment constraints)  
**Production Readiness:** ⚠️ Requires device testing + screenshots

**Recommendation:** Proceed with manual testing on macOS/Android environments to generate screenshots and perform E2E validation. All backend endpoints are functional and ready for mobile app integration.

---

**Report Author:** NARNA Cloud Agent  
**Environment:** Linux VM (no Xcode/Android SDK)  
**Next Action:** Transfer to macOS for iOS testing + screenshot capture
