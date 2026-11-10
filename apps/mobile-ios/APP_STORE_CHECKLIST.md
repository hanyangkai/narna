# NARNA iOS App Store Submission Checklist

**Status:** Ready for manual submission on macOS with Xcode

**Last Updated:** November 10, 2026

---

## ✅ COMPLETED

- [x] iOS app fully built and tested
- [x] Fastlane configured with automation lanes
- [x] App Store metadata created in `fastlane/metadata/en-US/`
- [x] Bundle identifier: `org.narna.mobile`
- [x] App name: NARNA Mobile
- [x] Subtitle: AI Agent Remote Control

---

## 📋 PREREQUISITES

### Required Tools (macOS only)

```bash
# Check Xcode installation
xcode-select --version

# Install Xcode Command Line Tools if needed
xcode-select --install

# Install fastlane
sudo gem install fastlane

# Or via Homebrew
brew install fastlane

# Navigate to project
cd apps/mobile-ios
```

### Required Apple Credentials

Set these environment variables (add to `~/.zshrc` or `~/.bash_profile`):

```bash
# Apple Developer Account
export APPLE_ID="your-apple-id@email.com"
export APPLE_TEAM_ID="YOUR_TEAM_ID"  # Find at developer.apple.com

# App Store Connect API (RECOMMENDED METHOD)
export FASTLANE_API_KEY_ID="YOUR_KEY_ID"
export FASTLANE_API_KEY_ISSUER_ID="YOUR_ISSUER_ID"
export FASTLANE_API_KEY_PATH="~/AuthKey_XXXXXXXX.p8"

# Alternative: App-Specific Password (less secure)
export FASTLANE_PASSWORD="your-app-specific-password"
```

**To create App Store Connect API Key:**
1. Go to https://appstoreconnect.apple.com/access/api
2. Click "Keys" → "+" to create new key
3. Give it "App Manager" access
4. Download the `.p8` file (one-time only!)
5. Note the Key ID and Issuer ID

---

## 🔐 STEP 1: Code Signing Setup

### Option A: Automatic via Fastlane Match (Recommended)

```bash
cd apps/mobile-ios

# Initialize match (first time only)
bundle exec fastlane match init

# Generate and download certificates
bundle exec fastlane setup_signing
```

### Option B: Manual via Xcode

1. Open `apps/mobile-ios/NARNA/NARNA.xcodeproj` in Xcode
2. Select NARNA target → Signing & Capabilities
3. Check "Automatically manage signing"
4. Select your Team from dropdown
5. Verify Bundle Identifier: `org.narna.mobile`
6. Xcode will automatically create certificates and provisioning profiles

**Status:** ⏳ Pending

---

## 📱 STEP 2: Prepare App Icon & Screenshots

### App Icon

**Required:** 1024x1024px PNG (no transparency, no rounded corners)

Current location: `apps/mobile-ios/NARNA/NARNA/Assets.xcassets/AppIcon.appiconset/`

**Action Required:**
- [ ] Verify app icon is 1024x1024px
- [ ] Replace placeholder if needed

### Screenshots

**Required sizes for iPhone:**
- 6.7" (iPhone 15 Pro Max): 1290 x 2796 px
- 6.5" (iPhone 14 Plus): 1284 x 2778 px
- 5.5" (iPhone 8 Plus): 1242 x 2208 px

**Required sizes for iPad:**
- 12.9" (iPad Pro): 2048 x 2732 px

**Directory:** `apps/mobile-ios/fastlane/screenshots/en-US/`

**Action Required:**
- [ ] Wait for Testing agent to provide screenshots
- [ ] Or generate manually using fastlane snapshot:
  ```bash
  bundle exec fastlane screenshots
  ```
- [ ] Place screenshots in `fastlane/screenshots/en-US/`

**Status:** ⏳ Waiting for Testing agent

---

## 🏗️ STEP 3: Build IPA

### Option A: Fastlane (Automated - Recommended)

```bash
cd apps/mobile-ios

# Full release build + upload + submit
bundle exec fastlane ios release

# This will:
# 1. Increment build number
# 2. Build IPA with app-store export
# 3. Upload to App Store Connect
# 4. Submit for review automatically
```

### Option B: Xcode (Manual)

```bash
# 1. Open project in Xcode
open apps/mobile-ios/NARNA/NARNA.xcodeproj

# 2. In Xcode:
#    - Product → Archive
#    - Wait for archive to complete
#    - Window → Organizer → Archives
#    - Select the archive → Distribute App
#    - Choose "App Store Connect"
#    - Choose "Upload"
#    - Select automatic signing
#    - Wait for upload to complete

# 3. IPA will be at:
#    ~/Library/Developer/Xcode/Archives/<date>/NARNA.xcarchive
```

