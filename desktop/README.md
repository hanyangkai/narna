# NARNA Desktop — run on your PC

Decision-quality AI agent on Windows / macOS / Linux. **BYOK** — keys stay in `~/.narna`.

## Windows portable (no Python)

1. Download `NARNA-Desktop-windows.zip` from [Releases](https://github.com/hanyangkai/narna/releases)
2. Unzip → double-click `NARNA-Desktop.exe`
3. Browser opens `http://127.0.0.1:8765/` — paste your LLM key

Build locally: `.\scripts\build_desktop_exe.ps1`

## Quick install (needs Python 3.11+)

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.ps1 | iex
narna desktop
```

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.sh | bash
narna desktop
```

### pip

```bash
pip install "narna[desktop]"
narna desktop
```

## Modes

| Command | What |
|---------|------|
| `narna desktop` | Local Ask UI in browser |
| `narna desktop --tui` | Fullscreen TUI |
| `NARNA-Desktop.exe` | Same UI, no Python |

## Data

Config + memory: `~/.narna` (override `NARNA_HOME` / `--workspace`).
