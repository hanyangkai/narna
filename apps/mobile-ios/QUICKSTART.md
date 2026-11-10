# NARNA iOS App - Quick Start Guide

Get the NARNA iOS companion app running in 5 minutes.

## Prerequisites

- Mac with Xcode 15.0+
- iOS device or simulator (iOS 16.0+)
- NARNA backend running

## Step 1: Start Backend (2 min)

```bash
# Terminal 1: Start backend server
cd web/backend
uvicorn app.main:app --reload --port 8765
```

Backend should be running at `http://localhost:8765`

## Step 2: Open in Xcode (1 min)

```bash
cd apps/mobile-ios/NARNA
open NARNA.xcodeproj
```

Xcode will open the project automatically.

## Step 3: Configure Signing (30 sec)

1. In Xcode, select **NARNA** target (top left)
2. Go to **Signing & Capabilities** tab
3. Check **Automatically manage signing**
4. Select your **Team** from dropdown
5. Bundle ID will auto-update to avoid conflicts if needed

## Step 4: Build & Run (30 sec)

### On Simulator (recommended for testing)

1. Select **iPhone 15 Pro** (or any iPhone) from device menu
2. Press **⌘ + R** (or click ▶️ Run button)
3. Wait for build to complete

### On Physical Device

1. Connect iPhone via USB
2. Unlock device and trust computer
3. Select your iPhone from device menu
4. Press **⌘ + R**

## Step 5: Pair with Desktop (1 min)

### On Desktop

```bash
# Terminal 2: Start desktop agent with pairing
python -m narna.desktop_server --enable-mobile-pairing
```

Desktop will display:
```
📱 Mobile Pairing Enabled
   Code: 123456
   Scan QR or enter code on mobile app
```

### On iOS App

**Option A - QR Scan (fastest)**
1. Tap "Scan QR Code"
2. Allow camera access
3. Point at QR code on desktop
4. ✅ Paired!

**Option B - Manual Entry**
1. Enter the 6-digit code: `123456`
2. Tap "Verify Code"
3. ✅ Paired!

## Step 6: Use the App

### View Bots

- See all active bots from your desktop agent
- Pull down to refresh
- Tap any bot to open chat

### Chat with Bot

1. Tap a bot from the list
2. Type your message
3. Real-time responses via WebSocket
4. Bot status shown at top (Idle/Working/Waiting Approval)

### Handle Approvals

When bot needs approval:
1. Orange badge appears on bot list
2. Tap bot to see approval request
3. Review command/action details
4. Tap "Allow" or "Deny"

## Troubleshooting

### "No Active Bots"

- Check backend is running: `curl http://localhost:8765/v1/mobile/health`
- Start a desktop agent session
- Pull down to refresh

### QR Scanner Won't Open

- Grant camera permission in iOS Settings → NARNA
- Try manual code entry instead

### Build Errors in Xcode

**"No signing certificate found"**
- Add Apple ID in Xcode → Settings → Accounts
- Or use "Sign to Run Locally" option

**"Failed to register bundle identifier"**
- Change Bundle ID in Signing & Capabilities
- Use `com.yourname.narna` instead

### Connection Issues

**Local Testing (simulator + localhost)**
```
Base URL: http://localhost:8765  ✅
```

**Local Testing (physical device + Mac)**
```
Base URL: http://192.168.1.xxx:8765  ✅
(Use your Mac's local IP)
```

**Remote Access**
```
# Use ngrok or cloudflare tunnel
ngrok http 8765

# Update Base URL in Settings to:
Base URL: https://xyz.ngrok.io  ✅
```

## Next Steps

- 📖 Read full docs: [README.md](README.md)
- 🔧 Configure settings (gear icon)
- 📱 Test on physical device
- 🚀 Deploy to TestFlight (optional)

## Common Workflows

### Test Pairing Flow

```bash
# Unpair device
Settings → Unpair Device

# Generate new code
# Desktop will show new code

# Re-pair with QR or code
```

### Test Approval Flow

```bash
# On desktop, trigger shell command
# iOS app shows approval request
# Allow/Deny from mobile
```

### Test WebSocket

```bash
# Start chat with bot
# Bot sends message
# Should appear instantly (< 1s latency)
```

## Production Deployment

### TestFlight (Internal Testing)

1. Archive app in Xcode (Product → Archive)
2. Upload to App Store Connect
3. Add internal testers
4. Install via TestFlight app

### App Store Release

1. Complete app metadata
2. Add screenshots (iPhone 6.7", 6.5")
3. Submit for review
4. Wait for approval (~24-48 hours)

## Support

- 📝 API Docs: [docs/MOBILE-API.md](../../docs/MOBILE-API.md)
- 🐛 Issues: https://github.com/narna/narna/issues
- 💬 Discord: https://discord.gg/narna

---

**Total Setup Time**: ~5 minutes ⚡

Ready to control NARNA from your iPhone! 🎉
