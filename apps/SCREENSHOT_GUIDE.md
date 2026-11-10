# NARNA Mobile - Screenshot Generation Guide

**Priority:** Store submissions require screenshots immediately!

This guide provides step-by-step instructions for generating high-quality screenshots for App Store and Play Store submissions.

---

## Quick Start

### iOS
```bash
cd apps/mobile-ios
bundle install
bundle exec fastlane snapshot

# Or manual:
./scripts/generate_screenshots.sh ios
```

### Android
```bash
cd apps/mobile-android
./gradlew assembleDebug assembleDebugAndroidTest
bundle install
bundle exec fastlane screengrab

# Or manual:
./scripts/generate_screenshots.sh android
```

---

## Screenshot Requirements

### iOS App Store
- **Devices:** iPhone 15 Pro Max, iPhone 15, iPad Pro 12.9"
- **Resolutions:**
  - iPhone 15 Pro Max: 1290 x 2796 px
  - iPhone 15: 1179 x 2556 px
  - iPad Pro 12.9": 2048 x 2732 px
- **Format:** PNG
- **Count:** 6-10 screenshots per device

### Google Play Store
- **Devices:** Pixel 8 Pro (phone), 10" tablet
- **Resolutions:**
  - Phone: 1344 x 2992 px
  - Tablet: 1920 x 1200 px
- **Format:** PNG or JPEG
- **Count:** Minimum 2, maximum 8 per device type

---

## Screenshot List

### Screen 1: Pairing (`01_pairing.png`)
**What to show:**
- QR code scanner camera view
- "Scan QR Code" title
- Manual code entry field below (6 digits)
- "Or enter code manually" subtitle
- Clean UI with NARNA branding

**How to capture:**
1. Launch app (fresh install)
2. Ensure pairing screen is visible
3. If using real QR: Start desktop agent with `narna mobile-pair` to generate code
4. Mock QR code is fine for screenshot
5. Capture full screen

**Key elements:**
- QR code scanning frame
- Manual entry alternative
- Clean, uncluttered design

---

### Screen 2: Bot List (`02_bot_list.png`)
**What to show:**
- 2-3 active bots in list view
- Each bot card shows:
  - Bot name (e.g., "NARNA Assistant", "NARNA Slack")
  - Model (e.g., "claude-3.5-sonnet")
  - Status badge (idle/working/waiting approval)
  - Last message timestamp
- Pull-to-refresh indicator (optional)
- Navigation bar with "Agents" title

**How to capture:**
1. Complete pairing
2. Start 2-3 agent sessions on desktop
3. Wait for bots to appear in list
4. Capture with varied statuses:
   - One bot "idle" (green)
   - One bot "working" (yellow)
   - One bot "waiting approval" (red)

**Mock data:**
```json
[
  {
    "name": "NARNA Assistant",
    "model": "claude-3.5-sonnet",
    "status": "idle",
    "last_message": "2 minutes ago"
  },
  {
    "name": "NARNA Slack",
    "model": "gpt-4",
    "status": "working",
    "last_message": "Just now"
  },
  {
    "name": "NARNA GitHub",
    "model": "gemini-pro",
    "status": "waiting approval",
    "last_message": "10 seconds ago"
  }
]
```

---

### Screen 3: Chat Conversation (`03_chat.png`)
**What to show:**
- Full chat conversation with 4-6 messages
- Alternating user and assistant messages
- User messages on right (blue/primary color)
- Assistant messages on left (gray/secondary)
- Timestamps
- Text input field at bottom
- "Send" button
- Optional: Typing indicator

**How to capture:**
1. Tap a bot from list
2. Send 2-3 messages
3. Scroll to show conversation
4. Capture with good message variety:
   - Short message ("Hello")
   - Medium message (question)
   - Long response (paragraph)

**Sample conversation:**
```
You: Hello! Can you help me with a task?
Assistant: Of course! I'd be happy to help. What would you like to work on?
You: Run ls command in /workspace
Assistant: I'll run that command for you. Let me check the directory contents...
```

---

### Screen 4: Approval Card (`04_approval.png`)
**What to show:**
- Approval request overlay/modal/bottom sheet
- Action type badge (e.g., "Shell Command")
- Description text
- Command preview (code block)
- "Allow" button (green)
- "Deny" button (red)
- Timestamp

**How to capture:**
1. In chat, ask bot to run a shell command
2. Agent will request approval
3. Approval card/sheet appears
4. Capture before making decision

