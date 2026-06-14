# PyInstaller spec for the Parth Windows build.
#
# Build with:
#   pyinstaller installer/parth.spec --noconfirm
#
# Produces dist/parth/parth.exe (one-folder mode — faster startup than
# one-file, easier to debug, and Inno Setup wraps the folder cleanly).

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None


# ── Bundled data ──────────────────────────────────────────────────────────
# Parth ships a web remote UI, default agents, and a few HTML/CSS assets
# under parth/. They must be present at runtime alongside the .exe.
datas = []
datas += collect_data_files("parth.web", includes=["**/*.html", "**/*.css", "**/*.js"])
datas += collect_data_files("parth.constants", includes=["default_agents/*.md"])

# Textual ships CSS via package_data — pick it up explicitly so the TUI's
# default stylesheet is bundled. Rich/MCP also have some non-Python assets.
datas += collect_data_files("textual")
datas += collect_data_files("rich")
datas += collect_data_files("mcp", excludes=["**/__pycache__"])


# ── Hidden imports ────────────────────────────────────────────────────────
# PyInstaller's static analysis misses anything loaded via importlib /
# __import__ / lazy imports. Pull whole packages in by their submodule
# graph so MCP transports, Anthropic streaming helpers, etc. are present.
hiddenimports = []
# Parth's own submodules — guarantees forward-ported subpackages
# (parth.tools.plan, parth.storage.commands, parth.tui.command_modal,
# parth.tui.intro_anim, parth.utils.json_repair, parth.commands.command)
# all land in the bundle, even when only reached via dynamic dispatch.
hiddenimports += collect_submodules("parth")
hiddenimports += collect_submodules("anthropic")
hiddenimports += collect_submodules("openai")
hiddenimports += collect_submodules("httpx")
hiddenimports += collect_submodules("mcp")
hiddenimports += collect_submodules("textual")
hiddenimports += collect_submodules("rich")
hiddenimports += collect_submodules("pyperclip")
hiddenimports += [
    "PIL.ImageGrab",
    "PIL.Image",
    "pytesseract",
    "qrcode",
    "pypdf",
    "openpyxl",
]


a = Analysis(
    ["..\\parth\\__main__.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # macOS-only helpers — never used on Windows. Excluding them keeps the
        # bundle slim and ensures PyInstaller does not warn on missing PyObjC.
        "Foundation",
        "AppKit",
        "Quartz",
        "Vision",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="parth",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,           # Parth is a TUI — needs a console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="..\\assets\\parth.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="parth",
)
