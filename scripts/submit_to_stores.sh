#!/bin/bash
# Auto-submit NARNA mobile apps to App Store & Google Play
# Requires: fastlane, credentials configured

set -e

echo "🚀 NARNA Mobile - Auto Submission to App Stores"
echo "================================================"
echo ""

# Check environment variables
check_env() {
  local var_name=$1
  if [ -z "${!var_name}" ]; then
    echo "❌ Error: $var_name not set"
    exit 1
  fi
}

echo "📋 Checking credentials..."

# iOS credentials
if [ "$SUBMIT_IOS" = "true" ]; then
  check_env "APPLE_ID"
  check_env "APPLE_TEAM_ID"
  check_env "FASTLANE_API_KEY_PATH"
  echo "✅ iOS credentials OK"
fi

# Android credentials
if [ "$SUBMIT_ANDROID" = "true" ]; then
  check_env "GOOGLE_PLAY_JSON_KEY_PATH"
  check_env "ANDROID_KEYSTORE_PATH"
  check_env "ANDROID_KEYSTORE_PASSWORD"
  check_env "ANDROID_KEY_ALIAS"
  check_env "ANDROID_KEY_PASSWORD"
  echo "✅ Android credentials OK"
fi

echo ""

# Submit iOS
if [ "$SUBMIT_IOS" = "true" ]; then
  echo "📱 Submitting iOS app to App Store..."
  cd apps/mobile-ios
  
  # Install dependencies
  bundle install
  bundle exec fastlane ios screenshots || echo "⚠️  Screenshot generation failed, continuing..."
  
  # Upload to App Store
  bundle exec fastlane ios release
  
  echo "✅ iOS app submitted to App Store!"
  echo "   - Check status: https://appstoreconnect.apple.com"
  echo "   - Review typically takes 1-2 weeks"
  echo ""
  
  cd ../..
fi

# Submit Android
if [ "$SUBMIT_ANDROID" = "true" ]; then
  echo "🤖 Submitting Android app to Google Play..."
  cd apps/mobile-android
  
  # Install dependencies
  bundle install
  bundle exec fastlane android screenshots || echo "⚠️  Screenshot generation failed, continuing..."
  
  # Upload to Google Play
  bundle exec fastlane android release
  
  echo "✅ Android app submitted to Google Play!"
  echo "   - Check status: https://play.google.com/console"
  echo "   - Review typically takes 1-3 days"
  echo ""
  
  cd ../..
fi

echo ""
echo "🎉 Submission complete!"
echo ""
echo "Next steps:"
echo "1. Monitor App Store Connect / Play Console for review status"
echo "2. Respond to any reviewer questions"
echo "3. Celebrate when apps go live! 🥳"
echo ""
echo "App links (after approval):"
echo "- iOS: https://apps.apple.com/app/narna-mobile/id[TO_BE_ASSIGNED]"
echo "- Android: https://play.google.com/store/apps/details?id=org.narna.mobile"
