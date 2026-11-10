# NARNA iOS Mobile App

Native iOS companion app for NARNA desktop agent, built with SwiftUI following the MausBot/GrokBot model.

## Features

✅ **QR Code Pairing** - Scan QR or enter 6-digit code to pair with desktop agent  
✅ **Bot Management** - View and interact with active NARNA bots  
✅ **Real-time Chat** - WebSocket-powered conversation with bots  
✅ **Approval Gates** - Review and approve shell commands, file edits, web actions  
✅ **Dark Mode** - Native dark mode support  
✅ **Pull-to-refresh** - Keep bot list up to date  
✅ **Secure Storage** - Mobile tokens stored in iOS Keychain  

## Requirements

- **Xcode**: 15.0+
- **iOS**: 16.0+
- **Swift**: 5.9+
- **Backend**: NARNA backend running at `http://localhost:8765`

## Project Structure

```
apps/mobile-ios/NARNA/
├── NARNA.xcodeproj/          # Xcode project file
└── NARNA/
    ├── Info.plist             # App configuration
    ├── NARNAApp.swift         # App entry point
    ├── ContentView.swift      # Root view with pairing check
    ├── Assets.xcassets/       # Images and colors
    │
    ├── Models/
    │   └── Models.swift       # Data models (Bot, Message, Approval, etc.)
    │
    ├── Services/
    │   ├── NARNAAPIService.swift    # REST API client
    │   ├── WebSocketService.swift   # WebSocket connection manager
    │   └── KeychainService.swift    # Secure token storage
    │
    ├── ViewModels/
    │   ├── PairingViewModel.swift   # Pairing logic
    │   ├── BotListViewModel.swift   # Bot list management
    │   └── ChatViewModel.swift      # Chat & WebSocket handling
    │
    └── Views/
        ├── PairingView.swift        # QR scanner + code entry
        ├── QRScannerView.swift      # AVFoundation QR scanner
        ├── BotListView.swift        # List of active bots
        ├── ChatView.swift           # Conversation UI
        ├── ApprovalCardView.swift   # Approval bottom sheet
        └── SettingsView.swift       # Settings & configuration
```

## Build Instructions

### 1. Open Project

```bash
cd apps/mobile-ios/NARNA
open NARNA.xcodeproj
```

### 2. Configure Signing

1. Select **NARNA** target in Xcode
2. Go to **Signing & Capabilities**
3. Select your **Team** or use automatic signing
4. Bundle Identifier: `org.narna.mobile`

### 3. Start Backend

The iOS app requires the NARNA backend running:

```bash
cd web/backend
uvicorn app.main:app --reload --port 8765
```

### 4. Build & Run

- **Simulator**: Select iPhone simulator and press `Cmd+R`
- **Physical Device**: 
  1. Connect iPhone via USB
  2. Trust computer on device
  3. Select device in Xcode
  4. Press `Cmd+R`

## Usage

### First Time Setup

1. **Start Desktop Agent**
   ```bash
   # On your desktop/laptop
   python -m narna.desktop_server
   ```

2. **Generate Pairing Code**
   - Desktop agent will display a 6-digit code and QR code

3. **Pair Mobile App**
   - Option A: Tap "Scan QR Code" and scan the QR
   - Option B: Enter the 6-digit code manually

4. **Success!**
   - Mobile token stored securely in Keychain
   - Now you can see your bots and chat with them

### Daily Usage

1. **View Bots**
   - Pull down to refresh bot list
   - Tap any bot to open chat

2. **Chat with Bot**
   - Type messages and send
   - Real-time updates via WebSocket
   - See bot status (idle/working/waiting approval)

3. **Handle Approvals**
   - Pending approvals shown at top of bot list
   - Review action details
   - Tap "Allow" or "Deny"

4. **Settings**
   - Change API base URL (for remote access)
   - View device info
   - Unpair device

## API Integration

### Base URL

Default: `http://localhost:8765`

For remote access:
1. Expose backend with ngrok/cloudflare tunnel
2. Update base URL in Settings

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/mobile/pairing/verify` | POST | Verify pairing code |
| `/v1/mobile/bots` | GET | List active bots |
| `/v1/mobile/bots/{id}/thread` | GET | Get conversation history |
| `/v1/mobile/bots/{id}/message` | POST | Send message to bot |
| `/v1/mobile/bots/{id}/stream` | WS | Real-time bot updates |
| `/v1/mobile/approvals` | GET | List pending approvals |
| `/v1/mobile/approvals/{id}/allow` | POST | Allow action |
| `/v1/mobile/approvals/{id}/deny` | POST | Deny action |

## Security

- **Mobile Token**: Stored in iOS Keychain (not UserDefaults)
- **Keychain Service**: `org.narna.mobile`
- **Token Format**: `narna_mobile_<random_32_bytes>`
- **Token Expiry**: 30 days (renewable)
- **Camera Permission**: Required for QR scanning (NSCameraUsageDescription in Info.plist)

## Troubleshooting

### "No Active Bots" Error

- Ensure desktop agent is running
- Check backend is accessible at base URL
- Verify mobile token hasn't expired (re-pair if needed)

### QR Scanner Not Working

- Grant camera permission in iOS Settings
- Check "Camera" permission prompt
- Try manual code entry as fallback

### WebSocket Connection Failed

- Verify backend WebSocket endpoint is accessible
- Check firewall/network settings
- WebSocket URL should be `ws://` (not `wss://` for localhost)

### "Invalid mobile token" Error

- Token expired (30 days)
- Backend was restarted (in-memory tokens cleared)
- Solution: Unpair and re-pair device

## Development Tips

### Preview in Xcode

Most views have `#Preview` blocks for live previews:

```swift
#Preview {
    BotListView()
}
```

### Debug Logging

Services print debug logs with emoji prefixes:
- ✅ Success
- ❌ Error
- 📨 WebSocket event
- 🔌 Connection status

### Modify API Base URL

For development, change base URL in `SettingsView` or:

```swift
// In NARNAAPIService.swift
@Published var baseURL: String = "http://192.168.1.100:8765"
```

## Architecture

### MVVM Pattern

- **Models**: Pure data structures (Codable)
- **Views**: SwiftUI views (UI only)
- **ViewModels**: Business logic + state management
- **Services**: API calls, WebSocket, Keychain

### State Management

- `@StateObject`: ViewModel lifecycle
- `@ObservedObject`: ViewModel passed from parent
- `@EnvironmentObject`: App-wide services (APIService)
- `@AppStorage`: Simple persisted settings
- `Keychain`: Sensitive data (tokens)

### Async/Await

All API calls use Swift concurrency:

```swift
Task {
    let bots = try await apiService.listBots()
    // Update UI
}
```

## Future Enhancements

- [ ] Push notifications (APNs)
- [ ] Voice call support (OpenAI Realtime API)
- [ ] E2E encryption for sensitive data
- [ ] iPad-optimized layout
- [ ] Rich message formatting (markdown, code blocks)
- [ ] File upload/download
- [ ] Biometric authentication

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on iOS Simulator + physical device
5. Submit a pull request

## License

MIT License - see [LICENSE](../../LICENSE) file

## Support

- **Documentation**: [docs/MOBILE-API.md](../../docs/MOBILE-API.md)
- **Issues**: https://github.com/narna/narna/issues
- **Discord**: https://discord.gg/narna

---

Built with ❤️ by the NARNA Team
