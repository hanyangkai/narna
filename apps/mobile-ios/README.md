# NARNA iOS Mobile App

Native iOS companion app for NARNA desktop agent, built with SwiftUI following the MausBot/GrokBot model.

## Features

✅ **QR Code Pairing** - Scan QR or enter 6-digit code to pair with desktop agent  
✅ **Tabbed Shell** - Bots, Inbox, Routines, Voice, and Settings after pairing  
✅ **Bot Management** - View and chat with active NARNA bots  
✅ **Cross-bot Inbox** - Approvals + pending messages with inline Allow/Deny  
✅ **Routines** - List, create, and toggle scheduled bot routines  
✅ **Voice Calls** - Start/stop live call UI with transcript placeholder  
✅ **Remote Access** - Local / Tailscale / Custom HTTPS host configuration  
✅ **Connected Apps** - Gmail, Slack, GitHub, Notion, Linear connect stubs  
✅ **Push Registration** - Device token stub for approval notifications  
✅ **Real-time Chat** - WebSocket-powered conversation with bots  
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
    ├── ContentView.swift      # Pairing gate + TabView shell
    ├── Assets.xcassets/       # Images and colors
    │
    ├── Models/
    │   └── Models.swift       # Data models (Bot, Inbox, Routine, Voice, etc.)
    │
    ├── Services/
    │   ├── NARNAAPIService.swift    # REST API client
    │   ├── WebSocketService.swift   # WebSocket connection manager
    │   └── KeychainService.swift    # Secure token storage
    │
    ├── ViewModels/
    │   ├── PairingViewModel.swift
    │   ├── BotListViewModel.swift
    │   ├── ChatViewModel.swift
    │   ├── InboxViewModel.swift
    │   ├── RoutinesViewModel.swift
    │   └── VoiceCallViewModel.swift
    │
    └── Views/
        ├── PairingView.swift
        ├── QRScannerView.swift
        ├── BotListView.swift        # Bots tab
        ├── InboxView.swift          # Inbox tab
        ├── RoutinesView.swift       # Routines tab
        ├── VoiceCallView.swift      # Voice tab
        ├── ChatView.swift
        ├── ApprovalCardView.swift
        └── SettingsView.swift       # Settings tab
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
   - Tab bar appears: **Bots · Inbox · Routines · Voice · Settings**

### Daily Usage

1. **Bots** — Pull to refresh, tap a bot to chat
2. **Inbox** — Cross-bot approvals and pending items; Allow/Deny inline (badge shows pending count)
3. **Routines** — Create cron schedules, toggle enabled/paused
4. **Voice** — Start/stop a live call; transcript placeholder until Realtime audio is wired
5. **Settings** — Remote access, connected apps, push toggle, OpenAI voice key, unpair

## API Integration

### Base URL

Default: `http://localhost:8765`

For remote access, use Settings → Remote Access (Local / Tailscale / Custom HTTPS).

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
| `/v1/mobile/inbox` | GET | Cross-bot inbox |
| `/v1/mobile/routines` | GET/POST | List / create routines |
| `/v1/mobile/routines/{id}/toggle` | POST | Enable/disable routine |
| `/v1/mobile/voice/start` | POST | Start voice session |
| `/v1/mobile/voice/stop` | POST | Stop voice session |
| `/v1/mobile/remote/status` | GET | Remote access status |
| `/v1/mobile/remote/config` | PUT | Save remote access config |
| `/v1/mobile/connected-apps` | GET | List connected apps |
| `/v1/mobile/connected-apps/{app}/connect` | POST | Connect app |
| `/v1/mobile/connected-apps/{app}/disconnect` | POST | Disconnect app |
| `/v1/mobile/push/register` | POST | Register push device token |

## Security

- **Mobile Token**: Stored in iOS Keychain (not UserDefaults)
- **Voice API key**: Stored in App Storage on-device only; never logged
- **Keychain Service**: `org.narna.mobile`
- **Token Format**: `narna_mobile_<random_32_bytes>`
- **Token Expiry**: 30 days (renewable)
- **Camera / Mic**: Required for QR scanning and voice (`Info.plist` usage strings)

## Troubleshooting

### "No Active Bots" Error

- Ensure desktop agent is running
- Check backend is accessible at base URL
- Verify mobile token hasn't expired (re-pair if needed)

### QR Scanner Not Working

- Grant camera permission in iOS Settings
- Try manual code entry as fallback

### WebSocket Connection Failed

- Verify backend WebSocket endpoint is accessible
- WebSocket URL should be `ws://` (not `wss://` for localhost)

### "Invalid mobile token" Error

- Token expired (30 days) or backend restarted
- Solution: Unpair and re-pair device

## Architecture

### MVVM Pattern

- **Models**: Pure data structures (Codable)
- **Views**: SwiftUI views (UI only)
- **ViewModels**: Business logic + state management
- **Services**: API calls, WebSocket, Keychain

### Async/Await

All API calls use Swift concurrency via `NARNAAPIService`.

## License

MIT License - see [LICENSE](../../LICENSE) file

## Support

- **Documentation**: [docs/MOBILE-API.md](../../docs/MOBILE-API.md)
- **Issues**: https://github.com/narna/narna/issues

---

Built with ❤️ by the NARNA Team