**iOS:** Card overlay with blur background  
**Android:** Bottom sheet from bottom edge

**Sample approval:**
```
Action: Shell Command
Command: ls -la /workspace
Working Directory: /workspace
Requested: 2 seconds ago

[Allow] [Deny]
```

---

### Screen 5: Settings (`05_settings.png`)
**What to show:**
- Settings screen with sections:
  - **Device Info:**
    - Device name
    - Paired agent name
    - Paired date
  - **API Keys:** (show as configured/unconfigured)
    - Anthropic API Key
    - OpenAI API Key
    - Google AI API Key
  - **Actions:**
    - Unpair Device button (destructive)
  - **About:**
    - Version number
    - Open source license
    - Links (website, support)

**How to capture:**
1. Tap settings icon (gear) in navigation
2. Scroll to show full screen
3. Ensure all sections visible

**iOS:** Standard iOS settings style  
**Android:** Material Design preferences

---

### Screen 6: Real-time Updates (`06_realtime.png`)
**What to show:**
- Chat screen with real-time indicators:
  - Typing indicator ("Assistant is typing...")
  - Or streaming message appearing
  - Or status badge updating live
- Emphasizes WebSocket real-time feature

**How to capture:**
1. Send message that triggers long response
2. Capture typing indicator immediately
3. Or capture mid-stream message update

**Alternative:** Show approval notification appearing as system notification

---

### Screen 7: Tablet Landscape (`07_tablet_landscape.png`) - Android Only
**What to show:**
- Split screen layout on tablet
- Left pane: Bot list
- Right pane: Chat conversation
- Master-detail UI pattern

**How to capture:**
1. Launch app on 10" tablet emulator
2. Rotate to landscape (Ctrl+F11)
3. Select a bot to show split view
4. Capture full screen

---

### Screen 8: Tablet Portrait (`08_tablet_portrait.png`) - Android Only
**What to show:**
- Tablet in portrait mode
- Same as phone but larger, more spacious
- Chat conversation with larger text
- More messages visible

**How to capture:**
1. Keep tablet in portrait
2. Show chat conversation
3. Capture full screen

---

## Best Practices

### Lighting & Contrast
- Use light mode for screenshots (dark mode optional)
- Ensure text is readable
- High contrast between background and foreground

### Status Bar
- Clean status bar (no notifications)
- Full battery icon
- Strong WiFi signal
- Use Fastlane's `override_status_bar: true`

### Content
- Use realistic but clean data
- No profanity or sensitive info
- Varied message lengths
- Professional tone

### Timing
- Show active states (not empty/loading)
- Multiple bots in list (not just one)
- Conversation in progress (not idle)

### Localization
- Primary: English (en-US)
- Optional: Vietnamese, Spanish, Chinese
- Use same screen sequence for each locale

---

## Automated Screenshot Generation

### iOS with Fastlane Snapshot

1. **Create UI Test:**
```swift
// NARNAUITests/ScreenshotTests.swift
import XCTest

class ScreenshotTests: XCTestCase {
    override func setUp() {
        super.setUp()
        let app = XCUIApplication()
        setupSnapshot(app)
        app.launch()
    }
    
    func testGenerateScreenshots() {
        let app = XCUIApplication()
        
        // 1. Pairing screen
        snapshot("01_pairing")
        
        // Mock pairing (if backend running)
        // ... enter code or scan QR
        
        // 2. Bot list
        snapshot("02_bot_list")
        
        // 3. Select first bot
        app.tables.cells.firstMatch.tap()
        snapshot("03_chat")
        
        // 4. Trigger approval (requires backend)
        // snapshot("04_approval")
        
        // 5. Open settings
        app.navigationBars.buttons["Settings"].tap()
        snapshot("05_settings")
        
        // 6. Back to chat for real-time
        app.navigationBars.buttons["Back"].tap()
        snapshot("06_realtime")
    }
}
```

2. **Run:**
```bash
cd apps/mobile-ios
bundle exec fastlane snapshot
```

### Android with Fastlane Screengrab