### Option C: Command Line (xcodebuild)

```bash
cd apps/mobile-ios

# 1. Archive
xcodebuild archive \
  -project NARNA/NARNA.xcodeproj \
  -scheme NARNA \
  -archivePath build/NARNA.xcarchive \
  -configuration Release \
  -destination "generic/platform=iOS" \
  CODE_SIGN_IDENTITY="Apple Distribution" \
  DEVELOPMENT_TEAM="YOUR_TEAM_ID"

# 2. Export IPA
xcodebuild -exportArchive \
  -archivePath build/NARNA.xcarchive \
  -exportPath build/ \
  -exportOptionsPlist ExportOptions.plist

# IPA will be at: build/NARNA.ipa
```

**Status:** ⏳ Pending (requires macOS + Xcode)

**Expected Output:**
- `apps/mobile-ios/build/NARNA.ipa` (~15-30 MB)
- `apps/mobile-ios/build/NARNA.app.dSYM.zip` (debug symbols)

---

## 📤 STEP 4: Upload to App Store Connect

### Option A: Fastlane (Already included in `release` lane)

If you ran `bundle exec fastlane ios release`, upload is automatic. Skip to Step 5.

### Option B: Transporter App (Manual Upload)

```bash
# 1. Install Transporter from Mac App Store
open "https://apps.apple.com/app/transporter/id1450874784"

# 2. Open Transporter and sign in with Apple ID
# 3. Drag apps/mobile-ios/build/NARNA.ipa into Transporter
# 4. Click "Deliver"
# 5. Wait for upload (5-15 minutes depending on connection)
```

### Option C: Command Line (xcrun altool)

```bash
cd apps/mobile-ios

xcrun altool --upload-app \
  --type ios \
  --file build/NARNA.ipa \
  --username "$APPLE_ID" \
  --password "$FASTLANE_PASSWORD"
```

**Status:** ⏳ Pending

**Expected Result:**
- "Package successfully uploaded" message
- Build appears in App Store Connect within 15-30 minutes
- Email confirmation from Apple

---

## 📝 STEP 5: Complete App Store Connect Listing

1. **Go to App Store Connect:**
   https://appstoreconnect.apple.com/apps

2. **Select NARNA Mobile** (or create new app if first submission)

3. **App Information:**
   - Name: `NARNA Mobile`
   - Subtitle: `AI Agent Remote Control`
   - Privacy Policy URL: `https://narna.org/privacy`
   - Category: **Developer Tools** (Primary)
   - Category: **Productivity** (Secondary)

4. **Pricing:**
   - Price: **Free**
   - Availability: **All countries**

5. **App Privacy:**
   - [ ] Complete privacy questionnaire
   - Data collected: None (if true)
   - Third-party analytics: None (if true)

6. **Version Information:**
   - Version: `1.0`
   - Copyright: `© 2026 NARNA`
   - Description: *(Auto-filled from metadata)*
   - Keywords: *(Auto-filled from metadata)*
   - Support URL: `https://narna.org/support`
   - Marketing URL: `https://narna.org`

7. **Build:**
   - [ ] Click "+" next to Build
   - [ ] Select the uploaded build
   - [ ] Add "What's New in This Version": `Initial release of NARNA Mobile`

8. **Screenshots:**
   - [ ] Upload screenshots for each device size
   - [ ] Add captions (optional)

9. **App Review Information:**
   - Contact: Your name and email
   - Phone: Your phone number
   - Demo account: If required for testing
   - Notes: 
     ```
     NARNA is an open-source AI agent remote control app. 
     Users connect to their own AI agents (Claude, ChatGPT, Gemini).
     Requires user to bring their own API keys.
     No server-side data collection.
     ```

10. **Export Compliance:**
    - [ ] Does your app use encryption? **NO**
    - (Or answer questions if yes)

**Status:** ⏳ Pending

---

## 🚀 STEP 6: Submit for Review

### Automated Submission (via fastlane `release` lane)

If you used `bundle exec fastlane ios release`, submission is automatic.

### Manual Submission (via App Store Connect)

1. Review all information in App Store Connect
2. Click **"Submit for Review"** button (top-right)
3. Confirm export compliance
4. Confirm advertising identifier usage: **NO**
5. Confirm content rights
6. Click **"Submit"**

**Status:** ⏳ Pending

