"""Detect image inputs from drag-drop paths or clipboard, run OCR, return text."""
import hashlib
import re
import shlex
import tempfile
import pathlib
from typing import Optional

from ..constants import CWD
from .ocr import read_image_text
from ..path_resolve import robust_resolve

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".heic"}


def _is_image_path(s: str) -> Optional[pathlib.Path]:
    if not s:
        return None
    p = robust_resolve(s, CWD)
    if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
        return p
    return None


def extract_image_paths(text: str) -> list[tuple[str, pathlib.Path]]:
    """Return [(raw_token, resolved_path)] for image file paths found in text.

    Handles shell-escaped drag-drop paths (e.g. `/foo/bar\\ baz.png`) and quoted paths.
    """
    found: list[tuple[str, pathlib.Path]] = []
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        tokens = text.split()

    for tok in tokens:
        p = _is_image_path(tok)
        if p:
            # rebuild the raw representation as it likely appeared in the input
            # try both quoted and backslash-escaped forms
            found.append((tok, p))

    # also scan raw regex for anything ending with image ext we missed
    for m in re.finditer(r"(?:[\w./~\-\\ ]+?)\.(?:png|jpg|jpeg|gif|bmp|tiff?|webp|heic)\b",
                         text, re.IGNORECASE):
        raw = m.group(0).replace("\\ ", " ")
        p = _is_image_path(raw)
        if p and not any(p == rp for _, rp in found):
            found.append((m.group(0), p))
    return found


def clipboard_image_to_file() -> Optional[pathlib.Path]:
    """If the system clipboard contains an image, write it to a temp PNG and return its path.

    Cross-platform via Pillow's ImageGrab. Returns None when the clipboard is
    empty, holds non-image content, or Pillow is unavailable.
    """
    try:
        from PIL import ImageGrab
    except ImportError:
        return None
    try:
        img = ImageGrab.grabclipboard()
    except Exception:
        return None
    if img is None:
        return None
    # On Linux, grabclipboard() can return a list of file paths instead of an image.
    if isinstance(img, list):
        for entry in img:
            p = pathlib.Path(str(entry))
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                return p
        return None
    tmp = pathlib.Path(tempfile.gettempdir()) / "parth_clipboard.png"
    try:
        img.save(tmp, format="PNG")
    except Exception:
        return None
    if tmp.exists() and tmp.stat().st_size > 0:
        return tmp
    return None


def file_digest(path: pathlib.Path) -> str:
    """Return a stable digest for a file so repeated clipboard pastes can be deduped."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ocr_image_block(path: pathlib.Path, label: Optional[str] = None) -> tuple[str, str]:
    """Return an OCR wrapper block and raw OCR text for an image file."""
    display_name = label or path.name
    ocr = read_image_text(str(path))
    block = f"[image: {display_name} — OCR text]\n{ocr}\n[/image]"
    return block, ocr


def append_image_block(text: str, block: str) -> str:
    """Append an OCR block to user text with stable spacing."""
    if not text.strip():
        return block
    return f"{text.rstrip()}\n\n{block}"


def process_input_for_images(text: str) -> str:
    """Scan input for image paths; replace each with an OCR'd text block.

    If the entire input is just the path, the output becomes the OCR block alone.
    """
    hits = extract_image_paths(text)
    if not hits:
        return text
    out = text
    for raw, path in hits:
        block, _ = ocr_image_block(path)
        replacement = f"\n\n{block}\n"
        # replace first occurrence of raw; if not present, append
        if raw in out:
            out = out.replace(raw, replacement, 1)
        else:
            out = append_image_block(out, block)
    return out.strip()
