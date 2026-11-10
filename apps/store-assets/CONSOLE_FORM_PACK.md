# Store Console Form Pack — paste-ready

**Bundle / package ID:** `org.narna.mobile`  
**Assets folder:** `apps/store-assets/` + Fastlane metadata paths below  
**Privacy:** https://narna.org/privacy  
**Support:** https://narna.org/support  
**Marketing:** https://narna.org  

> Agent **cannot** click Submit without your Apple/Google login.  
> Paste these fields into the consoles, upload assets, then Submit.

---

## App Store Connect (iOS)

Open: https://appstoreconnect.apple.com/apps

| Field | Value |
|-------|--------|
| Name | NARNA Mobile |
| Subtitle | AI Agent Remote Control |
| Primary category | Productivity |
| Secondary | Developer Tools |
| Content rights | Does not contain third-party content |
| Age rating | 4+ (no unrestricted web, no gambling; user-generated only via your own bot) |
| Privacy Policy URL | https://narna.org/privacy |
| Support URL | https://narna.org/support |
| Marketing URL | https://narna.org |
| Copyright | 2026 NARNA |
| Price | Free (+ optional NARNA Pro IAP) |

**Promotional text**
```
Control AI agents remotely. Approve commands, chat with Claude/ChatGPT/Gemini. Free & open source.
```

**Description** — file: `apps/mobile-ios/fastlane/metadata/en-US/description.txt`

**Keywords**
```
AI,agent,bot,automation,Claude,ChatGPT,remote,developer
```

**What's New (1.0.0)**
```
First release: pair Desktop NARNA bot by QR, chat, inbox Allow/Deny, routines, voice, dual-path AI (Desktop CLI / BYOK or NARNA Pro).
```

**Screenshots (iPhone 6.7")**  
`apps/mobile-ios/fastlane/screenshots/en-US/01-onboarding.png` … `04-chat.png`

**App icon**  
`apps/store-assets/icon-1024.png`

**IAP products** (create if not exist)

| Product ID | Type | Price |
|------------|------|------:|
| `narna_pro_monthly` | Auto-renewable | $19.99 |
| `narna_pro_yearly` | Auto-renewable | $159.99 |

---

## Google Play Console (Android)

Open: https://play.google.com/console

| Field | Value |
|-------|--------|
| App name | NARNA Mobile |
| Short description | Remote control for AI agents |
| Full description | `apps/mobile-android/fastlane/metadata/android/en-US/full_description.txt` |
| App category | Productivity |
| Tags | AI, automation, developer tools |
| Contact email | enterprise@narna.ai |
| Privacy policy | https://narna.org/privacy |
| App access | All features available / or provide demo Desktop pairing notes |
| Ads | No |
| Target audience | 18+ recommended (productivity) |
| News app | No |
| COVID | No |
| Data safety | Collect: App activity (chat/approvals), App info; Purpose: App functionality; Encrypted in transit; Users can request deletion |

**Graphics**

| Asset | Path | Size |
|-------|------|------|
| Hi-res icon | `…/images/icon.png` | 512×512 |
| Feature graphic | `…/images/featureGraphic.png` | 1024×500 |
| Phone screenshots | `…/images/phoneScreenshots/*.png` | 1080×1920 ×4 |

**Subscriptions**

| Product ID | Price |
|------------|------:|
| `narna_pro_monthly` | $19.99 |
| `narna_pro_yearly` | $159.99 |

**Release**  
Upload signed AAB → Internal testing first → Production when ready → **Send for review**.

---

## Still needs your machine

1. Apple Developer login + Mac build IPA (or CI macOS).  
2. Play Console account + service account JSON for Fastlane (optional).  
3. Click **Submit for Review** / **Send for review**.
