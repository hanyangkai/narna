# App Store Screenshots

This directory should contain screenshots for NARNA Mobile iOS app submission.

## Required Screenshot Sizes

### iPhone

**6.7" Display (iPhone 15 Pro Max, iPhone 14 Pro Max)**
- Resolution: 1290 x 2796 pixels
- Format: PNG or JPEG
- Required: 3-10 screenshots

**6.5" Display (iPhone 14 Plus, iPhone 13 Pro Max, iPhone 12 Pro Max)**
- Resolution: 1284 x 2778 pixels
- Format: PNG or JPEG
- Required: 3-10 screenshots (if not providing 6.7" screenshots)

**5.5" Display (iPhone 8 Plus, iPhone 7 Plus, iPhone 6s Plus)**
- Resolution: 1242 x 2208 pixels
- Format: PNG or JPEG
- Optional but recommended for compatibility

### iPad

**12.9" Display (iPad Pro 12.9-inch)**
- Resolution: 2048 x 2732 pixels
- Format: PNG or JPEG
- Required: 3-10 screenshots

**Alternatively:**

**11" Display (iPad Pro 11-inch)**
- Resolution: 1668 x 2388 pixels
- Format: PNG or JPEG

## Naming Convention

Use sequential numbering with descriptive names:

```
01-pairing-screen.png
02-qr-scanner.png
03-bot-list.png
04-chat-interface.png
05-approvals.png
06-settings.png
```

## Suggested Screenshots to Capture

1. **Pairing Screen** - First impression, QR code pairing UI
2. **QR Scanner** - Show camera scanning functionality
3. **Bot List** - Connected agents overview
4. **Chat Interface** - AI conversation in action
5. **Approval Card** - Command/file approval UI
6. **Settings** - Configuration options

## Screenshot Guidelines

✅ **DO:**
- Use real content (not Lorem Ipsum)
- Show actual features working
- Use high-quality images
- Portrait orientation only
- Remove status bar clutter (battery, time) - use `override_status_bar: true` in fastlane
- Show diversity in content

❌ **DON'T:**
- Include personal information
- Show placeholder text
- Use low resolution images
- Include offensive content
- Use landscape orientation for phone screenshots

## Automated Generation

If you have fastlane and Xcode installed:

```bash
cd apps/mobile-ios
bundle exec fastlane screenshots
```

This will automatically:
1. Build the app
2. Run UI tests
3. Capture screenshots for all devices
4. Save them to this directory

## Manual Capture

1. Open NARNA app in iOS Simulator
2. Navigate to each screen
3. Cmd+S to save screenshot
4. Resize to required dimensions using Preview or ImageMagick:

```bash
# Resize to iPhone 15 Pro Max
sips -z 2796 1290 screenshot.png --out 01-pairing-screen.png

# Resize to iPad Pro 12.9"
sips -z 2732 2048 screenshot.png --out 01-pairing-screen-ipad.png
```

## Current Status

⏳ **Waiting for screenshots from Testing Agent**

Expected delivery:
- [ ] iPhone 6.7" screenshots (3-5 images)
- [ ] iPad Pro 12.9" screenshots (3-5 images)

## Verification

Before submission, verify:

```bash
# Check image dimensions
cd apps/mobile-ios/fastlane/screenshots/en-US
sips -g pixelWidth -g pixelHeight *.png
```

Expected output:
- iPhone: 1290 x 2796
- iPad: 2048 x 2732

## Resources

- [App Store Screenshot Specifications](https://help.apple.com/app-store-connect/#/devd274dd925)
- [iOS Device Screen Sizes](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Fastlane Screenshots Guide](https://docs.fastlane.tools/getting-started/ios/screenshots/)

---

**Note:** Once screenshots are added to this directory, they will be automatically included in the App Store submission when running `bundle exec fastlane ios release`.
