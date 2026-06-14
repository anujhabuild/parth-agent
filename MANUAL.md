# Parth Agent — Manual

Phase 1 ship summary, Windows-build recipe, and how to run the project
straight from source for testing & debugging.

---

## Phase 1 — Done

**Files created:** `build.ps1`, `WINDOWS_BUILD.md`, `assets/parth.ico`,
plus 6 forward-ported feature modules:
- `parth/utils/json_repair.py`
- `parth/tui/intro_anim.py`
- `parth/tools/plan.py`
- `parth/storage/commands.py`
- `parth/commands/command.py`
- `parth/tui/command_modal.py`

**Files modified** (wiring + state + branding):
- `parth/state.py` — `plan_mode`, `global_commands` + reload/save hooks
- `parth/constants/paths.py` + `parth/constants/__init__.py` —
  `PARTH_COMMANDS_DIR` / `PROJECT_COMMANDS_DIRNAME`
- `parth/constants/models.py` — `RELEASE_REPO` placeholder cleared
- `parth/constants/providers.py` — dropped no-longer-free models, added
  `nemotron-3-ultra-free`, `north-mini-code-free`
- `parth/auth/codex_client.py`, `parth/auth/opencode_client.py` — wired
  `repair_json_arguments`
- `parth/tools/__init__.py`, `parth/tools/router.py` — plan-mode gate
- `parth/repl/system.py`, `parth/repl/render.py`, `parth/repl/banners.py`
  — plan-mode block, guard, `skip_art` arg
- `parth/commands/control.py`, `parth/commands/dispatch.py` — `/plan` +
  `/command` dispatch
- `parth/tui/app.py`, `parth/tui/app_commands.py` — intro animation,
  plan-mode status segment, `_open_command_manager`
- `installer/parth.spec` — `.ico` icon, added `parth` + `httpx` to hidden
  imports
- `installer/parth.iss` — `.ico` icon, real `MyAppURL`
- `README.md` — Windows-build banner

**Verified:** full `parth/` tree compiles cleanly via `py_compile`.
Runtime import smoke-test runs as the first step inside `build.ps1` on
the Windows side.

---

## What you do now on your Windows PC

```powershell
# 1. copy the parth-agent folder to the Windows machine (USB / Git / network share)
# 2. install prereqs once: Python 3.11 (from python.org, "Add to PATH") and Inno Setup 6
# 3. open PowerShell in the parth-agent folder, then:
.\build.ps1

# → produces installer\Output\parth-agent-0.1.3-x64-setup.exe
# → double-click it to install, then open a NEW terminal and run: parth
```

The full step-by-step is in `WINDOWS_BUILD.md` (prereqs, troubleshooting,
what's in `%APPDATA%\parth-agent\`, upgrade / uninstall flow,
before-release checklist).

---

## Known caveats to surface upfront

1. **Code-signing is not done** — Windows SmartScreen will prompt
   "More info → Run anyway" on first install. Documented in
   `WINDOWS_BUILD.md`.
2. **Runtime import smoke-test happens on Windows**, not here — the build
   was prepared on macOS without Python 3.10+ available. `build.ps1` step
   1 runs it before PyInstaller so any forward-port misfire fails the
   build fast with a readable message instead of a broken `.exe`.
3. **`MyAppURL` and `RELEASE_REPO`** default to
   `PrajsRamteke/parth-agent` with `TODO before public release` comments
   — change them if the repo lives elsewhere.
4. **`VERSION` is still `0.1.3`** — bump it in
   `parth/constants/models.py` before tagging a release; the
   source-of-truth flow ensures the installer filename and Add/Remove
   Programs entry track it.
5. **`build_windows/portable/`** is dead weight (zero-install bundle,
   empty site-packages). Not on the build path. Safe to delete later;
   left untouched.

Run `.\build.ps1` on the Windows PC and report which step (if any) it
stumbles on — that's Phase 1.1.

---

## Running from source for testing & debugging

You don't need the installer to run Parth while you're iterating on it.
Install the package in **editable mode** and your edits to `parth/*.py`
are picked up on the next launch — no rebuild, no install.

