# NARNA Mobile - Store Submission Checklist

**Use this checklist to track progress toward App Store and Play Store submissions.**

---

## Pre-Submission Requirements

### 1. Development Complete
- [x] iOS app built (Swift, 15 files, 2,058 LOC)
- [x] Android app built (Kotlin, 25 files, 2,974 LOC)
- [x] Backend API integrated (`web/backend/app/mobile.py`)
- [x] Pairing flow implemented (QR + manual)
- [x] Bot list with status indicators
- [x] Real-time chat with WebSocket
- [x] Approval flow (allow/deny)
- [x] Settings screen with API key management
- [x] Secure storage (Keychain/Keystore)

---

## Testing (⚠️ Requires macOS/Android SDK)

### iOS Testing
- [ ] Run on iOS Simulator (iPhone 15 Pro Max)
- [ ] Run on real iPhone device
- [ ] Test pairing flow end-to-end
- [ ] Test bot list refresh
- [ ] Test chat send/receive
- [ ] Test WebSocket real-time updates
- [ ] Test approval allow/deny
- [ ] Test settings (API keys, unpair)
- [ ] Verify Keychain storage
- [ ] Test token expiration
- [ ] Test WebSocket reconnection
- [ ] Performance test (memory < 100 MB)
- [ ] Battery test (< 5% per hour)

### Android Testing
- [ ] Run on Android Emulator (Pixel 8 Pro)
- [ ] Run on real Android device
- [ ] Test pairing flow end-to-end
- [ ] Test bot list refresh
- [ ] Test chat send/receive
- [ ] Test WebSocket real-time updates
- [ ] Test approval bottom sheet
- [ ] Test settings (API keys, unpair)
- [ ] Verify Keystore storage
- [ ] Test token expiration
- [ ] Test WebSocket reconnection
- [ ] Performance test (memory < 120 MB)
- [ ] Battery test (< 4% per hour)

**Scripts:**
```bash
./apps/scripts/test_ios_e2e.sh
./apps/scripts/test_android_e2e.sh
```

---

## Screenshot Generation (⚠️ Priority!)

### iOS Screenshots (6 required per device)
- [ ] `01_pairing.png` - Pairing screen with QR code
- [ ] `02_bot_list.png` - Bot list with active bots
- [ ] `03_chat.png` - Chat conversation
- [ ] `04_approval.png` - Approval card
- [ ] `05_settings.png` - Settings screen
- [ ] `06_realtime.png` - Real-time updates

**Devices:**
- [ ] iPhone 15 Pro Max (1290 x 2796 px)
- [ ] iPhone 15 (1179 x 2556 px)
- [ ] iPad Pro 12.9" (2048 x 2732 px)

**Generate:**
```bash
cd apps/mobile-ios
bundle exec fastlane snapshot
# Or manual: ./apps/scripts/generate_screenshots.sh ios
```

**Location:** `apps/mobile-ios/fastlane/screenshots/en-US/`

---

### Android Screenshots (8 required)
**Phone (6 screenshots):**
- [ ] `01_pairing.png` - Pairing screen
- [ ] `02_bot_list.png` - Bot list
- [ ] `03_chat.png` - Chat conversation
- [ ] `04_approval.png` - Approval bottom sheet
- [ ] `05_settings.png` - Settings screen
- [ ] `06_realtime.png` - Real-time updates

**Tablet (2 screenshots):**
- [ ] `07_tablet_landscape.png` - Landscape layout
- [ ] `08_tablet_portrait.png` - Portrait layout

**Devices:**
- [ ] Pixel 8 Pro (1344 x 2992 px)
- [ ] 10" Tablet (1920 x 1200 px)

**Generate:**
```bash
cd apps/mobile-android
./gradlew assembleDebug assembleDebugAndroidTest
bundle exec fastlane screengrab
# Or manual: ./apps/scripts/generate_screenshots.sh android
```

**Location:**
- Phone: `apps/mobile-android/fastlane/metadata/android/en-US/images/phoneScreenshots/`
- Tablet: `apps/mobile-android/fastlane/metadata/android/en-US/images/tenInchScreenshots/`

---

## Store Metadata

### iOS Metadata (App Store Connect)
- [x] App name: `NARNA Mobile`
- [x] Subtitle: `AI Agent Remote Control`
- [x] Description: Created in `fastlane/metadata/en-US/description.txt`
- [x] Keywords: `AI,agent,bot,automation,Claude,ChatGPT,remote,developer`
- [x] Privacy URL: `https://narna.org/privacy`
- [x] Support URL: `https://narna.org/support`
- [ ] App icon (1024x1024 px)
- [ ] Screenshots uploaded (6 per device)
- [ ] App Store Connect listing reviewed

