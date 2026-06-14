"""Installer-mode auto-update.

Activated when Parth is running as a PyInstaller frozen bundle on Windows.
Hits the GitHub Releases API, compares against the running VERSION, and (on
user consent or auto-mode) downloads the new ``parth-agent-{ver}-x64-setup.exe``,
launches it with ``/SILENT`` so it does an in-place upgrade, then exits the
current process so the installer can replace files.

For source / pip-install-e mode we fall back to the original git-pull updater
in ``parth.updater``.
"""
from __future__ import annotations

import json
import os
import pathlib
import platform
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

from .constants.models import (
    RELEASE_INSTALLER_ASSET,
    RELEASE_REPO,
    VERSION,
)


# ── Detection ────────────────────────────────────────────────────────────


def is_frozen_install() -> bool:
    """True when running from a PyInstaller bundle (the .exe installer mode)."""
    return bool(getattr(sys, "frozen", False))


def is_windows() -> bool:
    return platform.system() == "Windows"


# ── Version comparison ──────────────────────────────────────────────────


def _parse_version(tag: str) -> tuple[int, ...]:
    """Tolerant semver-ish parser. ``v0.1.3`` -> ``(0, 1, 3)``."""
    cleaned = tag.lstrip("vV").split("-", 1)[0]  # strip prefix + pre-release suffix
    parts = []
    for chunk in cleaned.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


def _is_newer(remote: str, local: str = VERSION) -> bool:
    return _parse_version(remote) > _parse_version(local)


# ── GitHub Releases lookup ──────────────────────────────────────────────


def fetch_latest_release(timeout: float = 10.0) -> dict | None:
    """Return the JSON payload of the latest GitHub release, or None on failure.

    Uses the public unauthenticated endpoint — 60 req/hr/IP is plenty.
    """
    if not RELEASE_REPO or "/" not in RELEASE_REPO:
        return None
    url = f"https://api.github.com/repos/{RELEASE_REPO}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"parth-agent/{VERSION}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _pick_installer_asset(release: dict) -> tuple[str, str] | None:
    """Return (version, download_url) for the .exe asset, or None."""
    tag = release.get("tag_name") or ""
    version = tag.lstrip("vV")
    expected = RELEASE_INSTALLER_ASSET.format(version=version)
    for asset in release.get("assets", []) or []:
        if asset.get("name") == expected:
            url = asset.get("browser_download_url")
            if url:
                return version, url
    # Fallback: any .exe in the release, prefer one matching x64-setup
    for asset in release.get("assets", []) or []:
        name = asset.get("name", "")
        if name.lower().endswith("-x64-setup.exe"):
            url = asset.get("browser_download_url")
            if url:
                return version, url
    return None


# ── Update check / download / launch ────────────────────────────────────


def check_for_update() -> dict | None:
    """Return ``{"version": x.y.z, "url": ..., "notes": ...}`` if newer; else None."""
    if not (is_frozen_install() and is_windows()):
        return None
    release = fetch_latest_release()
    if not release:
        return None
    picked = _pick_installer_asset(release)
    if not picked:
        return None
    version, url = picked
    if not _is_newer(version):
        return None
    return {
        "version": version,
        "url": url,
        "notes": (release.get("body") or "").strip(),
        "published": release.get("published_at"),
    }


def download_installer(url: str, dest: pathlib.Path | None = None) -> pathlib.Path | None:
    """Stream the installer to %TEMP% and return the local path on success."""
    if dest is None:
        dest = pathlib.Path(tempfile.gettempdir()) / "parth-agent-latest-setup.exe"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"parth-agent/{VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp, dest.open("wb") as out:
            # 1 MB chunks — keep memory bounded for slow/large connections.
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    if dest.stat().st_size <= 0:
        return None
    return dest


def launch_installer(installer_path: pathlib.Path, *, silent: bool = True) -> bool:
    """Spawn the installer and return True if it launched.

    /SILENT shows progress but no wizard pages; /VERYSILENT shows nothing.
    /CLOSEAPPLICATIONS lets the installer terminate any running parth.exe so
    file replacement can proceed.
    """
    if not installer_path.exists():
        return False
    args = [str(installer_path)]
    if silent:
        args.append("/SILENT")
    args += ["/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/NORESTART"]
    try:
        subprocess.Popen(args, close_fds=True)
    except OSError:
        return False
    return True


def apply_update_and_exit(info: dict) -> bool:
    """Download + launch the new installer, then ``os._exit`` so it can replace files.

    Returns False without exiting when the download or launch fails so the caller
    can surface an error to the user.
    """
    path = download_installer(info["url"])
    if path is None:
        return False
    if not launch_installer(path):
        return False
    # Hard exit — sys.exit() would run cleanup handlers that hold file locks on
    # parth.exe and stop the installer from replacing it.
    os._exit(0)
    return True  # unreachable but keeps type-checkers happy