### One-time setup (Windows OR macOS — same commands)

```powershell
# Windows (PowerShell, from the parth-agent repo root)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip wheel
pip install -e .          # editable install — code edits take effect immediately
parth --help              # verify the entry point is on PATH
```

```bash
# macOS / Linux (zsh / bash, from the parth-agent repo root)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -e .
parth --help
```

> **Why `-e .` and not `pip install -r requirements.txt`?**
> `-e` registers the `parth` console entry-point (`pyproject.toml →
> [project.scripts]`). Without it you have to launch via
> `python agent.py` every time.

### Launching the TUI (default mode)

Three equivalent ways once the venv is active:

```powershell
parth                      # uses the installed entry point — preferred
python agent.py            # the thin shim entry point — same TUI
python -m parth            # module form — same TUI
```

All three open the same Textual TUI. Code edits in `parth/` are visible
the next time you launch (no reinstall thanks to `-e .`).

### Headless / one-shot prompt (no TUI)

Useful for scripting and quick smoke-tests:

```powershell
parth -p "what does parth/tools/router.py do?"
# Runs the agent against a single prompt, prints the answer, exits.
# Auto-approves shell commands — only use for trusted prompts.
```

### Legacy Rich REPL

If the Textual TUI misbehaves on your terminal, fall back to the older
Rich-based REPL — same agent, simpler renderer:

```powershell
parth --legacy
# or:
python agent.py --legacy
```

### Web remote (the "server" mode)

Parth ships a built-in web UI you can drive from a browser on another
machine — useful for debugging the TUI / streaming protocol, or for
sharing a session over your LAN.

```powershell
# default port (8765)
parth --web

# pick a port — these two forms are equivalent
parth --web 8080
parth --web --web-port 8080
```

The TUI launches as usual; in addition, an HTTP server starts on the
chosen port and prints a URL + a QR code in the status bar. Open the URL
on another device to drive the same conversation. The web UI is bundled
at `parth/web/ui.html` and lives behind a small bridge in
`parth/web/server.py`.

> **Bind address.** The server binds to all interfaces by default. On a
> shared network, treat the URL as a temporary shared session — anyone
> who can reach the port can read & send. Stop the agent (Ctrl-D or
> `/exit`) to shut the server down.

### Running the tests

```powershell
pip install pytest         # one-time
python -m pytest tests/ -q
```

37 unit tests cover CLI argument parsing, OAuth flows, prompt attachments,
tool routing, model picker, MCP scope, OpenCode usage parsing, and more.

### Useful environment variables (set before launch)

| Var | What | Example |
|-----|------|---------|
| `ANTHROPIC_API_KEY` | Bypass the auth prompt (pins Anthropic) | `sk-ant-…` |
| `OPENROUTER_API_KEY` | Pin OpenRouter | `sk-or-…` |
| `OPENCODE_API_KEY` | Pin OpenCode Go | — |
| `OPENCODE_ZEN_API_KEY` | Pin OpenCode Zen | — |
| `PARTH_PROVIDER` | Force provider choice | `anthropic` / `openrouter` / `opencode` / `opencode_zen` |
| `CLAUDE_MODEL` | Force default startup model | `sonnet-4-6` |
| `PARTH_MAX_PARALLEL_TOOLS` | Concurrent tool workers (1–64) | `8` |
| `PARTH_BUNDLE_MAX_CHARS` | Max chars in `resolve_context` / `read_bundle` | `120000` |
| `PARTH_BUNDLE_PER_FILE_MAX` | Per-file cap inside a bundle | `20000` |
| `PARTH_BUNDLE_MODE` | Default for `resolve_context` | `skeleton` / `full` / `manifest` |
| `PARTH_HTTP_READ_TIMEOUT` | Streaming response timeout (sec) | `240` |
| `PARTH_HTTP_CONNECT_TIMEOUT` | Connection timeout (sec) | `30` |
| `PARTH_STREAM_REPLY` | Set to `0` to disable live streaming of assistant text | `0` |
| `PARTH_RELEASE_REPO` | Override the GitHub repo `/upgrade` watches | `PrajsRamteke/parth-agent` |

