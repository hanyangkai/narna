# NARNA Mobile - Store Submission Guide

## Prerequisites

### Required Accounts
- ✅ Apple Developer Account ($99/year) - Already have
- ✅ Google Play Developer Account ($25 one-time) - Already have

### Required Tools
```bash
# Install fastlane
sudo gem install fastlane

# Install bundler
sudo gem install bundler

# Verify installations
fastlane --version
bundle --version
```

---

## Step 1: Configure Credentials

### iOS (App Store Connect)

1. **Get App Store Connect API Key**:
   - Go to: https://appstoreconnect.apple.com/access/api
   - Create new key with "App Manager" role
   - Download `.p8` file
   - Note: Key ID, Issuer ID

2. **Set environment variables**:
```bash
export APPLE_ID="your-apple-id@email.com"
export APPLE_TEAM_ID="YOUR_TEAM_ID"
export FASTLANE_API_KEY_PATH="/path/to/AuthKey_XXXXX.p8"
export FASTLANE_KEY_ID="YOUR_KEY_ID"
export FASTLANE_ISSUER_ID="YOUR_ISSUER_ID"
```

3. **Setup code signing** (one-time):
```bash
cd apps/mobile-ios
bundle install
bundle exec fastlane match init
bundle exec fastlane setup_signing
```

### Android (Google Play Console)

1. **Create service account**:
   - Go to: https://play.google.com/console
   - Setup → API access → Create service account
   - Download JSON key file

2. **Generate signing keystore** (one-time):
```bash
cd apps/mobile-android
keytool -genkey -v \
  -keystore narna-release.keystore \
  -alias narna \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

3. **Set environment variables**:
```bash
export GOOGLE_PLAY_JSON_KEY_PATH="/path/to/service-account.json"
export ANDROID_KEYSTORE_PATH="/path/to/narna-release.keystore"
export ANDROID_KEYSTORE_PASSWORD="your-keystore-password"
export ANDROID_KEY_ALIAS="narna"
export ANDROID_KEY_PASSWORD="your-key-password"
```

---

## Step 2: Prepare App Store Listings

### iOS Metadata

Create `apps/mobile-ios/fastlane/metadata/en-US/`:

**name.txt**:
```
NARNA Mobile
```

**subtitle.txt**:
```
AI Agent Remote Control
```

**description.txt**:
```
Control powerful AI agents from your phone.

FEATURES:
• Connect to desktop or cloud agents
• Chat with Claude, ChatGPT, Gemini
• Approve shell commands & file edits
• Real-time WebSocket updates
• QR code pairing
• Secure encryption

BRING YOUR OWN AI:
• Claude Pro / API key
• ChatGPT Plus / API key
• Gemini / API key

FREE & OPEN SOURCE (MIT)
Visit narna.org
```

**keywords.txt**:
```
AI,agent,bot,automation,Claude,ChatGPT,remote,developer
```

**privacy_url.txt**:
```
https://narna.org/privacy
```

**support_url.txt**:
```
https://narna.org/support
```

### Android Metadata

Create `apps/mobile-android/fastlane/metadata/android/en-US/`:

**title.txt**: (same as iOS)
**short_description.txt**:
```
Remote control for AI agents
```

**full_description.txt**: (same as iOS description.txt)

**video.txt**: (optional YouTube link)

---

## Step 3: Generate Screenshots

### iOS Screenshots

```bash
cd apps/mobile-ios

# Install snapshot helper
bundle exec fastlane snapshot init

# Generate screenshots
bundle exec fastlane screenshots

# Screenshots saved to: fastlane/screenshots/
```

Required devices:
- iPhone 15 Pro Max (6.7")
- iPhone 15 (6.1")
- iPad Pro 12.9"

### Android Screenshots

```bash
cd apps/mobile-android

# Setup screengrab
bundle exec fastlane screengrab init

# Generate screenshots
bundle exec fastlane screenshots

# Screenshots saved to: fastlane/metadata/android/en-US/images/
```

Required devices:
- Pixel 8 Pro
- 10" tablet

---

## Step 4: Submit to Stores

### Option A: Submit Both (Automated)

```bash
export SUBMIT_IOS=true
export SUBMIT_ANDROID=true
./scripts/submit_to_stores.sh
```

### Option B: Submit iOS Only

```bash
cd apps/mobile-ios
bundle exec fastlane ios release
```

### Option C: Submit Android Only

```bash
cd apps/mobile-android
bundle exec fastlane android release
```

---

## Step 5: Monitor Review Status

### iOS App Store
- Check: https://appstoreconnect.apple.com
- Review time: 1-2 weeks
- Status updates via email

### Google Play
- Check: https://play.google.com/console
- Review time: 1-3 days
- Usually faster than iOS

---

## Common Issues & Solutions

### iOS: Provisioning Profile Errors
```bash
# Reset and regenerate
bundle exec fastlane match nuke distribution
bundle exec fastlane setup_signing
```

### iOS: Binary Upload Failed
```bash
# Use Application Loader as fallback
open -a "Transporter" apps/mobile-ios/build/NARNA.ipa
```

### Android: Signing Errors
```bash
# Verify keystore
keytool -list -v -keystore narna-release.keystore
```

### Android: AAB Upload Failed
```bash
# Manual upload via Play Console web UI
# Upload: app/build/outputs/bundle/release/app-release.aab
```

---

## Beta Testing (Optional)

### iOS TestFlight
```bash
cd apps/mobile-ios
bundle exec fastlane ios beta
```
Share link: https://testflight.apple.com/join/[CODE]

### Android Internal Testing
```bash
cd apps/mobile-android
bundle exec fastlane android beta
```
Share link: https://play.google.com/apps/internaltest/[TOKEN]

---

## Update Pipeline

After initial submission, updates are faster:

```bash
# 1. Make changes to app code
# 2. Increment version numbers
# 3. Run submission script
./scripts/submit_to_stores.sh
```

**iOS updates**: ~1-2 days review  
**Android updates**: ~1-2 hours review

---

## App Store Links (After Approval)

### iOS
```
https://apps.apple.com/app/narna-mobile/id[ASSIGNED_BY_APPLE]
```

### Android
```
https://play.google.com/store/apps/details?id=org.narna.mobile
```

---

## Security Checklist

- [ ] Code signed with production certificates
- [ ] API keys not hardcoded (use Keychain/Keystore)
- [ ] HTTPS only for API calls
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] No test/debug code in release build
- [ ] ProGuard enabled (Android)
- [ ] Bitcode enabled (iOS, if required)

---

## Support & Troubleshooting

- Fastlane docs: https://docs.fastlane.tools
- App Store Connect: https://developer.apple.com/support
- Google Play Console: https://support.google.com/googleplay/android-developer
- NARNA GitHub: https://github.com/hanyangkai/narna/issues

---

## Next Steps After Approval

1. ✅ Apps go live on stores
2. 📱 Share download links with users
3. 📊 Monitor analytics (App Store Connect / Play Console)
4. 🐛 Fix bugs based on crash reports
5. 🚀 Plan next feature update
6. 🎉 Celebrate! 🥳
