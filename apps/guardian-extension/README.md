# NARNA Guardian Extension (Chrome MV3)

**Protected Mode** for AI chat surfaces — citizen edge of the [Guardian Network](../../docs/GUARDIAN-NETWORK.md).

Slogan: *Every human protected. Every AI accountable. Every action governed.*

## Install (unpacked)

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select this folder: `apps/guardian-extension`
4. Open Options → confirm API base (`https://api.narna.org` or `http://127.0.0.1:8100` for local)
5. Visit ChatGPT / Claude / Gemini / DeepSeek / Copilot — badge **NARNA Protected** appears
6. Toggle Protected Mode in the popup

## Behavior

| Event | Action |
|-------|--------|
| Send message (Enter / Send) | `POST /v1/gateway/check` |
| Payment / contract / agent language | **Deny** (citizen default-deny) |
| Email-like ask | Banner → **Approve once** |
| CTI feed (1 min) | Local pattern block before network |
| Emergency broadcast | Chrome notification + CTI refresh |

## Icons

If icons are missing, Chrome still loads the extension; generate simple PNGs under `icons/` or reuse any 16/48/128 placeholder.

## Privacy

- No full-page MITM
- Citizen register is anonymous device key
- CTI signatures are pattern hashes only (NGS-0020)
