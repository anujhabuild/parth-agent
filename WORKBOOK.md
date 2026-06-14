# Parth Agent — Windows Port Workbook

**Purpose:** single source of truth for resuming this project across sessions.
Read this file first when you come back to this repo.

> **Repo location:** `~/Desktop/parth-agent/`
> **No git history yet** — the user explicitly deferred `git init` until later.
> **Source:** cloned from `https://github.com/PrajsRamteke/harness-agent`,
> then renamed and ported.

---

## TL;DR — where we are right now

| Status | What |
|---|---|
| ✅ Done | Full rename: `harness-agent`/`jarvis` → `parth-agent`/`parth` |
| ✅ Done | Default theme: `red` → `ocean` (16 themes still selectable via `/theme`) |
| ✅ Done | Windows TUI port — `%APPDATA%` paths, Mac tools removed, cross-platform replacements |
| ✅ Done | Production installer scripts (`installer/parth.iss`, `installer/parth.spec`) |
| ✅ Done | In-app updater for installer-mode (`parth/updater_installer.py`) |
| ✅ Done | GitHub Actions workflow (`.github/workflows/windows-installer.yml`) |
| ✅ Done | Verified on Mac: `pip install -e .` and `parth` CLI both work |
| 🔄 In flight | **Portable Windows ZIP build** at `build_windows/portable/` — pip Windows-wheel download was running when session paused |
| ⏳ Pending | Push to GitHub → tag `v0.1.3` → CI builds real `.exe` installer |
| ⏳ Pending | Replace placeholder `your-org/parth-agent` with the real GitHub owner/repo |
| ⏳ Pending | Test the actual `.exe` on a Windows machine |

---

## Critical context — read before doing anything

### What this tool is
A terminal AI agent (Python TUI built on `textual` + `rich`). Fork of
`PrajsRamteke/harness-agent` (aka "Jarvis"). We renamed it to "Parth Agent"
(CLI: `parth`) and ported it to Windows.

### Scope decision (locked in)
- **TUI-only for v1.** No GUI-control tools (no AppleScript replacement
  for Windows). The macOS `read_ui`/`click_element`/`type_text`/`key_press`/
  `mac_control` family was deleted, not replaced with `pywinauto`/`uiautomation`.
- **Web UI deferred.** The `parth/web/` server still exists in the source
  tree but isn't part of the v1 Windows deliverable; we'll come back to it.
- **Two install modes coexist:** source/dev (`pip install -e .` from a git
  checkout) and frozen (PyInstaller bundle behind Inno Setup `.exe`).

### File layout you need to know
```
~/Desktop/parth-agent/
├── parth/                            # Main Python package (was: jarvis/)
│   ├── cli.py                        # CLI entry — `parth = parth.cli:main`
│   ├── updater.py                    # Source-mode updater (git pull + pip)
│   ├── updater_installer.py          # NEW — frozen-mode updater (GitHub Releases)
│   ├── constants/
│   │   ├── models.py                 # VERSION, RELEASE_REPO live here
│   │   ├── paths.py                  # CONFIG_DIR branches on platform
│   │   └── system_prompt.py          # Cross-platform identity, Mac GUI removed
│   ├── tools/
│   │   ├── clipboard.py              # NEW — pyperclip (cross-platform)
│   │   ├── system.py                 # NEW — open_url via webbrowser stdlib
│   │   ├── schemas_system.py         # NEW — 3 schemas (clipboard_get/set, open_url)
│   │   ├── ocr.py                    # Now pytesseract instead of Swift Vision
│   │   ├── image_input.py            # Now PIL.ImageGrab instead of AppleScript
│   │   └── (no more mac/ folder)
│   ├── commands/upgrade.py           # /upgrade — branches on sys.frozen
│   ├── tui/theme.py                  # 16 themes, default ocean
│   └── state.py                      # theme default = ocean
├── installer/
│   ├── parth.spec                    # PyInstaller spec (one-folder, console=true)
│   ├── parth.iss                     # Inno Setup script (upgrade-aware)
│   └── README.md                     # Operator's manual for the installer pipeline
├── .github/workflows/
│   └── windows-installer.yml         # Builds .exe on push/tag, attaches to Release
├── build_windows/                    # 🔄 IN PROGRESS — portable ZIP build folder
│   └── portable/                     # Python 3.11 embed + Lib/site-packages + parth/
├── .venv/                            # Python 3.13 venv (Mac dev install — works)
├── pyproject.toml                    # name=parth-agent, scripts.parth=parth.cli:main
├── requirements.txt                  # +pyperclip, Pillow, pytesseract
└── WORKBOOK.md                       # ← you are here
```

