"""Filesystem paths used by the agent."""
import os
import pathlib
import platform
import sys


def _default_config_dir() -> pathlib.Path:
    """Return the OS-appropriate per-user config directory for parth-agent.

    Windows uses %APPDATA% (roaming profile). macOS and Linux use the XDG
    convention ~/.config/parth-agent for consistency with other dev tooling.
    """
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return pathlib.Path(appdata) / "parth-agent"
        return pathlib.Path.home() / "AppData" / "Roaming" / "parth-agent"
    return pathlib.Path.home() / ".config" / "parth-agent"


CWD = pathlib.Path.cwd()
CONFIG_DIR = _default_config_dir()

# User-authored agents + skills live under ~/.parth/ on every platform.
# This mirrors the convention of .ssh / .aws / .claude — a dotted directory
# in the user's home that Windows handles transparently.
PARTH_HOME = pathlib.Path.home() / ".parth"
PARTH_AGENTS_DIR = PARTH_HOME / "agents"
PARTH_SKILLS_DIR = PARTH_HOME / "skills"
PARTH_COMMANDS_DIR = PARTH_HOME / "commands"
PARTH_SETTINGS_FILE = PARTH_HOME / "settings.json"

# Project-local Parth directory (per-repo .parth/).
PROJECT_PARTH_DIRNAME = ".parth"
PROJECT_AGENTS_DIRNAME = ".parth/agents"
PROJECT_SKILLS_DIRNAME = ".parth/skills"
PROJECT_COMMANDS_DIRNAME = ".parth/commands"
PROJECT_PARTH_SETTINGS = ".parth/settings.json"


def set_cwd(path: str | pathlib.Path) -> pathlib.Path:
    """Update Parth' project root across already-imported modules."""
    new_cwd = pathlib.Path(path).expanduser().resolve()
    global CWD
    CWD = new_cwd

    for name, mod in list(sys.modules.items()):
        if not name.startswith("parth.") or mod is None:
            continue
        if hasattr(mod, "CWD"):
            try:
                setattr(mod, "CWD", new_cwd)
            except Exception:
                pass
    return new_cwd

SESSIONS_LIST_LIMIT = 50
SESSION_TITLE_MAX_LENGTH = 80
KEY_FILE = CONFIG_DIR / "key"
OPENROUTER_KEY_FILE = CONFIG_DIR / "openrouter_key"
OPENCODE_KEY_FILE = CONFIG_DIR / "opencode_key"
OPENCODE_ZEN_KEY_FILE = CONFIG_DIR / "opencode_zen_key"
OAUTH_FILE = CONFIG_DIR / "oauth.json"
CODEX_OAUTH_FILE = CONFIG_DIR / "codex_oauth.json"
AUTH_MODE_FILE = CONFIG_DIR / "auth_mode"
PROVIDER_FILE = CONFIG_DIR / "provider"
HIST_FILE = CONFIG_DIR / "history.json"
NOTES_FILE = CONFIG_DIR / "notes.md"
PIN_FILE = CONFIG_DIR / "pinned.txt"
ALIAS_FILE = CONFIG_DIR / "aliases.json"
SESSIONS_DB = CONFIG_DIR / "sessions.db"
MEMORY_FILE = CONFIG_DIR / "memory.json"
LESSONS_FILE = CONFIG_DIR / "lessons.json"
LAST_MODEL_FILE = CONFIG_DIR / "last_model.json"
LAST_THEME_FILE = CONFIG_DIR / "last_theme.json"
SKILLS_CONFIG_FILE = CONFIG_DIR / "skills_config.json"
THINK_CONFIG_FILE = CONFIG_DIR / "think_config.json"
MCP_PREFS_FILE = CONFIG_DIR / "mcp_config.json"
