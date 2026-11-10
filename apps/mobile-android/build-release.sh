#!/bin/bash
# NARNA Android - Build Release AAB Script

set -e  # Exit on error

echo "🚀 NARNA Android - Building Release AAB"
echo "========================================"

# Check for Android SDK
if [ -z "$ANDROID_HOME" ]; then
    echo "❌ ERROR: ANDROID_HOME not set"
    echo "Please install Android SDK and set ANDROID_HOME environment variable"
    echo ""
    echo "Example:"
    echo "  export ANDROID_HOME=~/android-sdk"
    echo "  export PATH=\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools"
    exit 1
fi

echo "✓ Android SDK found at: $ANDROID_HOME"

# Check for keystore
KEYSTORE_PATH="${ANDROID_KEYSTORE_PATH:-./narna-release.keystore}"
if [ ! -f "$KEYSTORE_PATH" ]; then
    echo "❌ ERROR: Keystore not found at: $KEYSTORE_PATH"
    echo "Generate keystore first or set ANDROID_KEYSTORE_PATH"
    exit 1
fi

echo "✓ Keystore found at: $KEYSTORE_PATH"

# Set signing environment variables if not already set
export ANDROID_KEYSTORE_PATH="${ANDROID_KEYSTORE_PATH:-./narna-release.keystore}"
export ANDROID_KEYSTORE_PASSWORD="${ANDROID_KEYSTORE_PASSWORD:-narnarelease2024}"
export ANDROID_KEY_ALIAS="${ANDROID_KEY_ALIAS:-narna}"
export ANDROID_KEY_PASSWORD="${ANDROID_KEY_PASSWORD:-narnarelease2024}"

echo ""
echo "Building AAB..."
echo "----------------"

# Clean previous builds
./gradlew clean

# Build release AAB
./gradlew bundleRelease

# Check if AAB was created
AAB_PATH="app/build/outputs/bundle/release/app-release.aab"
if [ ! -f "$AAB_PATH" ]; then
    echo "❌ ERROR: AAB not created at: $AAB_PATH"
    exit 1
fi

# Get AAB size
AAB_SIZE=$(du -h "$AAB_PATH" | cut -f1)

echo ""
echo "✅ SUCCESS!"
echo "=========="
echo "AAB built at: $AAB_PATH"
echo "AAB size: $AAB_SIZE"
echo ""
echo "Next steps:"
echo "1. Test the AAB using bundletool (optional)"
echo "2. Upload to Google Play Console manually, OR"
echo "3. Run 'bundle exec fastlane android release' to upload automatically"
echo "   (Requires GOOGLE_PLAY_JSON_KEY_PATH environment variable)"