**Location:** `apps/mobile-ios/fastlane/metadata/en-US/`

---

### Android Metadata (Play Console)
- [x] App name: `NARNA Mobile`
- [x] Short description: `Remote control for AI agents`
- [x] Full description: Created in `fastlane/metadata/android/en-US/full_description.txt`
- [x] Privacy policy URL: `https://narna.org/privacy`
- [x] Support email: `support@narna.org`
- [ ] Feature graphic (1024x500 px)
- [ ] App icon (512x512 px)
- [ ] Screenshots uploaded (8 total)
- [ ] Play Console listing reviewed

**Location:** `apps/mobile-android/fastlane/metadata/android/en-US/`

---

## Credentials & Signing

### iOS (App Store Connect)
- [ ] Apple Developer Account active ($99/year)
- [ ] App Store Connect API key created
- [ ] `.p8` file downloaded
- [ ] Environment variables set:
  - [ ] `APPLE_ID`
  - [ ] `FASTLANE_API_KEY_PATH`
  - [ ] `FASTLANE_KEY_ID`
  - [ ] `FASTLANE_ISSUER_ID`
- [ ] Code signing certificates configured
- [ ] Provisioning profiles created

**Setup:**
```bash
cd apps/mobile-ios
bundle exec fastlane match init
bundle exec fastlane setup_signing
```

---

### Android (Play Console)
- [ ] Google Play Developer Account active ($25 one-time)
- [ ] Play Console API access enabled
- [ ] Service account created
- [ ] JSON key file downloaded
- [ ] Release keystore generated
- [ ] Environment variables set:
  - [ ] `GOOGLE_PLAY_JSON_KEY_PATH`
  - [ ] `ANDROID_KEYSTORE_PATH`
  - [ ] `ANDROID_KEYSTORE_PASSWORD`
  - [ ] `ANDROID_KEY_ALIAS`
  - [ ] `ANDROID_KEY_PASSWORD`

**Setup:**
```bash
cd apps/mobile-android
keytool -genkey -v -keystore narna-release.keystore -alias narna -keyalg RSA -keysize 2048 -validity 10000
```

---

## Beta Testing

### iOS TestFlight
- [ ] Beta build uploaded
- [ ] Build processing complete (~10 min)
- [ ] Internal testers added (10-20 people)
- [ ] TestFlight link shared: `https://testflight.apple.com/join/[CODE]`
- [ ] Feedback collected (1 week minimum)
- [ ] Critical bugs fixed

**Upload:**
```bash
cd apps/mobile-ios
bundle exec fastlane ios beta
# Or: ./apps/scripts/submit_to_testflight.sh
```

---

### Android Internal Testing
- [ ] Internal testing build uploaded
- [ ] Release created in Play Console
- [ ] Internal testers added (10-20 people)
- [ ] Testing link shared: `https://play.google.com/apps/internaltest/[TOKEN]`
- [ ] Feedback collected (1 week minimum)
- [ ] Critical bugs fixed

**Upload:**
```bash
cd apps/mobile-android
bundle exec fastlane android beta
# Or: ./apps/scripts/submit_to_play_console.sh
```

---

## Legal & Privacy

### Privacy Policy
- [ ] Privacy policy written
- [ ] Published at: `https://narna.org/privacy`
- [ ] Covers data collection (minimal):
  - [ ] Device name (user-provided)
  - [ ] Mobile token (authentication)
  - [ ] Chat messages (not stored)
  - [ ] API keys (local only, never sent to backend)
- [ ] GDPR compliant
- [ ] COPPA compliant (13+)

---

### Terms of Service
- [ ] Terms of service written
- [ ] Published at: `https://narna.org/terms`
- [ ] Covers:
  - [ ] Usage rights
  - [ ] User responsibilities
  - [ ] Limitation of liability
  - [ ] Open source license (MIT)

---

### Support Page
- [ ] Support page created
- [ ] Published at: `https://narna.org/support`
- [ ] Includes:
  - [ ] Contact email: `support@narna.org`
  - [ ] FAQ section
  - [ ] GitHub issues link
  - [ ] Documentation links

---

## App Store Guidelines Compliance

### iOS App Store
- [ ] No private API usage
- [ ] No app crashes
- [ ] No hardcoded API keys
- [ ] Privacy policy linked
- [ ] Support URL provided
- [ ] Age rating: 4+ (no mature content)
- [ ] No duplicate apps
- [ ] Proper app metadata
- [ ] Screenshots show actual app
- [ ] App follows Human Interface Guidelines