### How to resume the Mac dev install quickly
```bash
cd ~/Desktop/parth-agent
.venv/bin/parth --help            # CLI works
.venv/bin/parth                   # Launches the TUI
```

### Critical configuration values to know
- `parth/constants/models.py:VERSION` = `"0.1.3"`
- `parth/constants/models.py:RELEASE_REPO` = `"your-org/parth-agent"`
  **(MUST be replaced before the in-app updater works)**
- `installer/parth.iss:AppId` = `{{6E2C9DAE-92B3-4F66-A50A-9B3F9E0F8E3D}` — **never change** (it's the upgrade identity)
- Inno Setup `MyAppURL` in `parth.iss` also says `your-org/parth-agent` — update at same time
- Default theme: `ocean` (changed from `red`)
- All 16 themes still available via `/theme` in TUI

---

## Phase tracker

### ✅ Phase 0 — Rename harness/jarvis → parth

| # | Step | Status |
|---|---|---|
| 0.1 | Clone original repo to `/tmp/harness-agent` | ✅ |
| 0.2 | Copy to `~/Desktop/parth-agent` for working location | ✅ |
| 0.3 | Move `jarvis/` → `parth/`, `.harness/` → `.parth/`, delete `harness/` alias package | ✅ |
| 0.4 | Rename `JARVIS.md`, `harness_agent.py`, `test_harness_agent.py`, asset PNGs, `harness-agent-flow.html` | ✅ |
| 0.5 | Bulk string replace across `.py`/`.toml`/`.md`/`.json`/`.html`/`.js`/`.css`: `harness-jarvis`, `harness-agent`, `harness_agent`, `JARVIS`, `Jarvis`, `jarvis`, `HARNESS_*` env vars, `.harness/` paths, `Harness Agent` brand | ✅ |
| 0.6 | Fix duplicate `["parth*", "parth*"]` in `pyproject.toml` | ✅ |
| 0.7 | Change default theme from `red` → `ocean` in `parth/tui/theme.py` (both `_ACTIVE_THEME` and `set_theme()` init call) | ✅ |
| 0.8 | Fix `parth/state.py` and `parth/storage/settings.py` so theme actually defaults to ocean (had two extra hardcoded fallbacks) | ✅ |
| 0.9 | Smoke test: `import parth, parth.cli, parth.tui.theme` all load cleanly | ✅ |

**Audit result:** zero remaining `jarvis`/`Jarvis`/`JARVIS`/`harness`/`Harness`/`HARNESS` references in `.py`/`.toml`/`.md`/`.json`/`.html`/`.js`/`.css`.

---

### ✅ Phase 1 — Windows TUI port (functional code changes)

| # | Step | Status | File |
|---|---|---|---|
| 1.1 | Make `CONFIG_DIR` Windows-aware: `%APPDATA%\parth-agent` on Windows, `~/.config/parth-agent` elsewhere | ✅ | `parth/constants/paths.py` |
| 1.2 | Delete `parth/tools/mac/` package (8 files) and `parth/tools/schemas_mac.py` | ✅ | — |
| 1.3 | Create cross-platform `clipboard.py` (pyperclip), `system.py` (webbrowser.open), `schemas_system.py` (3 schemas) | ✅ | `parth/tools/` |
| 1.4 | Update `parth/tools/__init__.py`: remove mac imports, replace `MAC_TOOLS` with `SYSTEM_TOOLS`, register only cross-platform tool callables in `FUNC` | ✅ | `parth/tools/__init__.py` |
| 1.5 | Update `parth/tools/router.py`: `MAC_RE` → `SYSTEM_RE` (matches "clipboard"/"open url"); `"mac"` group → `"system"` | ✅ | `parth/tools/router.py` |
| 1.6 | Rewrite `parth/constants/system_prompt.py`: drop "macOS agent" identity, remove Mac GUI / GUI WORKFLOW / SPECK sections, list only cross-platform tools | ✅ | `parth/constants/system_prompt.py` |
| 1.7 | Replace AppleScript clipboard-PNG extraction with `PIL.ImageGrab.grabclipboard()` | ✅ | `parth/tools/image_input.py` |
| 1.8 | Replace Swift+Vision OCR with `pytesseract` + auto-detect Windows Tesseract install path | ✅ | `parth/tools/ocr.py` |
| 1.9 | Repoint broken imports: `parth/tui/mcp_modal.py:48`, `parth/commands/context.py:6` from `tools.mac.clipboard` → `tools.clipboard` | ✅ | — |
| 1.10 | Prune dead refs to removed tools in `parth/constants/icons.py`, `parth/repl/render.py`, `parth/repl/tool_activity.py` | ✅ | — |
| 1.11 | Add `pyperclip>=1.8`, `Pillow>=10.0`, `pytesseract>=0.3.10` to `pyproject.toml` and `requirements.txt`; add `[project.optional-dependencies] build-windows = ["pyinstaller>=6.0"]` | ✅ | `pyproject.toml`, `requirements.txt` |
| 1.12 | Verify no POSIX-only Python imports (`termios`, `fcntl`, `curses`, `pwd`, `grp`, `resource`) in `parth/` | ✅ | — |

**Verification on Mac:**
- `pip install -e .` succeeded (Python 3.13.13)
- `parth --help` runs
- `parth.tools.FUNC` has 34 registered tools across 9 groups (`core`, `context`, `system`, `internet`, `memory`, `lessons`, `skills`, `ocr`, `mcp`)
- `parth.tui.theme.active_theme()` returns `"ocean"`

---

### ✅ Phase 2 — Production installer pipeline

| # | Step | Status | File |
|---|---|---|---|
| 2.1 | Write PyInstaller spec: one-folder mode, console=true, bundles `textual`/`rich`/`mcp` data + `parth/web/static/**`, collect_submodules for hidden imports, excludes Foundation/AppKit/Quartz/Vision | ✅ | `installer/parth.spec` |
| 2.2 | Write Inno Setup script v1 (basic): AppId, install dir, PATH integration, shortcuts, uninstaller | ✅ | `installer/parth.iss` (later overhauled) |
| 2.3 | Overhaul `parth.iss` for production: `VersionInfoVersion`, `CloseApplications=force`, `RestartApplications=yes`, `MinVersion=10.0`, `UninstallDisplayName`, parameterized `/DAppVersion=`, registry version stamp at `HKCU\Software\Parth\Parth Agent\InstalledVersion`, PATH cleanup in `[Code]`, optional user-data wipe prompt at uninstall | ✅ | `installer/parth.iss` |
| 2.4 | Write GitHub Actions workflow: reads `VERSION` from `parth.constants.models` at build time, verifies tag matches source version, passes `/DAppVersion=` to ISCC, outputs `parth-agent-{version}-x64-setup.exe`, uploads as artifact + attaches to GitHub Release on `v*` tag | ✅ | `.github/workflows/windows-installer.yml` |
| 2.5 | Add in-app updater for frozen builds: hits GitHub Releases API on `RELEASE_REPO`, semver-tolerant version compare, downloads `.exe` to `%TEMP%`, launches with `/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NORESTART`, hard-exits via `os._exit(0)` | ✅ | `parth/updater_installer.py` |
| 2.6 | Branch `parth/updater.py`: top of `check_and_update()` delegates to installer updater when `sys.frozen`; source mode untouched | ✅ | `parth/updater.py` |
| 2.7 | Branch `/upgrade` command: same UX in both modes — `check` shows version diff, no-arg runs the upgrade | ✅ | `parth/commands/upgrade.py` |
| 2.8 | Add `RELEASE_REPO` and `RELEASE_INSTALLER_ASSET` constants in `parth/constants/models.py`; overridable via `PARTH_RELEASE_REPO` env var | ✅ | `parth/constants/models.py` |
| 2.9 | Write installer operator's README (build, release, upgrade, uninstall flows, AppId warning, out-of-scope notes) | ✅ | `installer/README.md` |

---

### 🔄 Phase 3 — Portable Windows ZIP build (interrupted)

**Why this phase exists:** PyInstaller cannot cross-compile from macOS to
Windows. The CI workflow does it properly on a Windows runner, but the user
wanted a deliverable they could copy to a Windows machine **without pushing
to GitHub first**. Solution: bundle the Windows-native Python embeddable
package + Windows wheels of all deps into a portable folder.

| # | Step | Status | Notes |
|---|---|---|---|
| 3.1 | Download `python-3.11.9-embed-amd64.zip` (~11 MB) from python.org | ✅ | `build_windows/python-embed.zip` |
| 3.2 | Extract to `build_windows/portable/` | ✅ | — |
| 3.3 | Enable site-packages by editing `python311._pth`: uncomment `import site`, add `Lib\site-packages` path | ✅ | — |
| 3.4 | Download Windows wheels for all `requirements.txt` deps via `pip install --platform=win_amd64 --python-version=3.11 --abi=cp311 --only-binary=:all: --target=Lib/site-packages` | 🔄 **WAS RUNNING IN BACKGROUND WHEN SESSION ENDED** | Check `build_windows/portable/Lib/site-packages/` |
| 3.5 | Copy `parth/` source code into `build_windows/portable/Lib/site-packages/parth/` | ⏳ | Pending step 3.4 |
| 3.6 | Write `parth.bat` launcher (just `python.exe -m parth`) | ✅ | `build_windows/portable/parth.bat` |
| 3.7 | Write `README.txt` for end-users of the portable ZIP | ✅ | `build_windows/portable/README.txt` |
| 3.8 | ZIP the `portable/` folder → `parth-agent-0.1.3-windows-x64-portable.zip` | ⏳ | Pending 3.5 |
| 3.9 | Place final ZIP where the user can find it | ⏳ | Suggested: `~/Desktop/parth-agent/dist-portable/` |

**Resume command for 3.4 (run from `~/Desktop/parth-agent`):**

```bash
cd ~/Desktop/parth-agent/build_windows/portable && \
pip3 install \
  --platform=win_amd64 \
  --python-version=3.11 \
  --implementation=cp \
  --abi=cp311 \
  --only-binary=:all: \
  --target=Lib/site-packages \
  --upgrade \
  -r ../../requirements.txt
```

**Then 3.5–3.9 in one shot:**

```bash
cd ~/Desktop/parth-agent && \
cp -R parth build_windows/portable/Lib/site-packages/ && \
mkdir -p dist-portable && \
cd build_windows && \
zip -rq ../dist-portable/parth-agent-0.1.3-windows-x64-portable.zip portable/ && \
ls -lh ../dist-portable/
```

**Known risks for 3.4:**
- Some transitive deps may not have `win_amd64` wheels for cp311. Likely culprits:
  `cryptography` (has wheels), `pydantic-core` (has wheels), `httpcore` (has wheels),
  `Pillow` (has wheels). Should be fine, but if a wheel is missing, the install
  will fail with a clear "No matching distribution" error. Fix: drop `--only-binary=:all:`
  for that one package OR install a slightly older version that has a wheel.
- Disk size of the resulting `portable/` folder: ~150–250 MB before ZIP, ~80–120 MB
  after.

---

### ⏳ Phase 4 — Real `.exe` installer (deferred until you push to GitHub)

This is the path to a true Windows MSI/EXE installer with PATH integration,
Start Menu shortcuts, Add/Remove Programs entry, and auto-update.

| # | Step | Status | Notes |
|---|---|---|---|
| 4.1 | Replace `your-org/parth-agent` placeholder in `parth/constants/models.py:RELEASE_REPO` and `installer/parth.iss:MyAppURL` with the real GitHub `owner/repo` | ⏳ | Search for `your-org/parth-agent` and replace |
| 4.2 | `git init` + first commit | ⏳ | User explicitly deferred this |
| 4.3 | Create the GitHub repo (`gh repo create ...`) and push | ⏳ | `gh` CLI is logged in as `anujhabuild` |
| 4.4 | Tag `v0.1.3` and push the tag (`git tag v0.1.3 && git push origin v0.1.3`) | ⏳ | Workflow auto-verifies tag matches source `VERSION` |
| 4.5 | CI builds `parth-agent-0.1.3-x64-setup.exe` on `windows-latest` runner | ⏳ | Takes ~8–10 min |
| 4.6 | Download the installer from the GitHub Release page (or workflow artifacts) | ⏳ | — |
| 4.7 | Run installer on a Windows machine — verify Add/Remove Programs entry, PATH integration, `parth` command in any terminal | ⏳ | — |
| 4.8 | Bump `VERSION` to `0.1.4`, tag `v0.1.4`, push — verify the in-app `/upgrade` flow pulls the new installer and replaces the old one | ⏳ | — |
| 4.9 | Run silent install/uninstall for QA (`/VERYSILENT`, `/NORESTART`, `unins000.exe /VERYSILENT`) | ⏳ | Commands in `installer/README.md` |

---

### ⏳ Phase 5 — Tech debt / polish (low priority, non-blocking)

| # | Item | Why it's deferred | File |
|---|---|---|---|
| 5.1 | `tests/test_tool_repair.py` references removed tools (`click_element`, `click_menu`, `check_permissions`) | Tests will fail in CI until pruned; doesn't block runtime | `tests/test_tool_repair.py` |
| 5.2 | `SPECK_MAX_CHARS = 8000` is unused after removing speck tool | Harmless dead code | `parth/constants/models.py` |
| 5.3 | `index.html` marketing page still describes Mac GUI control features | Cosmetic; never served to users by default | `index.html` |
| 5.4 | `scripts/install` and `scripts/install-global` are bash-only macOS installers | Out of scope — Windows uses the `.exe` installer | `scripts/` |
| 5.5 | `README.md` install commands may still reference legacy paths | Cosmetic; new installer flow documented separately | `README.md` |
| 5.6 | `parth/web/` web UI server not yet adapted for Windows | Deferred per scope decision (TUI-only v1) | `parth/web/` |
| 5.7 | UI help text in modals still shows `~/.config/parth-agent/` even on Windows | Cosmetic — the actual file IO uses the correct platform path; only the displayed string is wrong | `parth/tui/mcp_modal.py`, `parth/tui/key_modal.py`, `parth/tui/shortcuts_modal.py` |

---

### ⏳ Phase 6 — Future scope (someday, not v1)

These were explicitly *deferred* from the initial scope because the user
wanted "TUI-only" for the first Windows release. The Mac code that did these
has been deleted, not abstracted; rebuilding them on Windows would mean adding
a new platform layer.

- **Windows GUI control parity** — `read_ui`, `click_element`, `type_text`,
  `key_press` etc. via `pywinauto` or `uiautomation` (Microsoft UIA framework)
- **Windows system control** — battery, wifi, sleep, dark mode, volume,
  brightness via WMI (`pywin32` / PowerShell cmdlets)
- **Cross-platform `notify`** — `winotify` / `win10toast` on Win, `osascript` on Mac
- **Cross-platform `speck` (TTS)** — `pyttsx3` (works on all platforms)
- **Web UI Windows port** — adapt `parth/web/` server
- **Code signing** for Windows installer (avoid SmartScreen) — requires
  EV/OV cert (~$200–600/yr)
- **ARM64 Windows build** — separate `windows-arm-runner` job
- **MSIX packaging** — for Microsoft Store / enterprise deployment

---

## Things to remember (decision log)

| Decision | Why |
|---|---|
| Renamed everything to `parth`/`Parth`/`PARTH` (incl. `harness` brand) | Personal fork; user wanted a clean rebrand |
| Kept `OPENCODE_ZEN_BASE_URL` unchanged | The free OAuth tier (was "Harness Agent", now "Parth Agent") talks to the same hosted service — only the user-facing label changed |
| New `AppId` GUID hardcoded in Inno Setup | Stable upgrade identity across all releases — **never change it** |
| Default theme: ocean | User wanted away from red; ocean = deep sapphire, calm, professional |
| Config dir: `%APPDATA%\parth-agent` on Win, `~/.config/parth-agent` elsewhere | Windows roaming profile convention |
| Home dir: `~/.parth` on all platforms | Mirrors `~/.ssh` / `~/.aws` / `~/.claude` — Windows handles dotted dirs in home fine |
| Two install modes (source / frozen) coexist | Don't force one over the other; `sys.frozen` detection branches at runtime |
| Portable ZIP is *not* the primary deliverable | It's the macOS-buildable fallback. The proper `.exe` ships via GitHub Actions on a Windows runner. |
| User data preserved on upgrade and (by default) on uninstall | `%APPDATA%\parth-agent\` is never touched on upgrade. Uninstall prompts "Also remove user data?" — defaults to No. |
| `your-org/parth-agent` is a **placeholder** | Replace before the in-app updater can work |

---

## When you come back

### If you want to continue the portable ZIP build (fastest path to a Windows deliverable):
1. `cd ~/Desktop/parth-agent`
2. Run the **Resume command for 3.4** in the Phase 3 section above
3. Then the **3.5–3.9 in one shot** block
4. ZIP lands at `~/Desktop/parth-agent/dist-portable/parth-agent-0.1.3-windows-x64-portable.zip`
5. Copy to Windows, extract, double-click `parth.bat`

### If you want the production `.exe` installer:
1. Replace `your-org/parth-agent` with the real GitHub repo path in two places:
   - `parth/constants/models.py:RELEASE_REPO`
   - `installer/parth.iss:MyAppURL`
2. `cd ~/Desktop/parth-agent && git init && git add . && git commit -m "Initial Parth Agent fork"`
3. `gh repo create <owner>/parth-agent --private --source=. --push` (uses authenticated `gh` CLI)
4. `git tag v0.1.3 && git push origin v0.1.3`
5. Wait ~10 min for the workflow to finish
6. `gh run download` or grab the `.exe` from the Releases page
7. Copy to Windows, install

### If you want to test locally on Mac (sanity check the agent works):
```bash
cd ~/Desktop/parth-agent
.venv/bin/parth
```
Then `/help`, `/theme`, `/upgrade check` inside the TUI.

### If you want to keep porting (Phase 6):
- Start with the Windows GUI control layer (`pywinauto`)
- Look at the historical `parth/tools/mac/` package in git history of the
  original repo for the API surface to mirror
- Build a `parth/tools/system/{darwin,windows,linux}/` platform-dispatch
  layer rather than dropping new code straight into `parth/tools/`

---

## Quick references

| What | Where |
|---|---|
| Run the Mac dev install | `~/Desktop/parth-agent/.venv/bin/parth` |
| Source files I touched most | `parth/constants/`, `parth/tools/`, `parth/tui/theme.py`, `parth/state.py`, `parth/updater*.py`, `installer/` |
| GitHub CLI auth | Logged in as `anujhabuild` (token has `repo`, `workflow` scopes) |
| Python on this Mac | `python3.13` at `/opt/homebrew/opt/python@3.13/bin/python3.13` |
| Installed dep versions (Mac venv) | `Pillow 12.2.0`, `anthropic 0.106.0`, `textual 8.2.7`, `mcp 1.27.2`, `pyperclip 1.11.0`, `pytesseract 0.3.13` |
| Tesseract for OCR | Not installed on this Mac. OCR gracefully degrades with a clear error. Install via `brew install tesseract` if needed. |
| Original upstream | `https://github.com/PrajsRamteke/harness-agent` |
| Inno Setup `AppId` GUID | `{{6E2C9DAE-92B3-4F66-A50A-9B3F9E0F8E3D}` (never change) |
