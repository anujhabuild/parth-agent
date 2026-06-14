"""Cross-platform clipboard get/set via pyperclip.

pyperclip ships shims for every supported platform: it uses ctypes on Windows,
pbcopy/pbpaste on macOS, and xclip/xsel/wl-clipboard on Linux. Failures are
surfaced as a string so the tool loop can keep running.
"""
from ..constants import MAX_TOOL_OUTPUT


def clipboard_get() -> str:
    try:
        import pyperclip
    except ImportError:
        return "ERROR: pyperclip not installed; run pip install pyperclip"
    try:
        text = pyperclip.paste() or ""
    except Exception as e:
        return f"ERROR: clipboard read failed: {e}"
    return text[:MAX_TOOL_OUTPUT]


def clipboard_set(text: str) -> str:
    try:
        import pyperclip
    except ImportError:
        return "ERROR: pyperclip not installed; run pip install pyperclip"
    try:
        pyperclip.copy(text)
    except Exception as e:
        return f"ERROR: clipboard write failed: {e}"
    return f"clipboard set ({len(text)} chars)"
