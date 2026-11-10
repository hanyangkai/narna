# Multi-Agent Build Plan: NARNA Mobile Apps

## Objective

Build complete iOS + Android apps with MausBot/GrokBot functionality, then auto-submit to App Store & Google Play using parallel agent teams.

---

## Agent Team Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    COORDINATOR AGENT                        │
│  - Orchestrate 6 parallel agents                           │
│  - Merge code from all agents                              │
│  - Final QA & submission coordination                       │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
   │ AGENT 1 │      │ AGENT 2   │     │ AGENT 3   │
   │ iOS App │      │Android App│     │ Backend   │
   └─────────┘      └───────────┘     └───────────┘
        │                  │                  │
   ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
   │ AGENT 4 │      │ AGENT 5   │     │ AGENT 6   │
   │Testing  │      │App Store  │     │Play Store │
   └─────────┘      └───────────┘     └───────────┘
```

---

## Agent 1: iOS App Builder

**Responsibility**: Build complete iOS app with SwiftUI

**Deliverables**:
- ✅ Xcode project setup
- ✅ Pairing flow (QR scan, code entry)
- ✅ Bot list view
- ✅ Chat interface with real-time updates
- ✅ Approval cards (shell, file, web actions)
- ✅ Settings (AI provider keys, preferences)
- ✅ WebSocket connection manager
- ✅ Keychain storage for tokens
- ✅ Dark mode support

**Tech Stack**:
- Swift 5.9+
- SwiftUI
- Combine
- URLSession
- Keychain
- AVFoundation (QR scanner)

**Timeline**: 2-3 days

---

## Agent 2: Android App Builder

**Responsibility**: Build Android app with Kotlin & Jetpack Compose

**Deliverables**:
- ✅ Android Studio project setup
- ✅ Material Design 3 UI
- ✅ QR scanner with CameraX
- ✅ Bot list (LazyColumn)
- ✅ Chat UI with WebSocket
- ✅ Approval bottom sheets
- ✅ Settings screen
- ✅ Android Keystore for tokens
- ✅ Background service for notifications

**Tech Stack**:
- Kotlin 1.9+
- Jetpack Compose
- Ktor (or Retrofit)
- Coroutines + Flow
- CameraX
- WorkManager

**Timeline**: 2-3 days

---

## Agent 3: Backend Integration

**Responsibility**: Connect mobile APIs to NARNA agent runtime

**Deliverables**:
- ✅ Replace stub data in `mobile.py` with real agent sessions
- ✅ Integrate with `src/uap/desktop_server.py`
- ✅ WebSocket event forwarding from agent → mobile
- ✅ Approval gate queue management
- ✅ Bot session lifecycle (create, pause, resume, stop)
- ✅ Redis/PostgreSQL for mobile token storage

**Timeline**: 1-2 days

---

## Agent 4: Testing & QA

**Responsibility**: Automated testing + screenshot generation

**Deliverables**:
- ✅ iOS UI tests (XCTest)
- ✅ Android instrumentation tests (Espresso)
- ✅ E2E flow tests (pairing → chat → approval)
- ✅ Screenshot automation (fastlane snapshot)
- ✅ TestFlight beta distribution (iOS)
- ✅ Internal testing track (Android)

**Tools**:
- fastlane
- XCTest
- Espresso
- pytest (backend tests)

**Timeline**: 1-2 days

---

## Agent 5: App Store Submission

**Responsibility**: Build iOS IPA + submit to App Store

**Deliverables**:
- ✅ Code signing setup (provisioning profiles, certificates)
- ✅ Build IPA with Xcode Cloud or fastlane
- ✅ App Store metadata (title, description, keywords)
- ✅ Screenshots (iPhone 15 Pro Max, iPad Pro)
- ✅ Privacy policy & terms of service
- ✅ Upload via App Store Connect API or Transporter
- ✅ Submit for review

**Requirements**:
- Apple Developer account credentials
- App Store Connect API key
- Provisioning profiles
- App Icon (1024×1024)
- Privacy policy URL

**Timeline**: 1 day (+ 1-2 weeks App Store review)

---

## Agent 6: Google Play Submission

**Responsibility**: Build Android AAB + submit to Google Play

**Deliverables**:
- ✅ Code signing setup (keystore)
- ✅ Build AAB with Gradle
- ✅ Google Play metadata (title, description, categories)
- ✅ Screenshots (Pixel 8 Pro, tablet)
- ✅ Privacy policy
- ✅ Upload via Google Play Console API
- ✅ Submit for review (Internal → Production)

**Requirements**:
- Google Play Console credentials
- Service account JSON key
- Signing keystore
- Feature graphic (1024×500)
- Privacy policy URL

**Timeline**: 1 day (+ 1-3 days Play Store review)

---

## Parallel Execution Strategy

### Phase 1: Setup (Day 1 morning)
- All 6 agents spawn simultaneously
- Agent 1 creates iOS project structure
- Agent 2 creates Android project structure
- Agent 3 starts backend integration
- Agent 4 sets up test frameworks
- Agent 5 prepares App Store metadata
- Agent 6 prepares Google Play metadata

### Phase 2: Core Development (Day 1 afternoon - Day 3)
- **Agents 1 & 2**: Build UI components in parallel
- **Agent 3**: Integrate with NARNA runtime
- **Agent 4**: Write tests as features complete
- **Agents 5 & 6**: Prepare submission materials

### Phase 3: Integration (Day 4)
- Merge all code into main branch
- Agent 4 runs full test suite
- Fix any integration issues

### Phase 4: Submission (Day 5)
- Agent 5 builds IPA → uploads to App Store
- Agent 6 builds AAB → uploads to Google Play
- Both submit for review

---

## Automated Submission Process

### App Store (fastlane + App Store Connect API)

```ruby
# fastlane/Fastfile
lane :submit_to_app_store do
  # Build IPA
  gym(
    scheme: "NARNA",
    export_method: "app-store",
    output_directory: "./build"
  )
  
  # Upload metadata & screenshots
  deliver(
    metadata_path: "./fastlane/metadata",
    screenshots_path: "./fastlane/screenshots",
    skip_binary_upload: false,
    submit_for_review: true,
    automatic_release: false,
    submission_information: {
      export_compliance_uses_encryption: false,
      add_id_info_uses_idfa: false
    }
  )