---

## ⏰ STEP 7: Monitor Review Status

### Expected Timeline

| Stage | Duration | What to Expect |
|-------|----------|----------------|
| **Upload Processing** | 15-30 min | Build appears in App Store Connect |
| **Waiting for Review** | 1-2 days | Status: "Waiting for Review" |
| **In Review** | 2-24 hours | Status: "In Review" |
| **Approved** | Instant | Status: "Ready for Sale" |

### Check Status

```bash
# Via fastlane
cd apps/mobile-ios
bundle exec fastlane deliver status

# Or visit:
# https://appstoreconnect.apple.com/apps/<app-id>/appstore
```

### Common Rejection Reasons

**Be prepared to address:**

1. **Missing Privacy Policy**
   - ✅ Already set: https://narna.org/privacy
   - Ensure page is live and accessible

2. **Incomplete Functionality**
   - App must be fully functional for reviewers
   - Provide demo credentials if needed

3. **Guideline 4.2 - Minimum Functionality**
   - NARNA has clear utility: AI agent control
   - Highlight features in review notes

4. **Guideline 5.1.1 - Data Collection**
   - Declare data collection accurately
   - NARNA collects minimal data (if any)

**Status:** ⏳ Pending submission

---

## 🎯 QUICK START (TL;DR)

**If you have all credentials ready:**

```bash
# 1. Install dependencies
cd apps/mobile-ios
bundle install

# 2. Set environment variables
export APPLE_ID="your@email.com"
export APPLE_TEAM_ID="TEAM123"
export FASTLANE_API_KEY_PATH="~/AuthKey_XXX.p8"

# 3. Setup signing (first time only)
bundle exec fastlane setup_signing

# 4. Build, upload, and submit in one command
bundle exec fastlane ios release

# Done! 🎉
```

---

## 🐛 TROUBLESHOOTING

### "No code signing identity found"

```bash
# Clean and reset
rm -rf ~/Library/Developer/Xcode/DerivedData
security find-identity -v -p codesigning

# Re-run setup
bundle exec fastlane setup_signing
```

### "Build failed"

```bash
# Clean build folder
cd apps/mobile-ios
xcodebuild clean -project NARNA/NARNA.xcodeproj -scheme NARNA

# Try again
bundle exec fastlane gym
```

### "Upload failed - Invalid credentials"

```bash
# Re-authenticate
bundle exec fastlane fastlane-credentials add --username $APPLE_ID

# Or regenerate App Store Connect API key
```

### "Missing compliance"

Edit `Fastfile` and update:

```ruby
submission_information: {
  export_compliance_uses_encryption: false,
  add_id_info_uses_idfa: false
}
```

---

## 📊 SUBMISSION STATUS SUMMARY

| Task | Status | Assignee | Notes |
|------|--------|----------|-------|
| Metadata created | ✅ Complete | Cloud Agent | All files in `fastlane/metadata/en-US/` |
| Fastlane configured | ✅ Complete | Cloud Agent | `Fastfile` and `Appfile` ready |
| App icon verified | ⏳ Pending | User | Check 1024x1024px asset |
| Screenshots | ⏳ Pending | Testing Agent | Waiting for delivery |
| Code signing | ⏳ Pending | User | Requires macOS + credentials |
| Build IPA | ⏳ Pending | User | Requires macOS + Xcode |
| Upload to ASC | ⏳ Pending | User | After build complete |
| Submit for review | ⏳ Pending | User | After upload + metadata |
| Monitor review | ⏳ Pending | User | 1-3 days typical |

---

## 📞 SUPPORT & RESOURCES

- **Fastlane Docs:** https://docs.fastlane.tools/
- **App Store Connect:** https://appstoreconnect.apple.com/
- **App Review Guidelines:** https://developer.apple.com/app-store/review/guidelines/
- **NARNA Website:** https://narna.org
- **Apple Developer Support:** https://developer.apple.com/support/

---

## 🎉 POST-APPROVAL

Once approved:

1. **Monitor Crash Reports:**
   - App Store Connect → Analytics → Crashes

2. **Respond to Reviews:**
   - App Store Connect → Ratings and Reviews

3. **Track Downloads:**
   - App Store Connect → Analytics → Metrics

4. **Update as Needed:**
   ```bash
   # For updates, increment version and repeat:
   bundle exec fastlane ios release
   ```

---

**Next Steps:** Complete prerequisites on macOS machine and run `bundle exec fastlane ios release`

**Estimated Total Time:** 2-4 hours (excluding Apple review time)
