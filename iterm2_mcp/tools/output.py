"""Output reading tools: read_output, watch_session."""

import json

from .. import applescript
from ..sessions import resolve_session
from .._server import mcp

# In-memory cursor state for watch_session
_watch_cursors: dict[str, str] = {}


async def _get_contents(session_id: str) -> str:
    """Read the visible contents of a session by ID."""
    sid = applescript.escape(session_id)
    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s to return contents
                end if
            end repeat
        end repeat
    end repeat
    return ""
end tell
'''
    return await applescript.run(script)


@mcp.tool()
async def iterm_read_output(identifier: str, lines: int = 50) -> str:
    """Read recent visible output from an iTerm2 session.

    Returns the last N lines of visible terminal content.

    Args:
        identifier: A session ID, TTY path, or (partial) session name.
        lines:      Maximum number of lines to return (default 50).
    """
    session = await resolve_session(identifier)
    raw = await _get_contents(session["session_id"])

    all_lines = raw.splitlines()
    while all_lines and not all_lines[-1].strip():
        all_lines.pop()
    trimmed = all_lines[-lines:] if len(all_lines) > lines else all_lines

    return json.dumps({
        "session_id": session["session_id"],
        "name": session["name"],
        "line_count": len(trimmed),
        "output": "\n".join(trimmed),
    })


@mcp.tool()
async def iterm_watch_session(identifier: str) -> str:
    """Get only new output since the last watch call for a session.

    On the first call for a session this returns the full visible buffer.
    Subsequent calls return only lines that were not present previously.
    Useful for polling a long-running command.

    Args:
        identifier: A session ID, TTY path, or (partial) session name.
    """
    session = await resolve_session(identifier)
    sid = session["session_id"]
    raw = await _get_contents(sid)

    all_lines = raw.splitlines()
    while all_lines and not all_lines[-1].strip():
        all_lines.pop()

    current_text = "\n".join(all_lines)
    previous_text = _watch_cursors.get(sid, "")

    if previous_text and current_text.startswith(previous_text):
        new_text = current_text[len(previous_text):]
        if new_text.startswith("\n"):
            new_text = new_text[1:]
    elif previous_text:
        new_text = current_text
    else:
        new_text = current_text

    _watch_cursors[sid] = current_text
    new_lines = new_text.splitlines() if new_text else []

    return json.dumps({
        "session_id": sid,
        "name": session["name"],
        "new_line_count": len(new_lines),
        "new_output": new_text,
        "is_first_read": previous_text == "",
    })