end
```

### Google Play (Gradle + Play Console API)

```kotlin
// app/build.gradle.kts
play {
    serviceAccountCredentials.set(file("../service-account.json"))
    track.set("production")
    releaseStatus.set(com.github.triplet.gradle.androidpublisher.ReleaseStatus.COMPLETED)
}
```

```bash
./gradlew bundleRelease publishBundle
```

---

## Credentials Required

### Apple Developer Account
- [ ] Apple ID (already have)
- [ ] App Store Connect API Key (.p8 file)
- [ ] Team ID
- [ ] App ID (bundle identifier: `org.narna.mobile`)
- [ ] Provisioning profile
- [ ] Distribution certificate

### Google Play Console
- [ ] Google Play Console login (already have)
- [ ] Service account JSON key
- [ ] App signing keystore
- [ ] Package name: `org.narna.mobile`

---

## App Store Listing (Draft)

### iOS App

**Title**: NARNA Mobile - AI Agent Bot  
**Subtitle**: Remote control for your AI agents  
**Description**:
```
NARNA Mobile lets you control powerful AI agents from your phone. 

FEATURES:
• Connect to desktop or cloud agents
• Chat with Claude, ChatGPT, Gemini bots
• Approve shell commands and file edits
• Real-time updates via WebSocket
• QR code pairing
• Secure end-to-end encryption

BRING YOUR OWN AI:
• Claude Pro / API key
• ChatGPT Plus / API key
• Gemini / API key
• DeepSeek, Qwen, local models

PERFECT FOR:
• Developers running AI agents on servers
• Automation enthusiasts
• Power users who want mobile access

FREE AND OPEN SOURCE
NARNA is MIT licensed. Visit narna.org to learn more.
```

**Keywords**: AI, agent, bot, automation, Claude, ChatGPT, Gemini, remote, developer  
**Category**: Productivity  
**Price**: Free

### Android App (Google Play)

Same title/description, category: Productivity

---

## Screenshots to Generate

### iOS (6 required)
1. Pairing screen (QR code)
2. Bot list
3. Chat conversation
4. Approval card (shell command)
5. Settings screen
6. Real-time updates

### Android (8 required)
Same as iOS + tablet versions

---

## Timeline Summary

| Day | Activity | Status |
|-----|----------|--------|
| 1 | Spawn 6 agents, setup projects | 🚀 Starting |
| 2-3 | Parallel development | 📋 Planned |
| 4 | Integration & testing | 📋 Planned |
| 5 | Submission to stores | 📋 Planned |
| 6-20 | Store review (Apple 7-14 days, Google 1-3 days) | ⏳ Waiting |

**Total active development**: 5 days  
**Total to app store availability**: 7-21 days (including reviews)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| App Store rejection | Follow guidelines strictly, privacy policy ready |
| Build failures | CI/CD with GitHub Actions, test before submission |
| Certificate issues | Auto-manage signing with Xcode, store backups |
| API rate limits | Implement retry logic, show user-friendly errors |
| WebSocket disconnects | Auto-reconnect with exponential backoff |

---

## Post-Launch Monitoring

After submission:
- [ ] Monitor App Store Connect for review status
- [ ] Monitor Google Play Console for review status
- [ ] Set up crash reporting (Sentry)
- [ ] Set up analytics (Firebase or custom)
- [ ] Prepare update pipeline (fastlane lanes)

---

## Next Steps

1. ✅ Confirm credentials available:
   - Apple Developer account login
   - Google Play Console login
   - App Store Connect API key
   - Play Console service account JSON

2. 🚀 Spawn Agent 1: iOS App Builder
3. 🚀 Spawn Agent 2: Android App Builder
4. 🚀 Spawn Agent 3: Backend Integration
5. 🚀 Spawn Agent 4: Testing & QA
6. 🚀 Spawn Agent 5: App Store Submission
7. 🚀 Spawn Agent 6: Google Play Submission

**Ready to launch? Type 'GO' to spawn all 6 agents!**
