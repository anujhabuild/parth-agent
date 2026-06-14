"""Browser remote control for a running Parth session."""

from .bridge import WebBridge
from .server import start_web_server

__all__ = ["WebBridge", "start_web_server"]
