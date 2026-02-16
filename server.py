#!/usr/bin/env python3
"""iTerm2 MCP Server entrypoint."""

from iterm2_mcp._server import mcp
from iterm2_mcp.tools import register_all

register_all(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
