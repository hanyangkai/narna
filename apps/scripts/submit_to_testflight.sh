#!/bin/bash
# Submit NARNA iOS to TestFlight
# Requires: macOS with Xcode, valid App Store Connect API key

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOS_DIR="$SCRIPT_DIR/../mobile-ios"

echo "✈️  NARNA iOS TestFlight Submission"
echo "===================================="
echo ""

# Check prerequisites
if [ ! -f "$IOS_DIR/NARNA.xcodeproj/project.pbxproj" ]; then
    echo "❌ Error: Xcode project not found at $IOS_DIR"
    exit 1
fi

if ! command -v bundle &> /dev/null; then
    echo "❌ Error: Bundler not found. Run: gem install bundler"
    exit 1
fi

# Check environment variables
echo "🔑 Checking credentials..."

if [ -z "$APPLE_ID" ]; then
    echo "⚠️  APPLE_ID not set. Reading from .env or prompting..."
    read -p "Enter Apple ID (email): " APPLE_ID
    export APPLE_ID
fi

if [ -z "$FASTLANE_API_KEY_PATH" ]; then
    echo "⚠️  FASTLANE_API_KEY_PATH not set."
    echo "   Download from: https://appstoreconnect.apple.com/access/api"
    read -p "Enter path to AuthKey_*.p8 file: " FASTLANE_API_KEY_PATH
    export FASTLANE_API_KEY_PATH
fi

if [ -z "$FASTLANE_KEY_ID" ]; then
    read -p "Enter App Store Connect Key ID: " FASTLANE_KEY_ID
    export FASTLANE_KEY_ID
fi

if [ -z "$FASTLANE_ISSUER_ID" ]; then
    read -p "Enter App Store Connect Issuer ID: " FASTLANE_ISSUER_ID
    export FASTLANE_ISSUER_ID
fi

echo "✅ Credentials configured"

# Navigate to iOS project
cd "$IOS_DIR"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
bundle install

# Show current version
CURRENT_VERSION=$(xcodebuild -showBuildSettings -project NARNA.xcodeproj -scheme NARNA | grep MARKETING_VERSION | awk '{print $3}' | head -1)
CURRENT_BUILD=$(xcodebuild -showBuildSettings -project NARNA.xcodeproj -scheme NARNA | grep CURRENT_PROJECT_VERSION | awk '{print $3}' | head -1)

echo ""
echo "📊 Current Version: $CURRENT_VERSION ($CURRENT_BUILD)"
echo ""

# Confirm submission
read -p "Submit to TestFlight? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ Submission cancelled"
    exit 0
fi

# Run TestFlight lane
echo ""
echo "🚀 Submitting to TestFlight..."
bundle exec fastlane ios beta

echo ""
echo "✅ TestFlight Submission Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Open App Store Connect: https://appstoreconnect.apple.com"
echo "   2. Go to TestFlight → NARNA Mobile"
echo "   3. Wait for build processing (~5-10 minutes)"
echo "   4. Add external testers (optional)"
echo "   5. Share TestFlight link: https://testflight.apple.com/join/[CODE]"
echo ""
echo "📧 You will receive an email when processing completes."
echo ""
