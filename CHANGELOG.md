# Changelog

## [0.2.0] — 2026-08-27

### Desktop (download for PC)
- `narna desktop` — local Ask UI on 127.0.0.1, BYOK keys in `~/.narna`
- Portable **NARNA-Desktop.exe** (PyInstaller) — no Python required on Windows
- Install scripts: `desktop/install.ps1`, `desktop/install.sh`
- Download page: https://narna.org/download

### Agent runtime (Hermes parity P1–P9)
- 44 tools including browser_vision, execute_code, shell backends (local/docker/ssh/modal/daytona)
- `narna tui`, `narna chat`, gateway compose profile + DM pairing
- TTS outbound + Telegram voice reply (BYOK)

### Decision moat (Track B)
- Decision Trace, Replay, universal `narna evaluate`, router modes (cheap/quality/critical)
- MEMORY.md / USER.md injection
- Decision Benchmark v0 (`narna benchmark run`)
- Skills Hub zip/sync + public index

### SDK
- `from narna.runtime import NarnaAgent` · `from narna.decision import DecisionTraceStore`

## [0.1.0] — 2026-07-20

- Initial PyPI release — UGS governance SDK, `pip install narna`
