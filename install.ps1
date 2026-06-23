# lrc-tools Windows installer (PowerShell 5.1+)
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/RicknotDev/lrc-tools"
$Spec = if ($args[0]) { $args[0] } else { "." }

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " lrc-tools installer for Windows" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check Python
$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Error: Python 3.12+ not found." -ForegroundColor Red
    Write-Host "  Download from https://python.org" -ForegroundColor Yellow
    exit 1
}

$pyver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python: $pyver" -ForegroundColor Green

# Check pip
$pipCheck = & python -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pip..." -ForegroundColor Yellow
    & python -c "import urllib.request; exec(urllib.request.urlopen('https://bootstrap.pypa.io/get-pip.py').read())"
}

Write-Host ""
Write-Host "Installing lrc-tools..." -ForegroundColor Yellow
& python -m pip install --user -e $Spec
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
try {
    $ver = & python -c "from lrc_tools import __version__; print(__version__)"
    Write-Host "  lrc-tools v$ver installed" -ForegroundColor Green
} catch {
    Write-Host "  Installation verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  lrc-tools       # Open the TUI"
Write-Host "  lrc-fetch       # Download lyrics"
Write-Host "  lrc-processor   # Process lyrics to word-level"
Write-Host "  lrc-vis         # Launch visualizer"
Write-Host ""
Write-Host "Quick start: lrc-tools" -ForegroundColor Green
