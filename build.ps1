<#
.SYNOPSIS
  Build the Parth Agent Windows installer end-to-end.

.DESCRIPTION
  Produces installer/Output/parth-agent-<version>-x64-setup.exe in three steps:

    1. Create / activate a venv and install build dependencies.
    2. Run PyInstaller to bundle Python + parth/ + deps into dist/parth/.
    3. Compile the Inno Setup script with the version stamped in.

  Run this from the repo root in a fresh PowerShell prompt.

.PARAMETER SkipVenv
  Reuse the existing .venv without re-installing dependencies. Useful when
  iterating on the spec or the .iss script after a clean first build.

.PARAMETER VerySilentTest
  After the build succeeds, run the installer with /VERYSILENT to install
  Parth on this machine (handy for quick local verification on the Windows
  box). Skips this step on every other host.

.EXAMPLE
  .\build.ps1

.EXAMPLE
  .\build.ps1 -SkipVenv

.NOTES
  Prereqs:
    * Python 3.11 (Microsoft Store / python.org installer is fine).
    * Inno Setup 6 installed at C:\Program Files (x86)\Inno Setup 6\ISCC.exe.
    * Git (to look up the working version, optional).

  This script never modifies %APPDATA%\parth-agent\ — user data is preserved.
#>

[CmdletBinding()]
param(
    [switch]$SkipVenv,
    [switch]$VerySilentTest
)

$ErrorActionPreference = "Stop"

function Write-Step($Number, $Title) {
    Write-Host ""
    Write-Host "==[ $Number ]== $Title" -ForegroundColor Cyan
}

function Fail($Message) {
    Write-Host ""
    Write-Host "BUILD FAILED: $Message" -ForegroundColor Red
    exit 1
}

# ── Sanity ───────────────────────────────────────────────────────────────
$root = $PSScriptRoot
if (-not (Test-Path (Join-Path $root "pyproject.toml"))) {
    Fail "Run this script from the parth-agent repo root."
}
Set-Location $root

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Fail "python is not on PATH. Install Python 3.11 from python.org first." }
$pyver = (& python --version) 2>&1
if ($pyver -notmatch "^Python 3\.(1[0-9]|[2-9][0-9])") {
    Fail "Python 3.10+ required (found '$pyver')."
}
Write-Host "Using: $pyver" -ForegroundColor DarkGray

# ── 1. venv + dependencies ───────────────────────────────────────────────
Write-Step 1 "Set up venv and install dependencies"
$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not $SkipVenv) {
    if (-not (Test-Path $venvDir)) {
        & python -m venv $venvDir
        if ($LASTEXITCODE -ne 0) { Fail "venv creation failed." }
    }
    & $venvPython -m pip install --upgrade pip wheel | Out-Host
    if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed." }
    # `.[build-windows]` pulls PyInstaller in alongside the runtime deps.
    & $venvPython -m pip install -e ".[build-windows]" | Out-Host
    if ($LASTEXITCODE -ne 0) { Fail "pip install -e .[build-windows] failed." }
} else {
    if (-not (Test-Path $venvPython)) { Fail "-SkipVenv requested but .venv\Scripts\python.exe is missing." }
    Write-Host "Reusing existing .venv (-SkipVenv)." -ForegroundColor DarkGray
}

# Smoke-check the package imports — fails fast if a forward-port left a bad import.
$smoke = & $venvPython -c "import parth, parth.cli, parth.tui.app, parth.tools, parth.tools.plan, parth.tui.intro_anim, parth.utils.json_repair, parth.storage.commands, parth.tui.command_modal, parth.updater_installer; print('imports ok')"
if ($LASTEXITCODE -ne 0) {
    Write-Host $smoke -ForegroundColor Red
    Fail "Package imports failed — fix the error above before building."
}
Write-Host "Smoke imports: $smoke" -ForegroundColor Green

# Resolve VERSION from source — single source of truth, matches CI.
$version = & $venvPython -c "from parth.constants.models import VERSION; print(VERSION)"
$version = $version.Trim()
if (-not ($version -match '^\d+\.\d+\.\d+')) {
    Fail "VERSION '$version' is not a dotted x.y.z string (parth/constants/models.py)."
}
Write-Host "Source VERSION = $version" -ForegroundColor Green

# ── 2. PyInstaller bundle ────────────────────────────────────────────────
Write-Step 2 "PyInstaller — bundle Python + parth/ + deps into dist/parth/"
# --clean wipes the build cache so a stale hidden-import scan can't carry
# yesterday's mistake into today's installer.
& $venvPython -m PyInstaller "installer\parth.spec" --noconfirm --clean | Out-Host
if ($LASTEXITCODE -ne 0) { Fail "PyInstaller failed." }

$parthExe = Join-Path $root "dist\parth\parth.exe"
if (-not (Test-Path $parthExe)) {
    Fail "PyInstaller finished but $parthExe is missing. Inspect dist\parth\."
}

# Sanity-launch the frozen binary with --help — catches missing hidden imports
# and broken data files before Inno Setup wraps a doomed bundle.
Write-Host "Smoke-launching dist\parth\parth.exe --help ..." -ForegroundColor DarkGray
$helpOut = & $parthExe --help 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host $helpOut -ForegroundColor Red
    Fail "dist\parth\parth.exe --help failed (exit $LASTEXITCODE). The frozen binary cannot start."
}
Write-Host "Frozen binary launches OK." -ForegroundColor Green

# ── 3. Inno Setup installer ──────────────────────────────────────────────
Write-Step 3 "Inno Setup — wrap dist\parth\ into a single .exe installer"
$iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    Fail "Inno Setup 6 not found at $iscc. Install it from https://jrsoftware.org/isinfo.php"
}

& $iscc "/DAppVersion=$version" "installer\parth.iss" | Out-Host
if ($LASTEXITCODE -ne 0) { Fail "ISCC compile failed." }

$installer = Join-Path $root "installer\Output\parth-agent-$version-x64-setup.exe"
if (-not (Test-Path $installer)) {
    Fail "Inno Setup finished but $installer is missing. Inspect installer\Output\."
}

$sizeMb = "{0:N1}" -f ((Get-Item $installer).Length / 1MB)
Write-Host ""
Write-Host "==[ done ]== built parth-agent-$version-x64-setup.exe  ($sizeMb MB)" -ForegroundColor Green
Write-Host "      path: $installer"
Write-Host ""
Write-Host "  Install: double-click the .exe, or run silent:"
Write-Host "    `"$installer`" /VERYSILENT /NORESTART"
Write-Host ""

if ($VerySilentTest) {
    Write-Step 4 "Installing the freshly-built .exe (-VerySilentTest)"
    & $installer /VERYSILENT /NORESTART
    if ($LASTEXITCODE -ne 0) { Fail "Silent install exited $LASTEXITCODE." }
    Write-Host "Installed. Open a NEW terminal and type 'parth' to launch." -ForegroundColor Green
}
