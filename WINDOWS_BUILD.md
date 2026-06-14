# Parth Agent — Windows Build & Install Guide

This document is the **complete, manual recipe** to build the Parth Windows
installer on a fresh Windows machine and install it. End-to-end the happy
path is ~3 minutes for the first build and ~30 seconds for incremental
rebuilds (`-SkipVenv`).

> **Audience.** You're on a Windows PC, you have a copy of the
> `parth-agent` repo, and you want a runnable `parth.exe`.

---

## TL;DR — fastest path

```powershell
# 1. open PowerShell in the parth-agent repo root
cd C:\path\to\parth-agent

# 2. one-shot build (creates venv, installs deps, runs PyInstaller, runs Inno Setup)
.\build.ps1

# 3. install the .exe it produced
.\installer\Output\parth-agent-0.1.3-x64-setup.exe

# 4. open a NEW terminal (PATH was just updated), then:
parth
```

That's it. User data — API keys, sessions, themes, memory, lessons — lives
under `%APPDATA%\parth-agent\` and is preserved across upgrades and
uninstalls (you'll be asked before any wipe).

---

## Prerequisites

Install once on the build machine. The runtime user does **not** need any
of these — the installer ships its own Python.

| Tool | Why | Where |
|------|-----|-------|
| **Python 3.11** (3.10+ also works) | Builds the bundle; not used at runtime by the installed app | https://www.python.org/downloads/windows/ (check "Add to PATH" during install) |
| **Inno Setup 6** | Wraps the PyInstaller folder into a single `.exe` installer | https://jrsoftware.org/isinfo.php — defaults to `C:\Program Files (x86)\Inno Setup 6\` |
| **Git** *(optional)* | If you want to clone or update via the in-app `/upgrade` later | https://git-scm.com/download/win |
| **Tesseract OCR** *(optional)* | Needed only if users will call `read_image_text` / `read_images_text` at runtime | https://github.com/UB-Mannheim/tesseract/wiki — installs to `C:\Program Files\Tesseract-OCR\` by default, auto-detected |

PowerShell must be allowed to run unsigned local scripts. Once per machine:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Build steps (what `build.ps1` does)

If you'd rather run the steps by hand:

```powershell
# 1. venv + deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip wheel
pip install -e ".[build-windows]"

# 2. read the source-of-truth version
$v = python -c "from parth.constants.models import VERSION; print(VERSION)"

# 3. bundle: dist\parth\parth.exe + its supporting files
pyinstaller installer\parth.spec --noconfirm --clean

# 4. smoke-test the frozen binary BEFORE wrapping it
.\dist\parth\parth.exe --help

# 5. compile the installer
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "/DAppVersion=$v" installer\parth.iss

