#!/bin/bash
# NARNA iOS App Store Setup Script
# Run this on macOS with Xcode installed

set -e

echo "🚀 NARNA iOS App Store Setup"
echo "================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode not found. Please install Xcode from the Mac App Store."
    exit 1
fi

if ! command -v bundle &> /dev/null; then
    echo "❌ Bundler not found. Installing..."
    sudo gem install bundler
fi

echo "✅ Prerequisites check passed"
echo ""

# Check environment variables
echo "🔐 Checking credentials..."

if [ -z "$APPLE_ID" ]; then
    echo "⚠️  APPLE_ID not set"
    echo "   Set it with: export APPLE_ID='your@email.com'"
fi

if [ -z "$APPLE_TEAM_ID" ]; then
    echo "⚠️  APPLE_TEAM_ID not set"
    echo "   Find your Team ID at: https://developer.apple.com/account"
fi

if [ -z "$FASTLANE_API_KEY_PATH" ] && [ -z "$FASTLANE_PASSWORD" ]; then
    echo "⚠️  No authentication method set"
    echo "   Option 1 (Recommended): App Store Connect API Key"
    echo "     export FASTLANE_API_KEY_PATH='~/AuthKey_XXX.p8'"
    echo "     export FASTLANE_API_KEY_ID='YOUR_KEY_ID'"
    echo "     export FASTLANE_API_KEY_ISSUER_ID='YOUR_ISSUER_ID'"
    echo ""
    echo "   Option 2: App-specific password"
    echo "     export FASTLANE_PASSWORD='xxxx-xxxx-xxxx-xxxx'"
fi

echo ""

# Navigate to project directory
cd "$(dirname "$0")"

echo "📦 Installing Ruby dependencies..."
if [ ! -f Gemfile ]; then
    echo "source 'https://rubygems.org'" > Gemfile
    echo "gem 'fastlane'" >> Gemfile
fi
bundle install

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Setup code signing:"
echo "   bundle exec fastlane setup_signing"
echo ""
echo "2. Build and submit to App Store:"
echo "   bundle exec fastlane ios release"
echo ""
echo "3. Or build only (no upload):"
echo "   bundle exec fastlane gym"
echo ""
echo "4. Check APP_STORE_CHECKLIST.md for detailed instructions"
echo ""
