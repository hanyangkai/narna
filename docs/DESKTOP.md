# NARNA Desktop

Run the **local AI agent** on your PC — Hermes-like chat + tools + ADQA, no cloud account required.

## Quick start

| Platform | Download | Run |
|----------|----------|-----|
| **Windows** | [NARNA-Desktop-windows.zip](https://github.com/hanyangkai/narna/releases/latest) | `NARNA-Desktop.exe` |
| **macOS** | [NARNA-Desktop-macos.zip](https://github.com/hanyangkai/narna/releases/latest) | see Gatekeeper below |
| **Any OS (recommended if zip blocked)** | `pip install "narna[desktop]"` | `narna desktop` |

Browser opens at `http://127.0.0.1:8765/`.

### macOS — Apple blocks “unidentified developer”

The GitHub zip is **not Apple-notarized** yet (unsigned PyInstaller build). Gatekeeper shows *“cannot be opened because Apple cannot check it for malicious software”* or *“damaged”*.

**Fix A — Terminal (fastest):**

```bash
# after unzip, path is usually ~/Downloads/NARNA-Desktop
xattr -cr ~/Downloads/NARNA-Desktop
chmod +x ~/Downloads/NARNA-Desktop/NARNA-Desktop
~/Downloads/NARNA-Desktop/NARNA-Desktop
```

Or from the repo:

```bash
bash scripts/macos_fix_gatekeeper.sh ~/Downloads/NARNA-Desktop
```

**Fix B — Finder:** Right-click `NARNA-Desktop` → **Open** → **Open** (first time only). Do not double-click.

**Fix C — skip the zip** (needs Python 3.11+):

```bash
pip install "narna[desktop]"
narna desktop
```

## How it works (Hermes-style)

1. **Download** portable app or install via pip
2. **Launch** — local FastAPI agent server starts on `127.0.0.1`
3. **Setup wizard** — paste OpenRouter / OpenAI / Ollama key (BYOK)
4. **Chat** — agent runs tools on your PC (shell, browser, memory, skills)
5. **ADQA** — every reply scored with Decision Quality (DQS)

All data stays in `~/.narna/` (config, sessions, decision memory, traces).

## CLI equivalents

```bash
narna desktop          # browser UI (default)
narna desktop --tui    # fullscreen terminal UI
narna chat             # REPL with slash commands
narna config set apiKey sk-...
narna config show
```

## Optional: social channels

Desktop agent works **without** Telegram/WhatsApp tokens. To connect social channels later:

```bash
narna gateway channels   # list channels
narna gateway run        # poll Telegram etc. (needs bot tokens)
```

## Options

| Path | Needs Python? | Command |
|------|---------------|---------|
| **Portable Windows zip** | No | Unzip → `NARNA-Desktop.exe` |
| **Portable macOS zip** | No | Unzip → `NARNA-Desktop` |
| **pip** | Yes 3.11+ | `pip install "narna[desktop]" && narna desktop` |
| **install.ps1 / install.sh** | Yes | See [`desktop/README.md`](../desktop/README.md) |

Build portable binaries (maintainers):

```powershell
.\scripts\build_desktop_exe.ps1   # Windows
bash scripts/build_desktop_mac.sh # macOS
```

Also: `narna desktop --tui` · `narna desktop --daemon --gateway` · https://narna.org/download

Install like Hermes:
```bash
curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/scripts/install.sh | bash
narna desktop
narna browser setup    # optional computer-use
narna daemon install   # optional always-on (macOS/Linux)
```