# 6. output
ls .\installer\Output\
# → parth-agent-{$v}-x64-setup.exe
```

### `build.ps1` flags

| Flag | Effect |
|------|--------|
| *(none)* | Full clean build. ~3 minutes first run. |
| `-SkipVenv` | Reuse the existing `.venv` and skip `pip install`. ~30 s after edits to spec/iss. |
| `-VerySilentTest` | After a successful build, run the installer with `/VERYSILENT /NORESTART` to install Parth on this machine immediately. |

---

## What ends up where

| Path | Purpose | Lifetime |
|------|---------|----------|
| `C:\Program Files\Parth Agent\` | Installed binaries (default per-user install location, override during setup) | Removed by uninstall |
| `%APPDATA%\parth-agent\` | API keys, chat history, sessions DB, memory, lessons, themes, MCP config | **Preserved** across upgrades; uninstall **asks first** before wiping |
| `%USERPROFILE%\.parth\` | User-authored agents, skills, custom commands | Preserved across upgrades and uninstalls (lives outside `Program Files`) |
| `HKCU\Software\Parth\Parth Agent\` | Version stamp + install dir registry entry | Removed on uninstall |
| `%PATH%` (user) | The install dir is appended so `parth` works in any terminal | Cleaned on uninstall |

---

## Install / Upgrade / Uninstall flow

### Install
Double-click `parth-agent-<ver>-x64-setup.exe`. Choose install dir (default
`C:\Program Files\Parth Agent`), tick / untick "Add to PATH" and "Desktop
shortcut", click Install.

> **SmartScreen warning** on first run — the installer isn't code-signed
> (yet). Click **More info → Run anyway**. Once we ship an EV cert, this
> goes away.

### Upgrade
Install a newer `.exe` over the older one. The same installer:
1. Closes a running `parth.exe` cleanly (`CloseApplications=force`).
2. Replaces files in-place (`ignoreversion` flag).
3. **Never** touches `%APPDATA%\parth-agent\` — your keys and history
   survive.
4. Bumps `HKCU\Software\Parth\Parth Agent\InstalledVersion`.

### Uninstall
`Start Menu → Parth Agent → Uninstall Parth Agent` (or Add/Remove
Programs).
* Removes the binaries.
* Cleans the PATH entry it added.
* Removes Start-Menu and Desktop shortcuts.
* Removes the `HKCU` registry entries.
* **Prompts** "Also remove your Parth Agent user data?" — defaults to
  **No** so a future reinstall picks up the same config. Choose Yes to
  wipe `%APPDATA%\parth-agent\` too.

`.parth/` in your home directory is **never** touched by uninstall.

---

## First-run setup

```powershell
parth
```

On the first launch, Parth asks how you want to sign in. Three options:

| Mode | What you need | Notes |
|------|---------------|-------|
| **Parth Agent (free)** | nothing | Default. OpenCode Zen free models — no API key, no setup. Hits `parth_agent` provider in `parth/constants/providers.py`. |
| **API key** | `sk-ant-…` (Anthropic), `sk-or-…` (OpenRouter), or an OpenCode key | Paste once; stored encrypted-at-rest in `%APPDATA%\parth-agent\`. |
| **OAuth** | A claude.ai or ChatGPT login | PKCE flow, no client secret — works on the same machine you're signed into. |

Common slash commands after sign-in:

```
/help           list every command
/model          switch model (live picker)
/agent          activate/deactivate a coding agent
/skill          browse available skills
/command        manage custom commands (forward-ported from upstream)
/plan on        read-only plan mode (forward-ported from upstream)
/memory         your persistent profile
/mcp            connect MCP servers
/upgrade        check for a newer parth.exe (uses RELEASE_REPO setting)
/exit
```

---

## Troubleshooting

### `parth` not found after install
The installer appends to your user PATH only on the **install** step, and
already-open terminals don't see PATH changes. Open a new PowerShell window.

If still missing:
```powershell
echo $env:PATH
# Confirm "C:\Program Files\Parth Agent" is in there.
# If not, log out + back in (or reboot) — PATH refresh is per-session.
```

### "Python 3.10+ required" from `build.ps1`
You've got Python 3.9 or older on PATH. Install 3.11 from python.org and
make sure it's first in PATH.

### `ISCC.exe not found`
You didn't install Inno Setup, or it's at a non-default path. Either
install at the default location or edit the path in `build.ps1` step 3.

### `dist\parth\parth.exe --help` fails right after PyInstaller
This means a hidden import didn't get bundled. The error message names the
missing module. Add it to `installer/parth.spec` under `hiddenimports`
(near the bottom of the existing list) and rerun `.\build.ps1`.

### SmartScreen blocks the installer
Click **More info → Run anyway**. Will go away once we add an EV
code-signing cert (CI step is documented in `installer/README.md`).

### Tesseract not detected → OCR tools say "tesseract is not installed"
Install Tesseract from the URL in the Prereqs table. Parth auto-detects
`C:\Program Files\Tesseract-OCR\tesseract.exe`. If you installed elsewhere,
add it to PATH.

### MSI instead of EXE?
Inno Setup produces a `.exe` installer; this is the recommended Windows
format for unsigned apps and supports per-user install with lowest
privileges. If you specifically need MSI, swap Inno Setup for WiX — out of
scope for phase 1.

---

## What's removed vs upstream `harness-agent`

This Windows build does **not** include the macOS UI-control tools
(AppleScript / JXA / app launch / clicks / `type_text` / `key_press`).
Those tools don't apply on Windows. The dispatcher, plan-mode allowlist,
and tool registry no longer reference them. PyInstaller excludes the
PyObjC modules (`Foundation`, `AppKit`, `Quartz`, `Vision`) so the bundle
stays slim.

Everything else from upstream — custom commands, plan mode, intro
animation, JSON-repair for streamed tool calls, the newest free models —
**is** included.

---

## Before publishing a release

Items to confirm before tagging `v0.1.x` and uploading to GitHub Releases:

- [ ] Bump `parth/constants/models.py::VERSION` (single source of truth;
      CI fails the build if the git tag doesn't match).
- [ ] Replace the placeholder `MyAppURL` in `installer/parth.iss` (line
      `#define MyAppURL`) with the real public repo URL if it changes.
- [ ] Confirm `RELEASE_REPO` in `parth/constants/models.py` matches the
      GitHub repo where the `.exe` lives. Users can also override with the
      `PARTH_RELEASE_REPO` env var.
- [ ] Tag and push: `git tag v0.1.x && git push origin v0.1.x`. CI builds
      the same installer on a Windows runner and attaches it to the
      Release automatically.
- [ ] **Optional (recommended for v1):** code-signing cert (~$200–600/yr).
      The signing step slots between `pyinstaller` and `iscc` in CI.

---

## Files of interest

| File | What it does |
|------|--------------|
| `build.ps1` | One-shot end-to-end Windows build (this guide's TL;DR). |
| `installer/parth.spec` | PyInstaller spec — controls the bundle's hidden imports, data files, icon, excludes. |
| `installer/parth.iss` | Inno Setup script — controls install dir, PATH integration, upgrade flow, uninstall prompts. |
| `installer/README.md` | Deeper installer engineering notes (AppId, signing slot, ARM64 plans). |
| `.github/workflows/windows-installer.yml` | CI build of the same installer on every push, PR, and tag. |
| `assets/parth.ico` | Multi-resolution Windows icon (16/24/32/48/64/128/256). |
| `parth/constants/paths.py` | Resolves config dir to `%APPDATA%\parth-agent\` on Windows. |
| `parth/updater_installer.py` | In-app `/upgrade` flow — fetches GitHub Releases, runs the new installer with `/SILENT /CLOSEAPPLICATIONS`. |
| `build_windows/portable/` | **Legacy** zero-install Python embed bundle. Not part of the installer path; safe to ignore. |
