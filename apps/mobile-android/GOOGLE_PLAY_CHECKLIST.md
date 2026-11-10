# Google Play Store Submission Checklist

## 📱 NARNA Mobile Android App - Play Store Release

**Package:** `org.narna.mobile`  
**Version:** 0.1.0 (versionCode: 1)  
**Status:** Ready for build and submission

---

## ✅ COMPLETED TASKS

### 1. Google Play Metadata ✓
**Location:** `fastlane/metadata/android/en-US/`

- ✅ **title.txt** - "NARNA Mobile - AI Agent Bot"
- ✅ **short_description.txt** - "Remote control for AI agents"
- ✅ **full_description.txt** - Full feature description with:
  - Core features (WebSocket, QR pairing, approvals)
  - Supported AI models (Claude, ChatGPT, Gemini, etc.)
  - Target audience (developers, automation enthusiasts)
  - Open source notice
- ⏳ **Screenshots** - Will be provided by Testing agent

### 2. Signing Configuration ✓
**Keystore Generated:** `apps/mobile-android/narna-release.keystore`

**Keystore Details:**
```
File: narna-release.keystore
Alias: narna
Algorithm: RSA 2048-bit
Validity: 10,000 days (~27 years)
DN: CN=NARNA Mobile, OU=Mobile Apps, O=NARNA, L=San Francisco, ST=California, C=US
Store Password: narnarelease2024
Key Password: narnarelease2024
```

**⚠️ IMPORTANT - Store These Credentials Securely:**
- Store keystore file in secure location (DO NOT commit to git)
- Save passwords in password manager
- Backup keystore - if lost, cannot update the app!

**Signing Config Added to:** `app/build.gradle.kts`
- Configured to use environment variables OR default keystore
- Release builds will be automatically signed

### 3. Fastlane Configuration ✓
**Files:** `fastlane/Fastfile`, `fastlane/Appfile`

Lanes available:
- `fastlane android release` - Build AAB + upload to production
- `fastlane android beta` - Build AAB + upload to internal testing
- `fastlane android screenshots` - Generate screenshots

---

## 🔧 BUILD REQUIREMENTS

### Prerequisites for Building
To build the Android app bundle (AAB), you need:

1. **Android SDK** (not currently installed in this environment)
   - Android SDK Platform 34 (compileSdk)
   - Android SDK Build Tools 34.0.0+
   - Android SDK Platform-Tools
   
2. **Java Development Kit (JDK)**
   - JDK 17 (already configured in build.gradle.kts)
   
3. **Gradle** (wrapper included)
   - Gradle 8.2 (configured and downloaded)

### Option A: Build Locally (Recommended for First Release)

**Step 1: Install Android SDK**
```bash
# On macOS with Homebrew
brew install --cask android-commandlinetools

# On Linux
wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
unzip commandlinetools-linux-*_latest.zip
mkdir -p ~/android-sdk/cmdline-tools
mv cmdline-tools ~/android-sdk/cmdline-tools/latest

# Set environment variable
export ANDROID_HOME=~/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
```

**Step 2: Install SDK Components**
```bash
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

**Step 3: Build the AAB**
```bash
cd apps/mobile-android

# Set keystore environment variables
export ANDROID_KEYSTORE_PATH="./narna-release.keystore"
export ANDROID_KEYSTORE_PASSWORD="narnarelease2024"
export ANDROID_KEY_ALIAS="narna"
export ANDROID_KEY_PASSWORD="narnarelease2024"

# Clean and build
./gradlew clean bundleRelease

# Output will be at:
# app/build/outputs/bundle/release/app-release.aab
```

**Step 4: Verify the AAB**
```bash
# Check file exists and size is reasonable (should be several MB)
ls -lh app/build/outputs/bundle/release/app-release.aab

# Optionally verify with bundletool
java -jar bundletool.jar validate --bundle=app/build/outputs/bundle/release/app-release.aab
```

### Option B: Use Fastlane (Requires Service Account)

**Prerequisites:**
1. Google Play Console service account JSON key
2. Set `GOOGLE_PLAY_JSON_KEY_PATH` environment variable
3. Android SDK installed (as above)

**Steps:**
```bash
cd apps/mobile-android

