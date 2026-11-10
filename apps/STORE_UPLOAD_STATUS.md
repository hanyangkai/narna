# Store Upload Status — Real Status

**Updated**: Nov 10, 2026 13:34 Asia/Saigon

## Reality Check

| Platform | Built? | Uploaded? | Waiting review? |
|----------|--------|-----------|-----------------|
| **Android (Play)** | ✅ YES — AAB ready | ❌ NO | ❌ Not yet |
| **iOS (App Store)** | ❌ NO | ❌ NO | ❌ Not yet |

## Why not uploaded yet

1. **This machine is Linux** — no Xcode → cannot build/sign iOS IPA here.
2. **No store credentials in env**:
   - Missing `GOOGLE_PLAY_JSON_KEY_PATH` (Play service account JSON)
   - Missing Apple `AuthKey_*.p8` / `APPLE_ID` / `APPLE_TEAM_ID`

## Android AAB (ready NOW)

```
/workspace/apps/mobile-android/dist/narna-mobile-0.1.0.aab
/opt/cursor/artifacts/narna-mobile-release.aab
```

- package: `org.narna.mobile`
- versionName: `0.1.0`
- versionCode: `1`
- signed with: `narna-release.keystore`

### Upload to Play (needs your JSON key)

```bash
export GOOGLE_PLAY_JSON_KEY_PATH=/path/to/play-service-account.json
cd apps/mobile-android
bundle exec fastlane android release
# OR manual: Play Console → Create app → Production → Upload AAB
```

## iOS (needs Mac + Xcode)

Cannot finish on this Linux VM. On a Mac:

```bash
cd apps/mobile-ios
./setup-app-store.sh
export APPLE_ID=...
export APPLE_TEAM_ID=...
export FASTLANE_API_KEY_PATH=~/AuthKey_XXX.p8
bundle exec fastlane ios release
```

## What you must provide to finish auto-upload

1. Google Play service account JSON (with Play Console API access)
2. Apple App Store Connect API key (.p8 + Key ID + Issuer ID + Team ID)
3. For iOS: a macOS runner with Xcode (this VM cannot)
