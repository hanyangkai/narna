#!/bin/bash
# Submit NARNA Android to Google Play Internal Testing
# Requires: Android SDK, valid Play Console service account

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANDROID_DIR="$SCRIPT_DIR/../mobile-android"

echo "🤖 NARNA Android Play Console Submission"
echo "========================================="
echo ""

# Check prerequisites
if [ ! -f "$ANDROID_DIR/build.gradle.kts" ]; then
    echo "❌ Error: Android project not found at $ANDROID_DIR"
    exit 1
fi

if ! command -v bundle &> /dev/null; then
    echo "❌ Error: Bundler not found. Run: gem install bundler"
    exit 1
fi

# Check environment variables
echo "🔑 Checking credentials..."

if [ -z "$GOOGLE_PLAY_JSON_KEY_PATH" ]; then
    echo "⚠️  GOOGLE_PLAY_JSON_KEY_PATH not set."
    echo "   Create service account: https://play.google.com/console → Setup → API access"
    read -p "Enter path to service-account.json: " GOOGLE_PLAY_JSON_KEY_PATH
    export GOOGLE_PLAY_JSON_KEY_PATH
fi

if [ ! -f "$GOOGLE_PLAY_JSON_KEY_PATH" ]; then
    echo "❌ Error: Service account JSON not found at $GOOGLE_PLAY_JSON_KEY_PATH"
    exit 1
fi

# Check signing keystore
if [ -z "$ANDROID_KEYSTORE_PATH" ]; then
    echo "⚠️  ANDROID_KEYSTORE_PATH not set."
    
    if [ -f "$ANDROID_DIR/narna-release.keystore" ]; then
        ANDROID_KEYSTORE_PATH="$ANDROID_DIR/narna-release.keystore"
        echo "   Found keystore at: $ANDROID_KEYSTORE_PATH"
    else
        echo "   Generate with: keytool -genkey -v -keystore narna-release.keystore ..."
        read -p "Enter path to keystore: " ANDROID_KEYSTORE_PATH
    fi
    
    export ANDROID_KEYSTORE_PATH
fi

if [ -z "$ANDROID_KEYSTORE_PASSWORD" ]; then
    read -sp "Enter keystore password: " ANDROID_KEYSTORE_PASSWORD
    echo ""
    export ANDROID_KEYSTORE_PASSWORD
fi

if [ -z "$ANDROID_KEY_ALIAS" ]; then
    read -p "Enter key alias (default: narna): " ANDROID_KEY_ALIAS
    ANDROID_KEY_ALIAS="${ANDROID_KEY_ALIAS:-narna}"
    export ANDROID_KEY_ALIAS
fi

if [ -z "$ANDROID_KEY_PASSWORD" ]; then
    read -sp "Enter key password: " ANDROID_KEY_PASSWORD
    echo ""
    export ANDROID_KEY_PASSWORD
fi

echo "✅ Credentials configured"

# Navigate to Android project
cd "$ANDROID_DIR"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
bundle install

# Show current version
CURRENT_VERSION=$(grep "versionName" app/build.gradle.kts | head -1 | sed 's/.*"\(.*\)".*/\1/')
CURRENT_CODE=$(grep "versionCode" app/build.gradle.kts | head -1 | sed 's/[^0-9]//g')

echo ""
echo "📊 Current Version: $CURRENT_VERSION ($CURRENT_CODE)"
echo ""

# Confirm submission
read -p "Submit to Play Console Internal Testing? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ Submission cancelled"
    exit 0
fi

# Run Play Console beta lane
echo ""
echo "🚀 Submitting to Play Console..."
bundle exec fastlane android beta

echo ""
echo "✅ Play Console Submission Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Open Play Console: https://play.google.com/console"
echo "   2. Go to Testing → Internal testing"
echo "   3. Create release from uploaded AAB"
echo "   4. Add testers by email"
echo "   5. Share testing link: https://play.google.com/apps/internaltest/[TOKEN]"
echo ""
echo "📧 Processing usually takes 1-2 hours."
echo ""