# Export all required environment variables
export ANDROID_KEYSTORE_PATH="./narna-release.keystore"
export ANDROID_KEYSTORE_PASSWORD="narnarelease2024"
export ANDROID_KEY_ALIAS="narna"
export ANDROID_KEY_PASSWORD="narnarelease2024"
export GOOGLE_PLAY_JSON_KEY_PATH="/path/to/service-account.json"

# Run fastlane to build and upload
bundle exec fastlane android release
```

This will:
- Clean the project
- Build the signed AAB
- Upload to Google Play Store (production track)
- Upload metadata and screenshots
- Set status to "completed" (ready for review)

---

## 📤 MANUAL UPLOAD TO GOOGLE PLAY CONSOLE

If you prefer to upload manually or automated upload fails:

### Step 1: Access Google Play Console
1. Go to https://play.google.com/console
2. Sign in with your Google Play developer account
3. Click "Create app" or select existing app

### Step 2: App Details
- **App name:** NARNA Mobile - AI Agent Bot
- **Default language:** English (United States)
- **App or game:** App
- **Free or paid:** Free

### Step 3: Store Listing
Navigate to: **Store presence → Main store listing**

**App details:**
- **App name:** NARNA Mobile - AI Agent Bot
- **Short description:** Remote control for AI agents
- **Full description:** (Copy from `fastlane/metadata/android/en-US/full_description.txt`)

**Graphics:**
- **App icon:** Required (512 x 512 PNG)
- **Feature graphic:** Required (1024 x 500 PNG)
- **Phone screenshots:** At least 2 required
- **7-inch tablet screenshots:** Optional
- **10-inch tablet screenshots:** Optional

**Categorization:**
- **App category:** Productivity
- **Tags:** AI, Automation, Developer Tools, Remote Control

**Contact details:**
- **Email:** (Your support email)
- **Phone:** (Optional)
- **Website:** https://narna.org
- **Privacy policy:** (Required - must be publicly accessible URL)

### Step 4: Privacy Policy
You MUST provide a privacy policy URL. Create one covering:
- What data is collected (API keys, preferences)
- How data is used (connecting to AI services)
- Data storage (local encrypted storage)
- Third-party services (Claude, OpenAI, Google, etc.)
- User rights (data deletion, access)

**Suggested hosting:** 
- GitHub Pages: `https://narna.org/privacy-policy`
- Google Sites
- Your own domain

### Step 5: Content Rating
Navigate to: **Store presence → Content rating**

Complete the questionnaire:
- **Category:** Utility, Productivity, Communication & Networking
- **Violence:** No
- **Sexual content:** No
- **Profanity:** No
- **Drugs:** No
- **Gambling:** No
- **Social features:** Yes (chat functionality)

**Expected rating:** Everyone / PEGI 3

### Step 6: App Access
Navigate to: **App content → App access**

- **Special access:** None required
- **Is your app free?** Yes
- **Contains ads?** No
- **In-app purchases?** No

### Step 7: Data Safety
Navigate to: **App content → Data safety**

**Data collected:**
- ✅ **Personal info:** Email (optional, for pairing)
- ✅ **App activity:** Chat messages with AI
- ✅ **Device or other IDs:** Device ID for pairing

**Data shared:**
- With third-party AI services (Claude, OpenAI, Google)
- For app functionality (chat, commands)

**Data security:**
- ✅ Data encrypted in transit
- ✅ Data encrypted at rest (device storage)
- ✅ Users can request data deletion
- ✅ Data is not sold to third parties

### Step 8: Upload AAB
Navigate to: **Release → Production → Create new release**

1. Click "Upload" and select `app-release.aab`
2. Enter **Release name:** "0.1.0 - Initial Release"
3. Enter **Release notes:**
   ```
   Initial release of NARNA Mobile!
   
   Features:
   • Connect to AI agents via QR code
   • Chat with Claude, ChatGPT, Gemini
   • Approve commands and file edits
   • Real-time WebSocket updates
   • Secure end-to-end encryption
   ```
4. Click "Save" then "Review release"

### Step 9: Review and Submit
1. Review all sections for completion
2. Fix any warnings or errors
3. Click "Start rollout to Production"
4. Confirm submission

