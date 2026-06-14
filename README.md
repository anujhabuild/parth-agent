# Parth — Parth Terminal Agent

**AI coding agent for your Windows terminal.**
Chat, run tools, edit files, execute shell commands — all from one TUI.

---

## ✨ Overview

Parth is a **terminal-native AI agent** that lives in your Windows terminal. You talk to it, it uses tools — reads/writes files, runs shell commands, searches code, uses git, OCRs images, browses the web — and gets work done right where your code lives.

> **No web UI, no daemon.** Just `parth` in your project folder.
>
> **Windows-only build.** This branch ships a single Inno Setup `.exe` for Windows. See [`WINDOWS_BUILD.md`](WINDOWS_BUILD.md) for the build recipe and [`MANUAL.md`](MANUAL.md) for everything from "what's done" to "how to run from source."

---

## 🚀 Quick Start

### Option A — install the `.exe` (most users)

1. Grab the latest installer from the [Releases page](https://github.com/anujhabuild/parth-agent/releases) (`parth-agent-<version>-x64-setup.exe`).
2. Double-click it. Defaults are fine: install to `C:\Program Files\Parth Agent`, "Add to PATH" ticked.
3. Open a **new** PowerShell or Windows Terminal (PATH was just updated) and run:

```powershell
parth
```

You'll be prompted to pick an auth method on first launch — by default the free **Parth Agent** provider just works, no API key needed.

> **SmartScreen** may prompt "More info → Run anyway" — the installer isn't code-signed yet.

### Option B — run from source (development / debugging)

Need Python 3.10+ on PATH (3.11 recommended). From the repo root in PowerShell:

```powershell
git clone https://github.com/anujhabuild/parth-agent.git
cd parth-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
parth
```

Code edits to `parth/*.py` take effect on the next launch — no rebuild required (that's what `-e` buys you).

### Option C — build the `.exe` yourself

Need Python 3.10+ **and** Inno Setup 6. From the repo root:

```powershell
.\build.ps1
# → installer\Output\parth-agent-0.1.3-x64-setup.exe
```

Full details, troubleshooting, and the before-release checklist are in [`WINDOWS_BUILD.md`](WINDOWS_BUILD.md).

---

## ✅ Requirements

**Runtime (end user):**
- Windows 10 or 11 (x64).
- That's it — the installer ships its own Python.

**Optional at runtime:**
- An API key (`sk-ant-…`, `sk-or-…`, OpenCode) **or** a Claude/ChatGPT OAuth login. None of these are required — the free **Parth Agent** provider is the default and works without credentials.
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (auto-detected at `C:\Program Files\Tesseract-OCR\`) — only if you'll use `read_image_text` / `read_images_text`.

**Build machine (only if you're building the installer):**
- Python 3.10+ (3.11 recommended) from python.org or the Microsoft Store.
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) at the default `C:\Program Files (x86)\Inno Setup 6\` path.
- Git (for clone + the in-app `/upgrade` flow).

---

## 🧰 Features

| | |
|---|---|
| 💬 **Interactive TUI** — Textual-powered terminal UI with markdown, syntax-highlighted code, panels, and streaming responses. | 🔐 **Multi-Auth** — free Parth Agent (no key), API keys (`sk-ant-…`, `sk-or-…`, OpenCode), or OAuth via PKCE (Anthropic, Codex). |
| 📁 **File Ops** — read, write, edit; `list_dir`, `glob_files`, `rank_files`, `fast_find`, `search_code` (ripgrep). | 🐚 **Shell Access** — run any PowerShell or CMD command, view output inline. |
| ⎇ **Git Integration** — status, diff, log straight from chat. | 📋 **Clipboard** — `clipboard_get` / `clipboard_set` via the bundled Windows `clip` command. |
| 🌐 **Web Access** — DuckDuckGo search + URL fetch; `verified_search` cross-checks multiple sources. | 🧠 **Persistent Memory** — facts about you across sessions; lessons, notes, aliases under `%APPDATA%\parth-agent\`. |
| 🛠️ **Custom Commands** — drop `.md` prompt templates in `.parth/commands/`; trigger with `/<name> [args]`. `$ARGUMENTS` / `$1..$9` placeholders. | 📐 **Plan Mode** — `/plan on` for read-only research, then `exit_plan_mode` to surface the plan for approval before any edits. |
| 🧩 **Agents & Skills** — project-local agents (`.parth/agents/*.md`) and skills (`.parth/skills/<name>/SKILL.md`) auto-discovered from Parth, Claude Code, OpenCode, Cursor configs. | 🔌 **MCP Support** — Model Context Protocol; connect external tools and data sources at runtime via `/mcp`. |
| 📊 **Cost Tracking** — `/cost` shows token usage and estimated USD spend per session. | 🎨 **Themes** — 15+ built-in (red, purple, ocean, cyberpunk, dracula, …); switch live with `/theme`. |

---

## 📦 Installation

### Production install via the `.exe`

```powershell
# 1. download parth-agent-<ver>-x64-setup.exe from Releases
# 2. double-click — accept defaults (per-user install, "Add to PATH" ticked)
# 3. open a NEW terminal, then:
parth
```

User data — API keys, chat history, memory, lessons, themes, MCP config — lives under `%APPDATA%\parth-agent\`. **Preserved** across upgrades; uninstall **asks before** wiping.

### Upgrade

* **In-app:** type `/upgrade` to fetch the latest release and self-replace.
* **Manual:** install a newer `.exe` over the older one. Inno Setup detects the prior install (via `AppId`), closes a running `parth.exe`, replaces files in-place, and preserves your data.

### Uninstall

Start Menu → Parth Agent → Uninstall Parth Agent (or Add/Remove Programs). Removes binaries, PATH entry, and shortcuts. You're **prompted** whether to also wipe `%APPDATA%\parth-agent\` (default: No).

### Development install

```powershell
git clone https://github.com/anujhabuild/parth-agent.git
cd parth-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip wheel
pip install -e .          # editable install — registers `parth` and watches your edits
parth --help              # verify
```

Equivalent on macOS / Linux while developing:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
parth --help
```

> `pip install -e .` is preferred over `pip install -r requirements.txt` — only the editable install registers the `parth` console entry point. `requirements.txt` mirrors the deps for tooling that doesn't read `pyproject.toml`.

**Run the agent:**

```powershell
parth                      # TUI (default)
python agent.py            # same TUI via the entry-shim
python -m parth            # same TUI via module form
parth --legacy             # Rich REPL (older renderer)
parth -p "your prompt"     # headless one-shot
parth --web                # TUI + web remote UI on :8765
parth --web 8080           # TUI + web remote UI on a custom port
```

**Run tests:**

```powershell
pip install pytest         # one-time
python -m pytest tests/ -q
```

---

## 🎮 Usage

```powershell
parth
```

Run it from the **folder you want it to work in**. The status bar shows the current project path — all file operations, code searches, and shell commands are scoped to that directory.

### First run

| Auth option | What you need | Notes |
|------------|---------------|-------|
| **Parth Agent (free)** | nothing | Default. OpenCode Zen free models — no API key, no setup. |
| **API key** | `sk-ant-…` / `sk-or-…` / OpenCode key | Paste once; stored at `%APPDATA%\parth-agent\` (`key`, `openrouter_key`, `opencode_key`). |
| **OAuth** | Claude or ChatGPT login | PKCE flow — works on the same machine you're signed into. |

### ⌨️ Slash Commands

| Command | What it does |
|---------|--------------|
| `/help` | List every command. |
| `/model [name]` | Switch model — `/model` opens the picker, `/model haiku-4-5` jumps directly. |
| `/agent` | Open the agent picker (Tab also cycles in the TUI). |
| `/agent new <name>` | Scaffold a new agent in `.parth/agents/<name>.md`. |
| `/agent init` | Scaffold a `.parth/` tree in the current project. |
| `/skill` | Browse skills (LLM auto-invokes by `description:`). |
| `/command` | Manage custom prompt commands — list, new, edit, show, delete, run, refresh, import/export. |
| `/<name> [args]` | Trigger a custom command directly. `$ARGUMENTS` and `$1..$9` are substituted into the template. |
| `/plan on` / `/plan off` | Toggle read-only plan mode (research → `exit_plan_mode` → approve → edits). |
| `/memory` | Manage persistent profile facts. |
| `/lesson` | Manage your saved lessons. |
| `/pin` | Pin context lines that are prepended to every message. |
| `/mcp` | Connect / list MCP servers. |
| `/think` | Toggle extended thinking budget. |
| `/cost` | Token usage + estimated USD spend for the session. |
| `/theme` | Switch the active theme (red, purple, ocean, dracula, …). |
| `/verbose` / `Ctrl-T` | Show internal tool trace. |
| `/upgrade` | Check for a newer `parth.exe` from GitHub Releases. |
| `/clear` | Reset the conversation. |
| `/exit` | Quit. |

---

## ⚙️ Environment Variables

| Variable | What it does | Default |
|----------|--------------|---------|
| `ANTHROPIC_API_KEY` | Bypass auth prompt (pins Anthropic). | — |
| `OPENROUTER_API_KEY` | Pin OpenRouter. | — |
| `OPENCODE_API_KEY` | Pin OpenCode Go. | — |
| `OPENCODE_ZEN_API_KEY` | Pin OpenCode Zen. | — |
| `PARTH_PROVIDER` | Force provider: `anthropic` / `openrouter` / `opencode` / `opencode_zen` / `parth_agent`. | (auto) |
| `CLAUDE_MODEL` | Override default startup model. | `sonnet-4-6` |
| `PARTH_MAX_PARALLEL_TOOLS` | Concurrent tool workers. | `64` (cap) |
| `PARTH_BUNDLE_MAX_CHARS` | Max chars in `resolve_context` / `read_bundle`. | `120000` |
| `PARTH_BUNDLE_PER_FILE_MAX` | Per-file cap inside a bundle. | `20000` |
| `PARTH_BUNDLE_MODE` | Default for `resolve_context`: `full` / `skeleton` / `manifest`. | `skeleton` |
| `PARTH_HTTP_READ_TIMEOUT` | Streaming response timeout (s). | `240` (OpenRouter), `600` (direct) |
| `PARTH_HTTP_CONNECT_TIMEOUT` | Connection timeout (s). | `30` |
| `PARTH_STREAM_REPLY` | Set to `0` to disable live streaming. | `1` |
| `PARTH_RELEASE_REPO` | Override the GitHub repo `/upgrade` watches. | `anujhabuild/parth-agent` |

Set them inline in PowerShell:

```powershell
$env:CLAUDE_MODEL = "sonnet-4-6"
$env:PARTH_PROVIDER = "anthropic"
parth
```

Or persistently via *Start → "Edit environment variables for your account"*.

---

## 🎛️ Agents, Skills, Commands

Parth has three file-based extension points that aggregate from every AI tool's config directory (Parth, Claude Code, OpenCode, Cursor, Windsurf, …):

```
project/
├── .parth/
│   ├── agents/                   ← project-local agents (manually selected)
│   │   ├── coding.md
│   │   ├── reverse_eng.md
│   │   └── setup.md
│   ├── skills/                   ← project-local skills (LLM auto-invokes)
│   │   ├── debugging/SKILL.md
│   │   └── testing/SKILL.md
│   ├── commands/                 ← custom slash commands (you trigger)
│   │   ├── pr-description.md
│   │   └── code-review.md
│   └── settings.json             ← (optional) per-project overrides
│
├── AGENTS.md  /  CLAUDE.md  /  PARTH.md   ← project context (auto-detected)
└── …

%USERPROFILE%\.parth\             ← user-global counterpart on Windows
├── agents/                       ← bundled coding/reverse_eng/setup seeded on first run
├── skills/
├── commands/
└── settings.json
```

- **Agents** — markdown files with frontmatter (`name`, `description`, optional `icon` / `color` / `model`). The active agent's body is appended to the system prompt. One active at a time; `Tab` cycles in the TUI. `/agent` opens the picker.
- **Skills** — `SKILL.md` packs with `name` + `description`. The LLM sees descriptions and decides when to `skill_load` itself.
- **Custom commands** — `.md` prompt templates triggered as `/<name> [args]`. `$ARGUMENTS` and `$1..$9` are substituted. The `/command` modal is a full manager (list, new, edit, preview, delete, import/export).

---

## 🗂️ Project Layout

```
parth-agent/
├── agent.py                # Thin entrypoint (routes to TUI or REPL)
├── build.ps1               # End-to-end Windows installer build
├── pyproject.toml          # Package config + [build-windows] extra
├── MANUAL.md               # What's done, how to run, how to debug
├── WINDOWS_BUILD.md        # Installer build/upgrade/uninstall details
├── CLAUDE.md               # Context file for AI assistants
├── PARTH.md
│
├── parth/                  # Main package
│   ├── __main__.py         # `python -m parth`
│   ├── cli.py              # CLI entry point (--web, --legacy, -p)
│   ├── main.py             # Rich REPL send-and-loop
│   ├── state.py            # Module-level shared state
│   ├── updater_installer.py# Windows-installer self-update via /upgrade
│   │
│   ├── auth/               # API key, OAuth PKCE, OpenRouter, OpenCode, Codex
│   ├── tools/              # File, shell, git, search, web, OCR, plan, MCP
│   │   ├── router.py       # Dynamic per-message tool selection
│   │   ├── plan.py         # exit_plan_mode + PLAN_MODE_ALLOWED
│   │   ├── system.py       # Cross-platform open_url
│   │   └── web/            # DuckDuckGo + URL fetch + verified search
│   ├── repl/               # Stream, render, system prompt, banners
│   ├── tui/                # Textual app + all modals (agent, skill, command, …)
│   │   ├── app.py
│   │   ├── intro_anim.py   # Welcome-art shine sweep
│   │   └── command_modal.py# Custom command manager modal
│   ├── commands/           # Slash command handlers (dispatched by dispatch.py)
│   │   ├── command.py      # /command (custom commands manager)
│   │   └── control.py      # /plan, /think, /model, /provider, /theme, …
│   ├── storage/            # SQLite sessions, memory, lessons, agents, skills, commands
│   ├── mcp/                # MCP config / registry / manager
│   ├── utils/              # json_repair, tool_repair, http, schema, io, …
│   ├── web/                # Optional --web remote server + UI
│   └── constants/          # Paths (%APPDATA%-aware), models, system prompt, default agents
│
├── installer/              # PyInstaller spec + Inno Setup script + docs
│   ├── parth.spec
│   └── parth.iss
├── .github/workflows/
│   └── windows-installer.yml  # CI: builds + uploads the .exe on every push and tag
├── assets/
│   └── parth.ico           # Multi-resolution Windows icon (16/24/32/48/64/128/256)
├── scripts/                # Verification / dev scripts
└── tests/                  # 37 pytest unit tests (`python -m pytest tests/ -q`)
```

---

## 📝 Notes

- **Credentials & data** — All config, keys, sessions, memory, lessons, themes live under `%APPDATA%\parth-agent\` on Windows (`~/.config/parth-agent/` on macOS/Linux). User-authored agents/skills/commands live under `%USERPROFILE%\.parth\`. Both directories survive upgrades; uninstall **asks before** touching the first one and never touches the second.
- **Tool selection is dynamic** — `tools/router.py` regex-scans the last few messages and only sends the schemas for tool groups it thinks you'll need (web, OCR, memory, skills, plan, MCP). Core file/code tools are always included. Keeps context lean and cheap.
- **Plan mode** — `/plan on` enters a read-only research mode. The model investigates, drafts a markdown plan, and calls `exit_plan_mode` to surface it for your approval. Approval flips the gate off mid-turn so the next API call regains the full toolset and starts executing.
- **Project context** — Drop a `PARTH.md` (or `AGENTS.md` / `CLAUDE.md`) in your project root and the agent reads it automatically for project-specific instructions.
- **In-app updates** — Frozen `.exe` builds check this repo's GitHub Releases on launch and via `/upgrade`. Override the watched repo with `PARTH_RELEASE_REPO=owner/repo`.

---

## 📚 More

- [`MANUAL.md`](MANUAL.md) — Phase 1 ship summary, build recipe, dev/debug run-from-source, env-var reference.
- [`WINDOWS_BUILD.md`](WINDOWS_BUILD.md) — Deeper installer build & upgrade docs.
- [`installer/README.md`](installer/README.md) — AppId, signing slot, ARM64 plans.
- [`PARTH.md`](PARTH.md) — Project context shipped with the repo.
- [`CLAUDE.md`](CLAUDE.md) — Context for AI assistants navigating this codebase.

---

Built with ❤️ — Windows port and Phase 1 forward-port by [@anujhabuild](https://github.com/anujhabuild).

[GitHub](https://github.com/anujhabuild/parth-agent) · [Issues](https://github.com/anujhabuild/parth-agent/issues) · [Releases](https://github.com/anujhabuild/parth-agent/releases)
