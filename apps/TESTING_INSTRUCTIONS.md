# NARNA Mobile Apps - Testing Instructions

**Quick Reference for Testing NARNA iOS and Android Apps**

This document provides practical, step-by-step instructions for testing the mobile apps before store submission.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [iOS Testing](#ios-testing)
4. [Android Testing](#android-testing)
5. [E2E Test Flows](#e2e-test-flows)
6. [Screenshot Generation](#screenshot-generation)
7. [Beta Distribution](#beta-distribution)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Development Machines

**For iOS:**
- macOS 13.0+ (Ventura or later)
- Xcode 15.0+
- CocoaPods or Swift Package Manager
- Ruby 2.7+ with Bundler
- Fastlane 2.200+

**For Android:**
- macOS, Linux, or Windows
- Android Studio 2023.1.1+
- Android SDK Platform 34+
- Java JDK 17+
- Gradle 8.0+

### Backend Setup Required

Both apps require the NARNA backend API running:

```bash
# Start backend server
cd web/backend
python -m uvicorn app.main:app --reload --port 8000

# Verify API health
curl http://localhost:8000/v1/mobile/health
```

Expected response:
```json
{
  "ok": true,
  "service": "narna-mobile-api",
  "version": "0.1.0"
}
```

---

## Backend Setup

### 1. Install Dependencies

```bash
cd web/backend
pip install -r requirements.txt
```

### 2. Configure Database

```bash
# Create database (SQLite by default)
python -m app.database migrate

# Or use PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/narna"
python -m app.database migrate
```

### 3. Generate Test Pairing Code

```bash
# In Python shell
from app.mobile import start_pairing
from app.database import get_db

db = next(get_db())
result = start_pairing({"device_name": "Test iPhone", "platform": "ios"}, org=...)
print(f"Pairing code: {result.pairing_code}")
print(f"QR data: {result.qr_data}")
```

Or use API directly:
```bash
curl -X POST http://localhost:8000/v1/mobile/pairing/start \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"device_name": "Test iPhone", "platform": "ios"}'
```

---

## iOS Testing

### 1. Open Project

```bash
cd apps/mobile-ios/NARNA
open NARNA.xcodeproj
```

### 2. Configure Backend URL

Edit `NARNAAPIService.swift` to point to your backend:

```swift
// For localhost testing (iOS Simulator)
private let baseURL = "http://localhost:8000"

// For device testing (use ngrok or LAN IP)
// private let baseURL = "https://YOUR-NGROK-URL.ngrok.io"
// private let baseURL = "http://192.168.1.100:8000"
```

### 3. Run in Simulator

1. Select target device: iPhone 15 Pro
2. Click "Run" (Cmd+R)
3. Wait for build and app launch

### 4. Run Unit Tests

```bash
cd apps/mobile-ios
xcodebuild test \
  -project NARNA.xcodeproj \
  -scheme NARNA \
  -destination 'platform=iOS Simulator,name=iPhone 15'
```

### 5. Test on Real Device

1. Connect iPhone via USB
2. Select your device in Xcode
3. Click "Run"
4. Trust developer certificate on device if prompted

**Note:** For device testing, backend must be accessible over network (use ngrok or LAN IP).

---

## Android Testing

### 1. Open Project

```bash
cd apps/mobile-android
# Open in Android Studio or use CLI
```

### 2. Configure Backend URL

Edit `NARNAApiService.kt`:

```kotlin
// For localhost testing (Android Emulator)
private const val BASE_URL = "http://10.0.2.2:8000"

// For device testing (use ngrok or LAN IP)
// private const val BASE_URL = "https://YOUR-NGROK-URL.ngrok.io"
// private const val BASE_URL = "http://192.168.1.100:8000"
```

**Note:** Android emulator uses `10.0.2.2` to access host machine's `localhost`.

### 3. Run in Emulator

```bash
# Start emulator
emulator -avd Pixel_8_Pro_API_34 &

# Build and install
./gradlew installDebug

# Or use Android Studio: Run → Run 'app'
```

### 4. Run Unit Tests

```bash
./gradlew test
./gradlew connectedAndroidTest  # Instrumentation tests
```

### 5. Test on Real Device

1. Enable Developer Options on Android device
2. Enable USB Debugging
3. Connect via USB
4. Click "Run" in Android Studio

---

## E2E Test Flows

### Test Flow 1: Pairing

**Backend Setup:**
```bash
# Start backend and generate pairing code
curl -X POST http://localhost:8000/v1/mobile/pairing/start \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"device_name": "Test Device", "platform": "ios"}' | jq .
```

**Mobile App Steps:**
1. ✅ Launch app
2. ✅ See pairing screen
3. ✅ Option A: Scan QR code (use QR generator for `narna://pair?code=...`)
4. ✅ Option B: Enter 6-digit code manually
5. ✅ Tap "Pair"
6. ✅ Verify token stored in Keychain/Keystore
7. ✅ Navigate to bot list

**Expected Result:** Mobile token received and stored, bot list visible.

---

### Test Flow 2: Bot List

**Backend Setup:**
```bash
# Create mock agent sessions (or run real agents)
# Bots will auto-appear in mobile app
```

**Mobile App Steps:**
1. ✅ Open bot list
2. ✅ See at least 1 bot (default "NARNA Assistant")
3. ✅ Pull down to refresh
4. ✅ Verify bot status badges (idle/working)
5. ✅ Tap a bot to open chat

**Expected Result:** Bot list loads with agent sessions.

---

### Test Flow 3: Chat

**Backend Setup:**
```bash
# Backend WebSocket should be running
# No additional setup needed
```

**Mobile App Steps:**
1. ✅ Open chat for a bot
2. ✅ See conversation history (may be empty)
3. ✅ Type message: "Hello"
4. ✅ Tap "Send"
5. ✅ Message appears immediately (optimistic UI)
6. ✅ Wait for assistant response via WebSocket
7. ✅ Response appears in chat
8. ✅ Verify timestamps

**Expected Result:** Real-time chat working with WebSocket.

---

### Test Flow 4: Approvals

**Backend Setup:**
```bash
# Agent needs to request approval
# This happens automatically when agent tries to run shell command
```

**Mobile App Steps:**
1. ✅ In chat, send: "Run ls -la command"
2. ✅ Agent processes and requests approval
3. ✅ Approval card/sheet appears
4. ✅ Shows: Action type, command, description
5. ✅ Tap "Allow"
6. ✅ Approval dismisses
7. ✅ Agent continues execution
8. ✅ Result appears in chat

**Expected Result:** Approval flow works end-to-end.

**Test Denial:**
1. ✅ Request another approval
2. ✅ Tap "Deny"
3. ✅ Verify agent receives denial
4. ✅ Agent stops action

---

### Test Flow 5: Settings

**Mobile App Steps:**
1. ✅ Open settings
2. ✅ See device name, paired agent, org ID
3. ✅ Configure Anthropic API key (optional)
4. ✅ Tap "Save"
5. ✅ Verify key stored in Keychain/Keystore
6. ✅ Tap "Unpair Device"
7. ✅ Confirm dialog
8. ✅ Verify token cleared
9. ✅ Redirected to pairing screen

**Expected Result:** Settings save locally, unpair works.

---

### Test Flow 6: WebSocket Reconnection

**Mobile App Steps:**
1. ✅ Open chat (WebSocket connected)
2. ✅ Turn on Airplane Mode
3. ✅ Verify connection lost indicator
4. ✅ Turn off Airplane Mode
5. ✅ Verify auto-reconnect
6. ✅ Send message to confirm working

**Expected Result:** App reconnects automatically.

---

### Test Flow 7: Token Expiration

**Backend Setup:**
```sql
-- Manually expire token in database for testing
UPDATE mobile_devices 
SET expires_at = NOW() - INTERVAL '1 day' 
WHERE mobile_token = 'test-token';
```

**Mobile App Steps:**
1. ✅ Open app with expired token
2. ✅ API returns 401 error
3. ✅ App clears token
4. ✅ Redirects to pairing screen
5. ✅ Shows "Session expired" message

**Expected Result:** Graceful handling of expired tokens.

---

## Screenshot Generation

### Option 1: Automated (Recommended)

**iOS:**
```bash
cd apps/mobile-ios
bundle install
bundle exec fastlane snapshot
```

**Android:**
```bash
cd apps/mobile-android
./gradlew assembleDebug assembleDebugAndroidTest
bundle install
bundle exec fastlane screengrab
```

### Option 2: Manual Capture

**iOS Simulator:**
1. Run app in iPhone 15 Pro Max simulator
2. Navigate to each screen (pairing, bot list, chat, approval, settings, real-time)
3. Press `Cmd+S` to save screenshot
4. Move to `apps/mobile-ios/fastlane/screenshots/en-US/`
5. Rename: `01_pairing.png`, `02_bot_list.png`, etc.

**Android Emulator:**
1. Run app in Pixel 8 Pro emulator
2. Navigate to each screen
3. Click screenshot button in toolbar (or `Ctrl+S`)
4. Move to `apps/mobile-android/fastlane/metadata/android/en-US/images/phoneScreenshots/`
5. Rename: `01_pairing.png`, `02_bot_list.png`, etc.

### Option 3: Use Scripts

```bash
# iOS
./apps/scripts/generate_screenshots.sh ios

# Android
./apps/scripts/generate_screenshots.sh android

# Both
./apps/scripts/generate_screenshots.sh both
```

See [SCREENSHOT_GUIDE.md](./SCREENSHOT_GUIDE.md) for detailed instructions.

---

## Beta Distribution

### iOS TestFlight

```bash
cd apps/mobile-ios

# Set credentials
export APPLE_ID="your-email@example.com"
export FASTLANE_API_KEY_PATH="/path/to/AuthKey_XXX.p8"
export FASTLANE_KEY_ID="YOUR_KEY_ID"
export FASTLANE_ISSUER_ID="YOUR_ISSUER_ID"

# Upload beta build
bundle exec fastlane ios beta

# Or use script
../scripts/submit_to_testflight.sh
```

**Post-Upload:**
1. Open [App Store Connect](https://appstoreconnect.apple.com)
2. Go to TestFlight → NARNA Mobile
3. Wait for build processing (~10 minutes)
4. Add external testers (optional)
5. Share link: `https://testflight.apple.com/join/[CODE]`

---

### Android Internal Testing

```bash
cd apps/mobile-android

# Set credentials
export GOOGLE_PLAY_JSON_KEY_PATH="/path/to/service-account.json"
export ANDROID_KEYSTORE_PATH="/path/to/keystore.jks"
export ANDROID_KEYSTORE_PASSWORD="your-password"
export ANDROID_KEY_ALIAS="narna"
export ANDROID_KEY_PASSWORD="your-password"

# Upload internal testing build
bundle exec fastlane android beta

# Or use script
../scripts/submit_to_play_console.sh
```

**Post-Upload:**
1. Open [Play Console](https://play.google.com/console)
2. Go to Testing → Internal testing
3. Create release from uploaded AAB
4. Add testers by email
5. Share link: `https://play.google.com/apps/internaltest/[TOKEN]`

---

## Troubleshooting

### iOS: "Could not find Xcode project"
**Solution:** Ensure you're in `apps/mobile-ios` directory.

### iOS: Code signing errors
**Solution:** 
```bash
bundle exec fastlane match nuke distribution
bundle exec fastlane setup_signing
```

### iOS: Simulator not starting
**Solution:** 
```bash
xcrun simctl shutdown all
xcrun simctl erase all
# Restart Xcode
```

### Android: Emulator won't start
**Solution:**
```bash
# Check AVD list
emulator -list-avds

# Delete and recreate
avdmanager delete avd -n Pixel_8_Pro_API_34
avdmanager create avd -n Pixel_8_Pro_API_34 -k "system-images;android-34;google_apis;x86_64"
```

### Android: "10.0.2.2 connection refused"
**Solution:** Ensure backend is running on host machine port 8000.

### Both: WebSocket connection fails
**Solution:**
- Check backend logs: `tail -f web/backend/app.log`
- Verify WebSocket endpoint: `ws://localhost:8000/v1/mobile/bots/{bot_id}/stream`
- Test with `wscat`: `wscat -c "ws://localhost:8000/v1/mobile/bots/test/stream?mobile_token=..."`

### Both: "Invalid or expired mobile token"
**Solution:**
- Re-pair device
- Check token in Keychain/Keystore
- Verify backend database has valid token

---

## Automated Testing Script

Run all tests in sequence:

```bash
#!/bin/bash
# apps/scripts/run_all_tests.sh

echo "🧪 Running NARNA Mobile E2E Tests"

# 1. Start backend
echo "🚀 Starting backend..."
cd web/backend
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 5

# 2. Test iOS
echo "📱 Testing iOS..."
cd apps/mobile-ios
./scripts/test_ios_e2e.sh

# 3. Test Android
echo "🤖 Testing Android..."
cd apps/mobile-android
./scripts/test_android_e2e.sh

# 4. Generate screenshots
echo "📸 Generating screenshots..."
./scripts/generate_screenshots.sh both

# 5. Cleanup
echo "🧹 Cleaning up..."
kill $BACKEND_PID

echo "✅ All tests complete!"
```

---

## Next Steps

After testing:

1. ✅ Review [TESTING_REPORT.md](./TESTING_REPORT.md) for detailed test results
2. ✅ Check [SCREENSHOT_GUIDE.md](./SCREENSHOT_GUIDE.md) for screenshot instructions
3. ✅ Follow [STORE_SUBMISSION_GUIDE.md](./STORE_SUBMISSION_GUIDE.md) for submission
4. ✅ Upload beta builds to TestFlight/Play Console
5. ✅ Collect feedback from internal testers
6. ✅ Fix any critical bugs
7. ✅ Submit to stores for review

---

**Questions?**
- GitHub Issues: https://github.com/hanyangkai/narna/issues
- Documentation: See `apps/` directory for more guides

**Last Updated:** November 10, 2026