---

## 🔐 GOOGLE PLAY SERVICE ACCOUNT SETUP

For automated uploads via Fastlane, you need a service account:

### Create Service Account
1. Go to Google Play Console
2. Navigate to: **Setup → API access**
3. Click "Create new service account"
4. Follow link to Google Cloud Console
5. Create service account:
   - Name: `narna-fastlane-upload`
   - Role: `Service Account User`
6. Create JSON key and download it
7. Return to Play Console
8. Click "Grant access" for the service account
9. Set permissions:
   - ✅ Admin (releases)
   - ✅ Manage store presence
   - ✅ Manage production releases
   - ✅ Manage testing tracks

### Save Credentials
```bash
# Save JSON key securely
export GOOGLE_PLAY_JSON_KEY_PATH="/secure/path/to/service-account.json"

# Or add to ~/.bashrc or ~/.zshrc
echo 'export GOOGLE_PLAY_JSON_KEY_PATH="/path/to/service-account.json"' >> ~/.bashrc
```

---

## ⏱️ REVIEW TIMELINE

**Typical Google Play review times:**
- **First submission:** 1-7 days (often 2-3 days)
- **Updates:** 1-3 days
- **Expedited review:** Not available for new apps

**After submission:**
1. App enters "In review" status
2. Automated checks run (malware, policy violations)
3. Manual review by Google team
4. Approval or rejection notification via email

**If rejected:**
- Review rejection reason
- Fix issues
- Resubmit with updated AAB or metadata
- Subsequent reviews are typically faster

---

## 📋 PRE-SUBMISSION CHECKLIST

Before submitting, verify:

- [ ] **Metadata complete** (title, descriptions)
- [ ] **Screenshots uploaded** (at least 2 phone screenshots)
- [ ] **App icon** (512x512 PNG)
- [ ] **Feature graphic** (1024x500 PNG)
- [ ] **Privacy policy** URL live and accessible
- [ ] **Keystore created** and backed up securely
- [ ] **AAB built** and signed correctly
- [ ] **Content rating** questionnaire completed
- [ ] **Data safety** form filled out
- [ ] **Target audience** set (13+)
- [ ] **App tested** on physical device
- [ ] **Deep links work** (narna://pair)
- [ ] **Permissions justified** (camera for QR scanning)
- [ ] **Release notes** written
- [ ] **Support email** configured
- [ ] **Website URL** accessible (narna.org)

---

## 🚀 POST-SUBMISSION TASKS

After the app is live:

1. **Monitor reviews** - Respond to user feedback
2. **Track crashes** - Use Google Play Console crash reports
3. **Analytics** - Monitor installations and retention
4. **Updates** - Plan regular updates with bug fixes
5. **Marketing** - Announce on narna.org, social media
6. **Documentation** - Update README with Play Store link

---

## 📱 APP STORE LISTING URLs

Once published:
- **Google Play Store:** `https://play.google.com/store/apps/details?id=org.narna.mobile`
- **Direct install link:** `market://details?id=org.narna.mobile`

---

## 🐛 TROUBLESHOOTING

### Build Issues
- **"SDK location not found"** → Set ANDROID_HOME environment variable
- **"Keystore not found"** → Check ANDROID_KEYSTORE_PATH points to keystore file
- **"Execution failed for task :app:lintVitalAnalyzeRelease"** → Run `./gradlew clean` first

### Upload Issues
- **"403 Forbidden"** → Service account lacks permissions
- **"Version code must be greater"** → Increment versionCode in build.gradle.kts
- **"Package name mismatch"** → Verify package name in Appfile matches app

### Review Issues
- **"Privacy policy required"** → Add privacy policy URL to store listing
- **"Misleading content"** → Clarify that user brings their own AI API keys
- **"Incomplete listing"** → Ensure all required fields filled

---

## 📞 SUPPORT

- **NARNA Website:** https://narna.org
- **GitHub Issues:** https://github.com/narna/narna/issues
- **Google Play Support:** https://support.google.com/googleplay/android-developer

---

**Last Updated:** November 10, 2026  
**Prepared by:** Cursor Cloud Agent  
**Next Step:** Install Android SDK and build AAB, or upload manually via Play Console
