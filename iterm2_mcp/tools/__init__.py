"""Tool registration - importing this module registers all tools."""


def register_all(mcp=None):
    """Import all tool modules so their @mcp.tool() decorators fire."""
    from . import session_mgmt, terminals, commands, output  # noqa: F401