Set them inline in PowerShell:

```powershell
$env:CLAUDE_MODEL = "sonnet-4-6"
$env:PARTH_PROVIDER = "anthropic"
parth
```

Or persistently in your user environment (Start → "Edit environment
variables for your account").

### Verifying a code change

After editing any file under `parth/`, three ways to confirm it works:

1. **Compile-only** (fastest, no runtime):
   ```powershell
   python -m py_compile parth\<path>\<file>.py
   ```
2. **Import check** (catches missing-symbol errors):
   ```powershell
   python -c "import parth, parth.cli, parth.tui.app, parth.tools, parth.tools.plan, parth.tui.intro_anim, parth.utils.json_repair, parth.storage.commands, parth.tui.command_modal; print('ok')"
   ```
3. **Live in the TUI**: `parth` and exercise the affected feature.

### Where data lives in dev-mode

When you run from source, Parth reads/writes the **same** directories the
installed version uses:

| Path | What |
|------|------|
| `%APPDATA%\parth-agent\` (Windows) / `~/.config/parth-agent/` (macOS/Linux) | API keys, sessions DB, memory, lessons, themes, MCP config |
| `~/.parth/` (every platform) | User-authored agents, skills, commands, global settings |
| `<cwd>/.parth/` | Per-project agents, skills, commands, settings |

This means **dev-mode keys & history are not isolated from the installed
build** — they share storage. To work with a throwaway profile, point the
config dir somewhere else for the dev session:

```powershell
# Windows
$env:APPDATA = "C:\temp\parth-dev"
parth
```

```bash
# macOS / Linux
XDG_CONFIG_HOME=/tmp/parth-dev parth
```

> Caveat: Parth's path resolver uses `%APPDATA%` on Windows directly, so
> overriding `APPDATA` is the cleanest dev sandbox. On macOS/Linux,
> `CONFIG_DIR` is hard-coded to `~/.config/parth-agent` — to sandbox, edit
> `parth/constants/paths.py` for the dev session.

### Hot-iteration tips

- **Auto-restart**: there isn't a built-in watcher. Use Ctrl-D to exit
  and re-run `parth`. The Textual TUI starts in ~0.3 s.
- **Debug logs**: pass `-v` to PyInstaller, or for runtime, add `print()`
  statements freely — they land in the transcript via the swapped
  `TUIConsole`. Use `state.show_internal = True` (or press `Ctrl-T` in
  the TUI) to surface the internal tool trace.
- **Test ONE provider end-to-end**: `$env:PARTH_PROVIDER="parth_agent";
  parth` — uses the free models, no API key.
- **Reset state**: rename `%APPDATA%\parth-agent\` for one session to
  start fresh, then rename it back.

### When you're ready to ship the dev build as an installer

```powershell
.\build.ps1
```

This packages the **current state of `parth/`** — whatever you've been
editing in dev-mode — into `installer\Output\parth-agent-<ver>-x64-setup.exe`.

---

## Quick command reference

| Command | What |
|---------|------|
| `parth` | Launch the TUI |
| `parth --legacy` | Launch the Rich REPL |
| `parth -p "…"` | Headless one-shot prompt |
| `parth --web [PORT]` | TUI + web remote server |
| `parth --help` | Full CLI help |
| `python -m pytest tests/ -q` | Run the test suite |
| `.\build.ps1` | Build the Windows installer (Windows only) |
| `.\build.ps1 -SkipVenv` | Rebuild without re-installing deps |
| `.\build.ps1 -VerySilentTest` | Build + install on this machine |

Inside the TUI:

| Slash command | What |
|---------------|------|
| `/help` | List every command |
| `/model` | Switch model |
| `/agent` | Activate/deactivate a coding agent |
| `/skill` | Browse skills |
| `/command` | Manage custom prompt commands (forward-ported) |
| `/plan on` | Read-only plan mode (forward-ported) |
| `/memory` | Persistent profile |
| `/mcp` | Connect MCP servers |
| `/upgrade` | Check for a newer `parth.exe` |
| `/exit` | Quit |
