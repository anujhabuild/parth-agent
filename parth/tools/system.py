"""Cross-platform system helpers: open_url.

Uses Python's stdlib webbrowser module, which picks the right launcher per OS
(``open`` on macOS, ``start`` on Windows, ``xdg-open`` on Linux).
"""
import webbrowser


def open_url(url: str) -> str:
    if not url:
        return "ERROR: url is empty"
    try:
        ok = webbrowser.open(url, new=2, autoraise=True)
    except Exception as e:
        return f"ERROR: {e}"
    return "opened" if ok else "ERROR: no browser launcher available"
