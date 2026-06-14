# Parth Windows Installer

This folder contains everything needed to produce
`parth-agent-{version}-x64-setup.exe` — the production Windows installer for
Parth.

## Pieces

| File | Purpose |
|---|---|
| `parth.spec` | PyInstaller spec — bundles the Python runtime + `parth/` package + dependencies into `dist/parth/parth.exe` plus its data files. |
| `parth.iss` | Inno Setup script — wraps that `dist/parth/` folder into the installer wizard with PATH integration, shortcuts, upgrade detection, and an uninstaller. |
| `Output/` (generated) | Where ISCC drops the final `.exe`. Git-ignored. |

The repository-level pipeline is
[`.github/workflows/windows-installer.yml`](../.github/workflows/windows-installer.yml).
It runs on every push to `main`, every `v*` tag, and every PR to `main`.

## How users get and run Parth

```text
Download parth-agent-0.1.3-x64-setup.exe
  ↓
Double-click → wizard:
   • Choose install location (default C:\Program Files\Parth Agent)
   • [✓] Add to user PATH       (default on)
   • [ ] Create desktop shortcut (default off)
  ↓
Files installed → uninstaller registered in "Apps & Features"
  ↓
Open any terminal → `parth` → TUI launches
```

User config (API keys, chat history, memory, lessons, themes) is written to
`%APPDATA%\parth-agent\`. This directory is **never** touched by upgrades and
is only removed on uninstall if the user opts in.

## How upgrades work

The installer uses a fixed `AppId` GUID so Inno Setup recognizes "this user
already has Parth installed" and routes into the upgrade flow automatically:

1. Closes any running `parth.exe` (`CloseApplications=force`).
2. Replaces files in the existing install dir (`ignoreversion` flag in
   `[Files]`).
3. Preserves the user PATH entry and shortcuts.
4. **Preserves all user data in `%APPDATA%\parth-agent\`** — never wiped on
   upgrade.
5. Writes the new version to `HKCU\Software\Parth\Parth Agent\InstalledVersion`.

Downgrade is not supported — installing 0.1.2 over 0.1.4 will silently leave
0.1.4 in place unless the user uninstalls first.

### In-app updates

Running Parth (frozen build only) checks GitHub Releases on the configured
repo for a newer version. `parth/updater_installer.py` handles this. Trigger:

* Automatic on startup (background, non-blocking).
* Manual: type `/upgrade` in the TUI (also works as `/upgrade check` to peek
  without downloading).

The flow:

```
parth running v0.1.3
   ↓  /upgrade  (or background check)
fetch GitHub Releases /repos/{RELEASE_REPO}/releases/latest
   ↓  parse tag, compare to local VERSION
download parth-agent-0.1.4-x64-setup.exe → %TEMP%
   ↓
launch installer with /SILENT /CLOSEAPPLICATIONS
   ↓
parth.exe exits, installer replaces files, re-launches a fresh parth.exe.
```

`RELEASE_REPO` lives in `parth/constants/models.py` and can be overridden at
runtime via the `PARTH_RELEASE_REPO` env var. Set it to your GitHub
`owner/repo` before the first release.

## How uninstall works

`Start menu → Parth Agent → Uninstall Parth Agent` (or Add/Remove Programs)
runs the registered Inno Setup uninstaller, which:

1. Removes `C:\Program Files\Parth Agent\` (and subdirectories).
2. Cleans the PATH entry it added on install.
3. Removes the Start Menu and Desktop shortcuts.
4. Removes `HKCU\Software\Parth\Parth Agent` registry entries.
5. **Prompts** "Also remove your Parth Agent user data?" — defaults to **No**.
   Choosing Yes deletes `%APPDATA%\parth-agent\` (API keys, chat history,
   etc.). Choosing No keeps the data for a future reinstall.

## Building locally (Windows)

```powershell
# from repo root, in PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[build-windows]"

# 1. Bundle Python + deps + parth/ into dist/parth/
pyinstaller installer\parth.spec --noconfirm --clean

# 2. Read VERSION from source (no manual sync)
$v = python -c "from parth.constants.models import VERSION; print(VERSION)"

# 3. Compile installer with that version stamped in
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "/DAppVersion=$v" installer\parth.iss

# Output → installer\Output\parth-agent-$v-x64-setup.exe
```

You can also run the installer non-interactively for testing:

```powershell
# Full silent install (no UI), assume defaults
.\installer\Output\parth-agent-0.1.3-x64-setup.exe /VERYSILENT /NORESTART

# Same again to test the upgrade path
.\installer\Output\parth-agent-0.1.4-x64-setup.exe /VERYSILENT /NORESTART

# Silent uninstall
& "C:\Program Files\Parth Agent\unins000.exe" /VERYSILENT
```

## Release process

1. Bump `VERSION` in `parth/constants/models.py`.
2. Commit the bump.
3. Tag and push: `git tag v0.1.4 && git push origin v0.1.4`.
4. `.github/workflows/windows-installer.yml` runs on the tag:
   * Verifies tag matches source version (fails the build on drift).
   * Builds the PyInstaller bundle.
   * Compiles the installer with the version stamped in.
   * Creates a GitHub Release and attaches the `.exe` as a download.
5. Users on older versions running the frozen Parth will see the update on
   their next launch (or `/upgrade`).

## What to know about the AppId

`parth.iss` declares:

```ini
AppId={{6E2C9DAE-92B3-4F66-A50A-9B3F9E0F8E3D}
```

**Never change this GUID.** It is the upgrade identity Inno Setup uses to
recognize prior installs. If it changes, every existing installation becomes
"orphaned" — the new installer treats them as fresh installs, leaves the old
files behind, and registers a second entry in Add/Remove Programs.

If you fork this project under a different brand, generate a new GUID
(Tools → Generate GUID in Inno Setup IDE) and replace it once. Your fork's
users then have a clean upgrade path of their own.

## Things that are out of scope for now

* **Code signing.** Without an EV/OV certificate the installer triggers
  SmartScreen on first run. Users can click "More info → Run anyway". A
  signing step would slot in between `pyinstaller` and `iscc` in CI; cost is
  ~$200–$600/yr for the cert.
* **ARM64 / Windows-on-ARM build.** x64 only for v1. ARM64 would need a
  separate `windows-arm-runner` job and a different PyInstaller bootloader.
* **MSIX packaging.** The Inno Setup `.exe` is preferred today because it
  works without store publishing and supports per-user install with lowest
  privileges.
