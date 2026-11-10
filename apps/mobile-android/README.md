# NARNA Android Mobile App

Android companion app for NARNA AI agent platform, enabling mobile control and monitoring of desktop agents.

## Features

- **Device Pairing**: QR code scanning and manual code entry
- **Bot Management**: View and interact with all your NARNA bots
- **Real-time Chat**: WebSocket-powered instant messaging
- **Approval Gates**: Mobile approval for sensitive bot actions
- **Secure Storage**: Android Keystore for token/key storage
- **Material Design 3**: Modern, beautiful UI with dark theme support
- **Background Connection**: Foreground service for persistent WebSocket
- **Push Notifications**: Alerts for messages and approval requests

## Requirements

- **Android Studio**: Hedgehog (2023.1.1) or later
- **JDK**: 17 or later
- **Android SDK**:
  - Min SDK: 26 (Android 8.0)
  - Target SDK: 34 (Android 14)
- **Gradle**: 8.2+
- **Kotlin**: 1.9.20

## Tech Stack

- **UI**: Jetpack Compose + Material Design 3
- **Architecture**: MVVM with ViewModel
- **Dependency Injection**: Hilt (Dagger)
- **Networking**: Ktor Client
- **WebSocket**: Ktor WebSockets + OkHttp fallback
- **Camera**: CameraX + ML Kit (QR scanning)
- **Serialization**: Kotlinx Serialization
- **Storage**: EncryptedSharedPreferences + DataStore
- **Background**: WorkManager + Foreground Service

## Project Structure

```
app/src/main/java/org/narna/mobile/
├── data/
│   ├── api/
│   │   └── NARNAApiService.kt          # REST API client
│   ├── model/                           # Data models (Pairing, Bot, Approval, WebSocket)
│   ├── preferences/
│   │   └── UserPreferences.kt          # DataStore preferences
│   ├── storage/
│   │   └── SecureStorage.kt            # Android Keystore wrapper
│   └── websocket/
│       └── WebSocketManager.kt         # WebSocket connection manager
├── di/
│   └── AppModule.kt                    # Hilt DI module
├── navigation/
│   └── NavGraph.kt                     # Navigation setup
├── service/
│   └── WebSocketService.kt             # Background WebSocket service
├── ui/
│   ├── approvals/
│   │   └── ApprovalBottomSheet.kt      # Approval request UI
│   ├── bots/
│   │   ├── BotListScreen.kt            # Bot list
│   │   └── BotListViewModel.kt
│   ├── chat/
│   │   ├── ChatScreen.kt               # Chat UI
│   │   └── ChatViewModel.kt
│   ├── pairing/
│   │   ├── PairingScreen.kt            # QR scanner + code entry
│   │   └── PairingViewModel.kt
│   ├── settings/
│   │   ├── SettingsScreen.kt           # Settings UI
│   │   └── SettingsViewModel.kt
│   └── theme/                          # Material 3 theme
├── MainActivity.kt
└── NARNAApplication.kt
```

## Build Instructions

### 1. Clone Repository

```bash
git clone <repo-url>
cd apps/mobile-android
```

### 2. Open in Android Studio

1. Launch Android Studio
2. File → Open → Select `apps/mobile-android/`
3. Wait for Gradle sync to complete

### 3. Configure API Endpoint

**For Emulator** (default):
- Uses `http://10.0.2.2:8765` (localhost on host machine)
- No configuration needed

**For Physical Device**:

Edit `app/build.gradle.kts`:

```kotlin
defaultConfig {
    // Replace with your desktop's local IP
    buildConfigField("String", "BASE_URL", "\"http://192.168.1.100:8765\"")
}
```

Or use ngrok for remote access:

```bash
# On desktop
ngrok http 8765

# Update build.gradle.kts
buildConfigField("String", "BASE_URL", "\"https://your-ngrok-url.ngrok.io\"")
```

### 4. Build & Run

#### Debug Build (Development)

```bash
# Command line
./gradlew assembleDebug
./gradlew installDebug

# Or in Android Studio
Run → Run 'app' (Shift+F10)
```

#### Release Build (Production)

1. **Create Keystore** (first time only):

```bash
keytool -genkey -v -keystore narna-release.keystore \
  -alias narna -keyalg RSA -keysize 2048 -validity 10000
```

2. **Configure Signing**:

Create `keystore.properties` in project root:

```properties
storeFile=/path/to/narna-release.keystore
storePassword=your_store_password
keyAlias=narna
keyPassword=your_key_password
```

Add to `app/build.gradle.kts`:

```kotlin
val keystorePropertiesFile = rootProject.file("keystore.properties")
val keystoreProperties = Properties()
keystoreProperties.load(FileInputStream(keystorePropertiesFile))

android {
    signingConfigs {
        create("release") {
            storeFile = file(keystoreProperties["storeFile"] as String)
            storePassword = keystoreProperties["storePassword"] as String
            keyAlias = keystoreProperties["keyAlias"] as String
            keyPassword = keystoreProperties["keyPassword"] as String
        }
    }
    
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            // ... rest of config
        }
    }
}
```

3. **Build Release APK**:

```bash
./gradlew assembleRelease

# Output: app/build/outputs/apk/release/app-release.apk
```

