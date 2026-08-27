# NARNA Desktop

Run the decision-quality agent entirely on your PC.

## Options

| Path | Needs Python? | Command |
|------|---------------|---------|
| **Portable Windows zip** | No | Unzip → `NARNA-Desktop.exe` ([Releases](https://github.com/hanyangkai/narna/releases)) |
| **pip** | Yes 3.11+ | `pip install "narna[desktop]" && narna desktop` |
| **install.ps1 / install.sh** | Yes | See [`desktop/README.md`](../desktop/README.md) |

Build portable exe (maintainers):

```powershell
.\scripts\build_desktop_exe.ps1
```

Browser opens at `http://127.0.0.1:8765/`. BYOK keys → `~/.narna/config.json`.

Also: `narna desktop --tui` · https://narna.org/download
