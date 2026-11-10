# App Store Metadata

This directory contains all metadata for the NARNA Mobile app submission to the Apple App Store.

## Files

- **name.txt** - App name (30 chars max): "NARNA Mobile"
- **subtitle.txt** - Short description (30 chars max): "AI Agent Remote Control"
- **description.txt** - Full app description (4000 chars max)
- **keywords.txt** - Comma-separated keywords (100 chars max)
- **promotional_text.txt** - Promotional text (170 chars max)
- **privacy_url.txt** - Privacy policy URL
- **support_url.txt** - Support/help URL
- **marketing_url.txt** - Marketing website URL

## Language Support

Currently configured for:
- en-US (English - United States)

To add more languages, create additional directories:
- `es-ES/` for Spanish
- `fr-FR/` for French
- `vi/` for Vietnamese
- etc.

## Usage with Fastlane

These files are automatically used by the `deliver` action in the Fastlane configuration:

```ruby
deliver(
  metadata_path: "./fastlane/metadata",
  # ...
)
```

## Editing

You can edit these files directly, or use fastlane's built-in editor:

```bash
bundle exec fastlane deliver edit_app_metadata
```

## Screenshots

Screenshots should be placed in `../screenshots/en-US/` directory with the following naming convention:

- iPhone 6.7": `01-pairing.png`, `02-chat.png`, etc.
- iPad Pro 12.9": `01-pairing.png`, `02-chat.png`, etc.

## Privacy Policy Requirements

The privacy_url.txt must point to a live, accessible webpage that:
- Describes data collection practices
- Lists third-party services used
- Explains user rights
- Provides contact information

Current URL: https://narna.org/privacy

**Make sure this page is live before submitting!**
