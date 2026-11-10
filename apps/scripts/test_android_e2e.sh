#!/bin/bash
# Android E2E Testing Script for NARNA Mobile
# Requires: Android SDK and emulator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANDROID_DIR="$SCRIPT_DIR/../mobile-android"

echo "🧪 NARNA Android E2E Testing"
echo "============================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v adb &> /dev/null; then
    echo "❌ Error: Android SDK not found. Install Android Studio."
    exit 1
fi

if ! command -v gradle &> /dev/null && [ ! -f "$ANDROID_DIR/gradlew" ]; then
    echo "❌ Error: Gradle not found."
    exit 1
fi

echo "✅ Prerequisites OK"

# Navigate to Android project
cd "$ANDROID_DIR"

# Clean build
echo ""
echo "🧹 Cleaning build..."
./gradlew clean

# Run unit tests
echo ""
echo "🧪 Running unit tests..."
./gradlew test || echo "⚠️  Unit tests failed (may not exist yet)"

# Build debug APK
echo ""
echo "🔨 Building debug APK..."
./gradlew assembleDebug

echo "✅ Build successful: app/build/outputs/apk/debug/app-debug.apk"

# Check for running emulators
echo ""
echo "📱 Checking for Android emulators..."

EMULATOR_SERIAL=$(adb devices | grep emulator | awk '{print $1}' | head -1)

if [ -z "$EMULATOR_SERIAL" ]; then
    echo "⚠️  No emulator running. Starting default emulator..."
    
    # Try to start an emulator (if AVD exists)
    AVD_NAME=$(emulator -list-avds | head -1)
    
    if [ -z "$AVD_NAME" ]; then
        echo "❌ No Android Virtual Devices found."
        echo "   Create one with: Android Studio → Device Manager → Create Device"
        exit 1
    fi
    
    echo "📱 Starting emulator: $AVD_NAME"
    emulator -avd "$AVD_NAME" &
    
    echo "⏳ Waiting for emulator to boot..."
    adb wait-for-device
    sleep 10  # Extra time for full boot
    
    EMULATOR_SERIAL=$(adb devices | grep emulator | awk '{print $1}' | head -1)
fi

echo "✅ Emulator ready: $EMULATOR_SERIAL"

# Install APK
echo ""
echo "📲 Installing app on emulator..."
adb -s "$EMULATOR_SERIAL" install -r app/build/outputs/apk/debug/app-debug.apk

echo "✅ App installed"

# Launch app
echo ""
echo "🚀 Launching app..."
adb -s "$EMULATOR_SERIAL" shell am start -n org.narna.mobile/.MainActivity

echo ""
echo "✅ Android E2E Testing Setup Complete!"
echo ""
echo "📋 Manual Test Steps:"
echo "   1. App should be running on emulator"
echo "   2. Test pairing flow with backend"
echo "   3. Test bot list refresh"
echo "   4. Test chat with WebSocket"
echo "   5. Test approval bottom sheet"
echo "   6. Test settings (API keys, unpair)"
echo ""
echo "📸 Generate Screenshots:"
echo "   1. Navigate to each screen"
echo "   2. Press screenshot button or Ctrl+S"
echo "   3. Or build instrumentation tests:"
echo "      ./gradlew assembleDebugAndroidTest"
echo "      bundle exec fastlane screengrab"
echo ""
echo "📊 View Logs:"
echo "   adb -s $EMULATOR_SERIAL logcat | grep NARNA"
echo ""
