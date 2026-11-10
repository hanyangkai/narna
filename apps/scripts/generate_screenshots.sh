#!/bin/bash
# Automated Screenshot Generation for NARNA Mobile
# Generates screenshots for both iOS and Android store submissions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOS_DIR="$SCRIPT_DIR/../mobile-ios"
ANDROID_DIR="$SCRIPT_DIR/../mobile-android"

echo "📸 NARNA Mobile Screenshot Generation"
echo "======================================"
echo ""

# Parse arguments
PLATFORM="${1:-both}"  # ios, android, or both

generate_ios_screenshots() {
    echo "📱 Generating iOS Screenshots..."
    echo "--------------------------------"
    
    cd "$IOS_DIR"
    
    # Check prerequisites
    if ! command -v bundle &> /dev/null; then
        echo "❌ Error: Bundler not found. Run: gem install bundler"
        return 1
    fi
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    bundle install
    
    # Generate screenshots
    echo "📸 Running snapshot..."
    bundle exec fastlane snapshot || {
        echo "⚠️  Automated snapshot failed. Trying manual approach..."
        echo ""
        echo "Manual iOS Screenshot Steps:"
        echo "1. Run app in Simulator (iPhone 15 Pro Max)"
        echo "2. Navigate to pairing screen → Cmd+S → Save as '01_pairing.png'"
        echo "3. Navigate to bot list → Cmd+S → Save as '02_bot_list.png'"
        echo "4. Navigate to chat → Cmd+S → Save as '03_chat.png'"
        echo "5. Show approval card → Cmd+S → Save as '04_approval.png'"
        echo "6. Navigate to settings → Cmd+S → Save as '05_settings.png'"
        echo "7. Show real-time update → Cmd+S → Save as '06_realtime.png'"
        echo ""
        echo "Save to: $IOS_DIR/fastlane/screenshots/en-US/"
        return 1
    }
    
    echo "✅ iOS screenshots generated in: fastlane/screenshots/"
    echo ""
}

generate_android_screenshots() {
    echo "🤖 Generating Android Screenshots..."
    echo "-----------------------------------"
    
    cd "$ANDROID_DIR"
    
    # Check prerequisites
    if ! command -v adb &> /dev/null; then
        echo "❌ Error: Android SDK not found."
        return 1
    fi
    
    # Build test APKs
    echo "🔨 Building test APKs..."
    ./gradlew assembleDebug
    ./gradlew assembleDebugAndroidTest || echo "⚠️  No instrumentation tests found"
    
    # Generate screenshots
    echo "📸 Running screengrab..."
    bundle install
    bundle exec fastlane screengrab || {
        echo "⚠️  Automated screengrab failed. Trying manual approach..."
        echo ""
        echo "Manual Android Screenshot Steps:"
        echo "1. Run app in Emulator (Pixel 8 Pro)"
        echo "2. Navigate to pairing screen → Ctrl+S → Save as '01_pairing.png'"
        echo "3. Navigate to bot list → Ctrl+S → Save as '02_bot_list.png'"
        echo "4. Navigate to chat → Ctrl+S → Save as '03_chat.png'"
        echo "5. Show approval → Ctrl+S → Save as '04_approval.png'"
        echo "6. Navigate to settings → Ctrl+S → Save as '05_settings.png'"
        echo "7. Show real-time → Ctrl+S → Save as '06_realtime.png'"
        echo "8. Switch to 10\" tablet emulator"
        echo "9. Landscape → Ctrl+S → Save as '07_tablet_landscape.png'"
        echo "10. Portrait → Ctrl+S → Save as '08_tablet_portrait.png'"
        echo ""
        echo "Phone: $ANDROID_DIR/fastlane/metadata/android/en-US/images/phoneScreenshots/"
        echo "Tablet: $ANDROID_DIR/fastlane/metadata/android/en-US/images/tenInchScreenshots/"
        return 1
    }
    
    echo "✅ Android screenshots generated in: fastlane/metadata/android/en-US/images/"
    echo ""
}

# Generate based on platform
case "$PLATFORM" in
    ios)
        generate_ios_screenshots
        ;;
    android)
        generate_android_screenshots
        ;;
    both)
        generate_ios_screenshots
        echo ""
        generate_android_screenshots
        ;;
    *)
        echo "❌ Invalid platform: $PLATFORM"
        echo "Usage: $0 [ios|android|both]"
        exit 1
        ;;
esac

echo ""
echo "✅ Screenshot Generation Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Review all screenshots for quality"
echo "   2. Optimize images (strip metadata, compress)"
echo "   3. Upload to App Store Connect / Play Console"
echo ""
echo "Screenshot Checklist:"
echo "   iOS (6 required):"
echo "   - [ ] 01_pairing.png"
echo "   - [ ] 02_bot_list.png"
echo "   - [ ] 03_chat.png"
echo "   - [ ] 04_approval.png"
echo "   - [ ] 05_settings.png"
echo "   - [ ] 06_realtime.png"
echo ""
echo "   Android (8 required):"
echo "   - [ ] 01_pairing.png (phone)"
echo "   - [ ] 02_bot_list.png (phone)"
echo "   - [ ] 03_chat.png (phone)"
echo "   - [ ] 04_approval.png (phone)"
echo "   - [ ] 05_settings.png (phone)"
echo "   - [ ] 06_realtime.png (phone)"
echo "   - [ ] 07_tablet_landscape.png"
echo "   - [ ] 08_tablet_portrait.png"
echo ""