1. **Create Instrumentation Test:**
```kotlin
// ScreenshotTest.kt
@RunWith(AndroidJUnit4::class)
class ScreenshotTest {
    @Rule
    @JvmField
    val activityRule = ActivityScenarioRule(MainActivity::class.java)
    
    @Test
    fun generateScreenshots() {
        // 1. Pairing screen
        Screengrab.screenshot("01_pairing")
        
        // 2. Bot list (after mock pairing)
        // ... navigate to bot list
        Screengrab.screenshot("02_bot_list")
        
        // 3. Chat
        onView(withId(R.id.bot_list)).perform(click())
        Screengrab.screenshot("03_chat")
        
        // 4. Approval
        // ... trigger approval
        Screengrab.screenshot("04_approval")
        
        // 5. Settings
        onView(withId(R.id.settings_button)).perform(click())
        Screengrab.screenshot("05_settings")
        
        // 6. Real-time
        pressBack()
        Screengrab.screenshot("06_realtime")
    }
}
```

2. **Run:**
```bash
cd apps/mobile-android
./gradlew assembleDebug assembleDebugAndroidTest
bundle exec fastlane screengrab
```

---

## Manual Screenshot Workflow

### iOS Simulator
1. Open Xcode
2. Run app on iPhone 15 Pro Max simulator
3. Navigate to each screen
4. Press `Cmd+S` to save screenshot
5. Screenshots save to `~/Desktop/`
6. Move to `apps/mobile-ios/fastlane/screenshots/en-US/`
7. Rename: `01_pairing.png`, `02_bot_list.png`, etc.

### Android Emulator
1. Open Android Studio
2. Launch Pixel 8 Pro emulator (API 34)
3. Run app
4. Navigate to each screen
5. Click screenshot button in emulator toolbar
6. Or press `Ctrl+S`
7. Move to `apps/mobile-android/fastlane/metadata/android/en-US/images/phoneScreenshots/`
8. Rename: `01_pairing.png`, `02_bot_list.png`, etc.

---

## Image Optimization

Before uploading to stores:

```bash
# Install ImageMagick
brew install imagemagick  # macOS
sudo apt install imagemagick  # Linux

# Optimize all screenshots
cd apps/mobile-ios/fastlane/screenshots/en-US
for img in *.png; do
    convert "$img" -strip -quality 90 -resize 1290x2796 "optimized_$img"
done

# Compress further with pngquant
brew install pngquant
pngquant --quality=80-90 --ext .png --force *.png
```

**Targets:**
- File size: < 5 MB per image
- Format: PNG (lossless)
- No metadata/EXIF

---

## Verification Checklist

Before submission:

- [ ] All 6 iOS screenshots generated (iPhone 15 Pro Max)
- [ ] All 6 iOS screenshots generated (iPhone 15)
- [ ] All 6 iOS screenshots generated (iPad Pro 12.9")
- [ ] All 8 Android screenshots generated (Pixel 8 Pro)
- [ ] All 2 Android tablet screenshots generated (10" tablet)
- [ ] Status bars cleaned up
- [ ] No sensitive data visible
- [ ] Text is readable
- [ ] Images optimized (< 5 MB each)
- [ ] File names follow convention (01_pairing.png, etc.)
- [ ] All images in correct directories

---

## Troubleshooting

### Issue: Fastlane snapshot fails
**Solution:** Run UI tests manually in Xcode to debug

### Issue: Screenshots are blank
**Solution:** Ensure app is fully loaded before snapshot()

### Issue: Approval screen not showing
**Solution:** Requires real backend. Mock with test data or skip for now

### Issue: Images too large
**Solution:** Run ImageMagick optimization script

### Issue: Android screengrab can't find devices
**Solution:** Start emulator first: `emulator -avd Pixel_8_Pro_API_34`

---

## After Screenshot Generation

1. **Review Quality:**
   - Open all images
   - Check readability
   - Verify no errors visible

2. **Upload to Stores:**
   - **iOS:** App Store Connect → App Information → Screenshots
   - **Android:** Play Console → Store Listing → Graphic assets

3. **Add Captions (Optional):**
   - Short, punchy descriptions
   - Highlight key features
   - Match screenshot content

4. **Test on Device:**
   - View store listing on phone
   - Ensure screenshots look good
   - Check load times

---

## Need Help?

- **Fastlane Docs:** https://docs.fastlane.tools
- **Snapshot Guide:** https://docs.fastlane.tools/actions/snapshot/
- **Screengrab Guide:** https://docs.fastlane.tools/actions/screengrab/
- **App Store Guidelines:** https://developer.apple.com/app-store/product-page/
- **Play Store Guidelines:** https://support.google.com/googleplay/android-developer/answer/9866151

---

**Last Updated:** November 10, 2026  
**Status:** Ready for screenshot generation on proper dev environments
