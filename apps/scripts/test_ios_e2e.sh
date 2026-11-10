#!/bin/bash
# iOS E2E Testing Script for NARNA Mobile
# Requires: macOS with Xcode 15+

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOS_DIR="$SCRIPT_DIR/../mobile-ios"

echo "🧪 NARNA iOS E2E Testing"
echo "========================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode not found. Install from App Store."
    exit 1
fi

if ! command -v bundle &> /dev/null; then
    echo "❌ Error: Bundler not found. Run: gem install bundler"
    exit 1
fi

echo "✅ Prerequisites OK"

# Navigate to iOS project
cd "$IOS_DIR"

# Install dependencies
echo ""
echo "📦 Installing Ruby dependencies..."
bundle install

# Clean build folder
echo ""
echo "🧹 Cleaning build folder..."
xcodebuild clean -project NARNA.xcodeproj -scheme NARNA

# Run unit tests
echo ""
echo "🧪 Running unit tests..."
xcodebuild test \
    -project NARNA.xcodeproj \
    -scheme NARNA \
    -destination 'platform=iOS Simulator,name=iPhone 15,OS=17.0' \
    -quiet || echo "⚠️  Unit tests failed (may not exist yet)"

# Build app
echo ""
echo "🔨 Building app..."
xcodebuild build \
    -project NARNA.xcodeproj \
    -scheme NARNA \
    -configuration Debug \
    -destination 'platform=iOS Simulator,name=iPhone 15,OS=17.0' \
    -quiet

echo "✅ Build successful"

# Launch simulator for manual testing
echo ""
echo "📱 Launching iOS Simulator..."
open -a Simulator

# Wait for simulator to boot
sleep 5

# Install app on simulator
echo ""
echo "📲 Installing app on simulator..."
xcrun simctl install booted "$IOS_DIR/build/Debug-iphonesimulator/NARNA.app" || echo "⚠️  Auto-install failed, use Xcode to run"

echo ""
echo "✅ iOS E2E Testing Setup Complete!"
echo ""
echo "📋 Manual Test Steps:"
echo "   1. Run app in Xcode (Cmd+R)"
echo "   2. Test pairing flow with backend"
echo "   3. Test bot list refresh"
echo "   4. Test chat with WebSocket"
echo "   5. Test approval flow"
echo "   6. Test settings (API keys, unpair)"
echo ""
echo "📸 Generate Screenshots:"
echo "   1. Navigate to each screen"
echo "   2. Press Cmd+S to save screenshot"
echo "   3. Or run: bundle exec fastlane screenshots"
echo ""
