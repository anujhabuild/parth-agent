"""Tool JSON schemas for cross-platform system tools."""

SYSTEM_TOOLS = [
    {
        "name": "clipboard_get",
        "description": "Return current clipboard text.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "clipboard_set",
        "description": "Set clipboard text.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "open_url",
        "description": "Open a URL or local file path in the OS default handler (browser, viewer, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
]
