# Google Play Store - Quick Start Guide

**For full details, see:** [GOOGLE_PLAY_CHECKLIST.md](GOOGLE_PLAY_CHECKLIST.md)

## 🎯 Quick Build & Upload (3 Steps)

### Step 1: Install Android SDK
```bash
# macOS
brew install --cask android-commandlinetools

# Linux
wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
unzip commandlinetools-linux-*_latest.zip -d ~/android-sdk/cmdline-tools

export ANDROID_HOME=~/android-sdk
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

### Step 2: Build AAB
```bash
cd apps/mobile-android
./build-release.sh
```

**Output:** `app/build/outputs/bundle/release/app-release.aab`

### Step 3: Upload to Play Console

**Option A - Automated (with service account):**
```bash
export GOOGLE_PLAY_JSON_KEY_PATH="/path/to/service-account.json"
bundle exec fastlane android release
```

**Option B - Manual:**
1. Go to https://play.google.com/console
2. Navigate to: Release → Production → Create new release
3. Upload `app-release.aab`
4. Fill release notes
5. Click "Start rollout to Production"

---

## 📋 Before First Upload

**Required:**
- [ ] Screenshots (at least 2) - PNG format
- [ ] App icon (512x512) - PNG format
- [ ] Feature graphic (1024x500) - PNG format
- [ ] Privacy policy URL - Must be live and accessible

**Store listing is ready:**
- ✅ Title: "NARNA Mobile - AI Agent Bot"
- ✅ Short description: "Remote control for AI agents"
- ✅ Full description: Complete (see `fastlane/metadata/android/en-US/`)

**Technical setup complete:**
- ✅ Keystore: `narna-release.keystore` (DO NOT COMMIT!)
- ✅ Signing config: Configured in `app/build.gradle.kts`
- ✅ Fastlane: Configured for automated uploads

---

## 🔒 Keystore Information

**File:** `narna-release.keystore`  
**Alias:** `narna`  
**Passwords:** `narnarelease2024` (both store and key)

**⚠️ CRITICAL:** 
- Backup this keystore securely!
- If lost, you CANNOT update the app
- Store passwords in password manager
- DO NOT commit keystore to git (already in .gitignore)

---

## ⏱️ Review Timeline

- **First submission:** 2-7 days (typically 2-3 days)
- **Updates:** 1-3 days
- **You'll receive:** Email notification when approved/rejected

---

## 🆘 Quick Troubleshooting

**"SDK location not found"**
→ Set `export ANDROID_HOME=/path/to/android-sdk`

**"Privacy policy required"**
→ Add privacy policy URL to Play Console store listing

**"Package name already exists"**
→ Verify you're signed into correct Google Play account

**"403 Forbidden" on upload**
→ Service account needs "Release Manager" permission in Play Console

---

## 📱 After Publication

**Your app will be at:**
- https://play.google.com/store/apps/details?id=org.narna.mobile

**Badge for README:**
```markdown
[![Get it on Google Play](https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png)](https://play.google.com/store/apps/details?id=org.narna.mobile)
```

---

## 📞 Need Help?

See [GOOGLE_PLAY_CHECKLIST.md](GOOGLE_PLAY_CHECKLIST.md) for:
- Detailed build instructions
- Complete Play Console setup guide
- Service account configuration
- Privacy policy requirements
- Troubleshooting guide

**Google Play Support:** https://support.google.com/googleplay/android-developer
