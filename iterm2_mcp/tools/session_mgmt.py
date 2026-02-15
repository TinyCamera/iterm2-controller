"""Session management tools: register, list, focus, get_by_name, set_name."""

import json
from datetime import datetime, timezone

from .. import applescript
from ..sessions import load_state, save_state, fuzzy_match, resolve_session
from .._server import mcp


@mcp.tool()
async def iterm_register_session(tty_path: str) -> str:
    """Register a TTY as belonging to the current Claude Code session.

    Call this once at session start so other tools know which terminal
    belongs to this Claude session.

    Args:
        tty_path: The TTY device path (e.g. "/dev/ttys004").
    """
    all_sessions = await applescript.list_all_sessions()
    session = next((s for s in all_sessions if s["tty"] == tty_path), None)
    if session is None:
        return json.dumps({
            "error": f"No iTerm2 session found with tty {tty_path}. "
                     "Make sure iTerm2 is running and the tty is correct."
        })

    state = load_state()
    state["sessions"][tty_path] = {
        "iterm_session_id": session["session_id"],
        "session_name": session["name"],
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(state)

    return json.dumps({
        "status": "registered",
        "tty": tty_path,
        "iterm_session_id": session["session_id"],
        "session_name": session["name"],
    })


@mcp.tool()
async def iterm_list_sessions() -> str:
    """List all iTerm2 sessions across every window, tab, and pane.

    Returns a JSON array of session objects with id, name, tty,
    window info, tab index, and whether it is registered to a Claude session.
    """
    all_sessions = await applescript.list_all_sessions()
    state = load_state()
    registered_ttys = set(state.get("sessions", {}).keys())

    for s in all_sessions:
        s["registered"] = s["tty"] in registered_ttys

    return json.dumps(all_sessions, indent=2)


@mcp.tool()
async def iterm_focus_session(identifier: str) -> str:
    """Bring an iTerm2 session to the foreground.

    Args:
        identifier: A session ID, TTY path, or (partial) session name.
    """
    session = await resolve_session(identifier)
    sid = applescript.escape(session["session_id"])

    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell t to select
                    return "focused"
                end if
            end repeat
        end repeat
    end repeat
    return "not_found"
end tell
'''
    result = await applescript.run(script)
    return json.dumps({
        "status": "focused" if result == "focused" else "not_found",
        "session_id": session["session_id"],
        "name": session["name"],
    })


@mcp.tool()
async def iterm_get_session_by_name(name: str) -> str:
    """Find iTerm2 sessions whose name matches the query (fuzzy).

    Args:
        name: Full or partial session name to search for.
    """
    all_sessions = await applescript.list_all_sessions()
    matches = fuzzy_match(name, all_sessions)
    if not matches:
        return json.dumps({"error": f"No session matching '{name}'."})
    return json.dumps(matches[:5], indent=2)


@mcp.tool()
async def iterm_set_session_name(identifier: str, new_name: str) -> str:
    """Rename an iTerm2 session.

    Args:
        identifier: A session ID, TTY path, or (partial) session name.
        new_name:   The new display name to set.
    """
    session = await resolve_session(identifier)
    sid = applescript.escape(session["session_id"])
    safe_name = applescript.escape(new_name)

    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s to set name to "{safe_name}"
                    return "renamed"
                end if
            end repeat
        end repeat
    end repeat
    return "not_found"
end tell
'''
    result = await applescript.run(script)
    return json.dumps({
        "status": "renamed" if result == "renamed" else "not_found",
        "session_id": session["session_id"],
        "old_name": session["name"],
        "new_name": new_name,
    })
