# Android Phone Screenshots for Google Play

Required screenshots for Google Play submission:

## Phone Screenshots (Pixel 8 Pro - 1344 x 2992 px)

### 1. Pairing Screen (`01_pairing.png`)
- **Shows:** QR code scanner + manual code entry field
- **Caption:** "Pair with your desktop or cloud agent in seconds"

### 2. Bot List (`02_bot_list.png`)
- **Shows:** 2-3 active bots with Material Design cards
- **Caption:** "Manage multiple AI agents from one app"

### 3. Chat Conversation (`03_chat.png`)
- **Shows:** Full conversation with Material 3 chat bubbles
- **Caption:** "Chat with Claude, ChatGPT, and Gemini"

### 4. Approval Bottom Sheet (`04_approval.png`)
- **Shows:** Bottom sheet showing approval for shell command
- **Caption:** "Review and approve agent actions in real-time"

### 5. Settings (`05_settings.png`)
- **Shows:** Settings screen with Material Design preferences
- **Caption:** "Secure configuration with Android Keystore"

### 6. Real-time Updates (`06_realtime.png`)
- **Shows:** Chat with typing indicator
- **Caption:** "Live WebSocket updates for instant responses"

---

## Generation Instructions

### Option 1: Automated with Fastlane Screengrab
```bash
cd apps/mobile-android

# Build debug APK
./gradlew assembleDebug

# Build test APK
./gradlew assembleDebugAndroidTest

# Generate screenshots
bundle exec fastlane screengrab
```

### Option 2: Manual Capture
1. Run app in Android Emulator (Pixel 8 Pro API 34)
2. Navigate to each screen
3. Press `Ctrl+S` or use screenshot button
4. Move to `fastlane/metadata/android/en-US/images/phoneScreenshots/`
5. Rename to match naming convention

### Option 3: UI Automator Test
```kotlin
// In ScreenshotTest.kt
@Test
fun generateScreenshots() {
    // 1. Pairing screen
    onView(withId(R.id.pairing_screen)).captureScreenshot("01_pairing")
    
    // 2. Bot list (after pairing)
    // ... navigate to bot list
    onView(withId(R.id.bot_list)).captureScreenshot("02_bot_list")
    
    // ... etc
}
```

---

## Status

- [ ] Generated on Pixel 8 Pro
- [ ] Optimized and compressed
- [ ] Uploaded to Play Console
