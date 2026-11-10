# Android Tablet Screenshots for Google Play

Required tablet screenshots for Google Play submission:

## Tablet Screenshots (10" Tablet - 1920 x 1200 px)

### 7. Tablet Landscape (`07_tablet_landscape.png`)
- **Shows:** Bot list + chat in split view (master-detail layout)
- **Caption:** "Optimized for tablets with split-screen layout"

### 8. Tablet Portrait (`08_tablet_portrait.png`)
- **Shows:** Full chat conversation on tablet
- **Caption:** "Beautiful on phones and tablets"

---

## Generation Instructions

### Automated
```bash
cd apps/mobile-android

# Create 10" tablet AVD (if not exists)
avdmanager create avd \
  -n tablet_10 \
  -k "system-images;android-34;google_apis;x86_64" \
  -d "10.1in WXGA (Tablet)"

# Start emulator
emulator -avd tablet_10 &

# Wait for boot
adb wait-for-device

# Install APKs
adb install app/build/outputs/apk/debug/app-debug.apk
adb install app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk

# Run screenshot tests
bundle exec fastlane screengrab
```

### Manual
1. Start tablet emulator
2. Rotate to landscape: `Ctrl+F11` or hardware rotate
3. Capture landscape screenshot
4. Rotate to portrait
5. Capture portrait screenshot

---

## Status

- [ ] Generated in landscape
- [ ] Generated in portrait
- [ ] Uploaded to Play Console
