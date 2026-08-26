# NARNA Desktop

Run the decision-quality agent entirely on your PC.

## Install

See [`desktop/README.md`](../desktop/README.md) or https://narna.org/download

```bash
pip install "narna[desktop]"
narna desktop
```

Windows one-liner:

```powershell
irm https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.ps1 | iex
```

## What you get

- Local Ask UI at `http://127.0.0.1:8765/`
- BYOK OpenRouter / OpenAI / Ollama (`~/.narna/config.json`)
- Full tool loop + ADQA + Decision Trace on disk
- Optional `narna desktop --tui`

No cloud account required for the runtime.