**Review Time:** 1-2 weeks typical

---

### Google Play Store
- [ ] No malware
- [ ] No copyrighted content
- [ ] Privacy policy linked
- [ ] Correct app category (Productivity)
- [ ] Content rating: Everyone
- [ ] No misleading descriptions
- [ ] Proper permissions declared
- [ ] Screenshots show actual app
- [ ] Follows Material Design guidelines

**Review Time:** 1-3 days typical

---

## Final Pre-Submission Checks

### iOS
- [ ] App builds successfully in Release mode
- [ ] No compiler warnings
- [ ] All tests passing
- [ ] Version number updated (e.g., 1.0.0)
- [ ] Build number incremented
- [ ] App icon set
- [ ] Launch screen configured
- [ ] Bundle identifier: `org.narna.mobile`
- [ ] Deployment target: iOS 17.0
- [ ] Archive validates in Xcode Organizer

---

### Android
- [ ] App builds successfully in Release mode
- [ ] ProGuard enabled (code obfuscation)
- [ ] No warnings in Lint
- [ ] All tests passing
- [ ] Version name updated (e.g., 1.0.0)
- [ ] Version code incremented
- [ ] App icon set (all densities)
- [ ] Splash screen configured
- [ ] Application ID: `org.narna.mobile`
- [ ] Min SDK: API 34
- [ ] AAB validates in Play Console

---

## Submission

### iOS App Store
```bash
cd apps/mobile-ios
bundle exec fastlane ios release
```

**Post-Submission:**
- [ ] "Waiting for Review" status in App Store Connect
- [ ] Email confirmation received
- [ ] Monitor review progress
- [ ] Respond to App Review feedback (if any)
- [ ] App approved → Live on App Store
- [ ] Share App Store link: `https://apps.apple.com/app/narna-mobile/id[APP_ID]`

---

### Google Play Store
```bash
cd apps/mobile-android
bundle exec fastlane android release
```

**Post-Submission:**
- [ ] "Under Review" status in Play Console
- [ ] Email confirmation received
- [ ] Monitor review progress
- [ ] Respond to policy issues (if any)
- [ ] App approved → Live on Play Store
- [ ] Share Play Store link: `https://play.google.com/store/apps/details?id=org.narna.mobile`

---

## Post-Launch

### Monitoring
- [ ] Set up crash reporting (Crashlytics / Sentry)
- [ ] Monitor App Store Connect analytics
- [ ] Monitor Play Console analytics
- [ ] Track user reviews
- [ ] Respond to user feedback
- [ ] Fix critical bugs in patch release

---

### Marketing
- [ ] Announce launch on social media
- [ ] Update NARNA website with download links
- [ ] Create demo video
- [ ] Write launch blog post
- [ ] Submit to app review sites
- [ ] Share in developer communities

---

### Future Updates
- [ ] Plan v1.1 features
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Automate screenshot generation
- [ ] Automate beta builds
- [ ] Monitor user retention
- [ ] Iterate based on feedback

---

## Summary

**Ready for Submission When:**
1. ✅ All development complete
2. ✅ E2E testing passed on devices
3. ✅ Screenshots generated (14+ images)
4. ✅ Beta testing complete (1+ week)
5. ✅ Metadata finalized
6. ✅ Legal pages published
7. ✅ Signing credentials configured
8. ✅ Store guidelines compliance verified

**Estimated Time to Launch:**
- **Beta Testing:** 1-2 weeks
- **iOS Review:** 1-2 weeks
- **Android Review:** 1-3 days
- **Total:** 2-4 weeks from beta to live

---

## Current Status

**Completed:**
- ✅ iOS app development
- ✅ Android app development
- ✅ Backend API integration
- ✅ Testing documentation created
- ✅ Screenshot guide created
- ✅ Submission guide created
- ✅ Automation scripts created
- ✅ Store metadata prepared

**Pending (Requires macOS/Android SDK):**
- ⚠️ E2E testing on real devices
- ⚠️ Screenshot generation (14+ images)
- ⚠️ TestFlight beta upload
- ⚠️ Play Console beta upload
- ⚠️ Final store submission

**Blockers:**
- Environment constraint: Linux VM lacks Xcode and Android SDK
- **Next Step:** Transfer to macOS or Android development machine for testing and screenshot generation

---

**Last Updated:** November 10, 2026  
**Version:** 1.0.0  
**Status:** Ready for device testing and screenshot generation
