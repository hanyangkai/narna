#Requires -Version 5.1
# NARNA Desktop installer for Windows (pip path — needs Python 3.11+)
# For no-Python install: download NARNA-Desktop-windows.zip from GitHub Releases.
$ErrorActionPreference = "Stop"
Write-Host "==> NARNA Desktop install (pip)" -ForegroundColor Cyan
Write-Host "    No Python? Get portable zip: https://github.com/hanyangkai/narna/releases" -ForegroundColor DarkGray

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
  Write-Host "Python 3.11+ required. Install from https://www.python.org/downloads/ (check Add to PATH)." -ForegroundColor Red
  exit 1
}

& $py.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if ($LASTEXITCODE -ne 0) {
  Write-Host "Need Python 3.11+. Found older version." -ForegroundColor Red
  exit 1
}

Write-Host "==> pip install narna[desktop]"
& $py.Source -m pip install --upgrade "narna[desktop]"
if ($LASTEXITCODE -ne 0) {
  Write-Host "PyPI install failed — trying editable from repo if present..." -ForegroundColor Yellow
  $root = Split-Path -Parent $PSScriptRoot
  if (Test-Path (Join-Path $root "pyproject.toml")) {
    Push-Location $root
    & $py.Source -m pip install -e ".[desktop]"
    Pop-Location
  } else {
    exit 1
  }
}

$launcherDir = Join-Path $env:USERPROFILE "NARNA"
New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null
$bat = Join-Path $launcherDir "NARNA-Desktop.bat"
@"
@echo off
title NARNA Desktop
python -m uap.desktop_app %*
"@ | Set-Content -Encoding ascii $bat

$desktopLink = Join-Path ([Environment]::GetFolderPath("Desktop")) "NARNA Desktop.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($desktopLink)
$sc.TargetPath = $bat
$sc.WorkingDirectory = $launcherDir
$sc.Description = "NARNA Desktop — local AI agent"
$sc.Save()

Write-Host ""
Write-Host "Installed. Double-click 'NARNA Desktop' on your Desktop," -ForegroundColor Green
Write-Host "or run:  narna desktop" -ForegroundColor Green
Write-Host "Data folder: $env:USERPROFILE\.narna"
