# NARNA Desktop — run on your PC

Decision-quality AI agent on Windows / macOS / Linux. **BYOK** — your keys stay on disk (`~/.narna`).

## Quick install

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.ps1 | iex
```

Or from a clone:

```powershell
.\desktop\install.ps1
```

Then double-click **NARNA Desktop** on the Desktop, or run:

```powershell
narna desktop
```

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.sh | bash
narna desktop
```

### Manual (any OS)

```bash
pip install "narna[desktop]"
narna desktop
```

Browser opens at `http://127.0.0.1:8765/` — paste OpenRouter / OpenAI / Ollama key, Ask.

## Modes

| Command | What |
|---------|------|
| `narna desktop` | Local Ask UI in your browser |
| `narna desktop --tui` | Fullscreen terminal UI (`pip install 'narna[tui]'`) |
| `narna chat` | Simple REPL |
| `narna gateway run` | Telegram / Discord / Slack poll |

## Data location

- Config + memory: `~/.narna` (override with `NARNA_HOME` or `--workspace`)
- API key stored only in `~/.narna/config.json`

## Offline demo

Without a key, provider falls back to **mock** — ADQA still scores answers.