4. **Build AAB (for Play Store)**:

```bash
./gradlew bundleRelease

# Output: app/build/outputs/bundle/release/app-release.aab
```

## Running on Device

### Emulator

1. Create AVD in Android Studio (Tools → Device Manager)
2. Min API 26, recommended: Pixel 5 with API 34
3. Run → Select Device → Run

### Physical Device

1. Enable **Developer Options** on device:
   - Settings → About Phone → Tap "Build Number" 7 times
2. Enable **USB Debugging**:
   - Settings → Developer Options → USB Debugging
3. Connect via USB and run

## Usage Flow

### 1. Pairing

1. Start NARNA desktop agent
2. In desktop, generate pairing QR/code
3. Open mobile app
4. **Scan QR code** or **enter 6-digit code**
5. App securely stores mobile token

### 2. Bot Interaction

1. View list of active bots
2. Tap bot to open chat
3. Send messages via text input
4. Receive real-time responses

### 3. Approvals

1. Bot requests approval (e.g., shell command)
2. Push notification appears
3. Tap notification → Approval bottom sheet opens
4. Review details → **Allow** or **Deny**

### 4. Settings

- Configure AI API keys (OpenAI, Anthropic)
- Toggle dark theme
- Enable/disable notifications
- Unpair device

## Testing

### Unit Tests

```bash
./gradlew test
```

### Instrumented Tests

```bash
./gradlew connectedAndroidTest
```

### Manual Testing Checklist

- [ ] Pairing: QR scan works
- [ ] Pairing: Manual code entry works
- [ ] Bot list: Shows connected bots
- [ ] Chat: Messages send/receive
- [ ] Chat: WebSocket reconnects on disconnect
- [ ] Approvals: Bottom sheet displays correctly
- [ ] Approvals: Allow/Deny works
- [ ] Settings: API keys save securely
- [ ] Settings: Theme toggle works
- [ ] Notifications: Appear for messages
- [ ] Background: Service maintains connection

## Troubleshooting

### Gradle Sync Failed

```bash
./gradlew clean
File → Invalidate Caches → Invalidate and Restart
```

### Camera Permission Denied

- Settings → Apps → NARNA → Permissions → Enable Camera

### WebSocket Won't Connect

- Check API endpoint in `BuildConfig.BASE_URL`
- Verify desktop agent is running
- For physical device, ensure same WiFi network
- Check Android logs: `adb logcat | grep WebSocket`

### Build Errors

```bash
# Clear Gradle cache
./gradlew clean
rm -rf .gradle
./gradlew build --refresh-dependencies
```

## API Integration

### Base URL Configuration

| Environment | URL |
|-------------|-----|
| Emulator (local) | `http://10.0.2.2:8765` |
| Physical device (local) | `http://192.168.x.x:8765` |
| Remote (ngrok) | `https://xxx.ngrok.io` |
| Production | `https://api.narna.org` |

### Endpoints Used

- `POST /v1/mobile/pairing/verify` - Verify pairing code
- `GET /v1/mobile/bots` - List bots
- `GET /v1/mobile/bots/{id}/thread` - Get chat history
- `POST /v1/mobile/bots/{id}/message` - Send message
- `GET /v1/mobile/approvals` - List pending approvals
- `POST /v1/mobile/approvals/{id}/allow` - Allow approval
- `WS /v1/mobile/bots/{id}/stream` - WebSocket for real-time updates

See [MOBILE-API.md](../../docs/MOBILE-API.md) for full API specification.

## Security

- **Mobile Token**: Stored in Android Keystore (EncryptedSharedPreferences)
- **API Keys**: Stored in Android Keystore
- **Network**: HTTPS required for production (HTTP allowed for local dev)
- **Permissions**: Camera (QR scan), Internet, Notifications

## Contributing

1. Follow Material Design 3 guidelines
2. Use Kotlin coroutines for async operations
3. Implement proper error handling
4. Add loading states to all async actions
5. Test on API 26 (min) and API 34 (target)

## Google Play Store Submission

The app is ready for Google Play Store submission. See:

- **[PLAY_STORE_QUICK_START.md](PLAY_STORE_QUICK_START.md)** - Quick build and upload guide
- **[GOOGLE_PLAY_CHECKLIST.md](GOOGLE_PLAY_CHECKLIST.md)** - Complete submission checklist

**Quick Build for Play Store:**

```bash
# Install Android SDK (first time only)
# See PLAY_STORE_QUICK_START.md for instructions

# Build signed AAB
./build-release.sh

# Upload to Play Console
bundle exec fastlane android release
# OR upload manually at play.google.com/console
```

**Store Listing:**
- **Package:** `org.narna.mobile`
- **Title:** NARNA Mobile - AI Agent Bot
- **Category:** Productivity
- **Rating:** Everyone
- **Privacy Policy:** Required before submission

Once published, the app will be available at:  
https://play.google.com/store/apps/details?id=org.narna.mobile

## License

See root repository LICENSE file.

## Support

- **Issues**: GitHub Issues
- **API Docs**: `docs/MOBILE-API.md`
- **Backend**: `web/backend/app/mobile.py`
- **Play Store:** [GOOGLE_PLAY_CHECKLIST.md](GOOGLE_PLAY_CHECKLIST.md)
