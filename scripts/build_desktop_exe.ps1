#Requires -Version 5.1
# Build portable NARNA-Desktop Windows folder (PyInstaller)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "pyproject.toml"))) {
  $Root = Split-Path -Parent $PSScriptRoot
}
Set-Location $Root

Write-Host "==> install build deps" -ForegroundColor Cyan
python -m pip install -q -e ".[desktop]" pyinstaller

Write-Host "==> pyinstaller" -ForegroundColor Cyan
Push-Location desktop
python -m PyInstaller --noconfirm --clean narna-desktop.spec
Pop-Location

$out = Join-Path $Root "dist\NARNA-Desktop"
if (-not (Test-Path (Join-Path $out "NARNA-Desktop.exe"))) {
  Write-Host "Build failed — exe missing" -ForegroundColor Red
  exit 1
}

Copy-Item (Join-Path $Root "desktop\README.md") (Join-Path $out "README.md") -Force
@"
NARNA Desktop (portable)

1. Double-click NARNA-Desktop.exe
2. Browser opens http://127.0.0.1:8765/
3. Paste OpenRouter / OpenAI / Ollama key (saved under %USERPROFILE%\.narna)

No Python install required.
"@ | Set-Content -Encoding utf8 (Join-Path $out "START-HERE.txt")

$zip = Join-Path $Root "dist\NARNA-Desktop-windows.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $out -DestinationPath $zip -Force
Write-Host "OK: $zip" -ForegroundColor Green
Write-Host "Run: $out\NARNA-Desktop.exe"
