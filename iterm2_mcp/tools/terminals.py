"""Terminal creation tools: new_tab, split_pane."""

import json

from .. import applescript, colors
from ..sessions import resolve_session
from .._server import mcp


async def _send_command(session_id: str, command: str) -> None:
    """Send a shell command to a session by ID."""
    sid = applescript.escape(session_id)
    safe_cmd = applescript.escape(command)
    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s to write text "{safe_cmd}"
                    return
                end if
            end repeat
        end repeat
    end repeat
end tell
'''
    await applescript.run(script)


async def _set_session_name(session_id: str, name: str) -> None:
    """Set the display name on a session by ID."""
    sid = applescript.escape(session_id)
    safe_name = applescript.escape(name)
    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s to set name to "{safe_name}"
                    return
                end if
            end repeat
        end repeat
    end repeat
end tell
'''
    await applescript.run(script)


@mcp.tool()
async def iterm_new_tab(
    command: str = "",
    name: str = "",
    window_identifier: str = "",
) -> str:
    """Create a new tab in an iTerm2 window.

    Args:
        command:           Optional shell command to execute in the new tab.
        name:              Optional display name for the new session.
        window_identifier: Optional session ID, TTY, or name to identify
                           which window to create the tab in. Defaults to
                           the frontmost window.
    """
    if window_identifier:
        session = await resolve_session(window_identifier)
        wid = session["window_id"]
        window_ref = f"window id {wid}"
    else:
        window_ref = "first window"

    script = f'''
tell application "iTerm2"
    tell {window_ref}
        set newTab to (create tab with default profile)
        tell current session of newTab
            set sid to id of it
            set stty to tty of it
        end tell
    end tell
    return sid & "||" & stty
end tell
'''
    raw = await applescript.run(script)
    p = raw.split("||")
    session_id = p[0] if len(p) > 0 else ""

    await colors.apply(session_id, "background_task")

    if name:
        await _set_session_name(session_id, name)

    if command:
        await _send_command(session_id, command)

    return json.dumps({
        "status": "created",
        "session_id": session_id,
        "tty": p[1] if len(p) > 1 else "",
        "name": name,
    })


@mcp.tool()
async def iterm_split_pane(
    direction: str = "vertical",
    command: str = "",
    name: str = "",
    identifier: str = "",
) -> str:
    """Split the current (or specified) pane to create a new session.

    Args:
        direction:  "vertical" (side-by-side) or "horizontal" (top/bottom).
        command:    Optional shell command to run in the new pane.
        name:       Optional display name for the new session.
        identifier: Optional session ID, TTY, or name of the pane to split.
                    Defaults to the current session of the frontmost window.
    """
    if direction not in ("vertical", "horizontal"):
        return json.dumps({"error": "direction must be 'vertical' or 'horizontal'."})

    split_cmd = "split vertically" if direction == "vertical" else "split horizontally"

    if identifier:
        session = await resolve_session(identifier)
        sid = applescript.escape(session["session_id"])
        script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s
                        set newSession to ({split_cmd} with default profile)
                    end tell
                    tell newSession
                        set rsid to id of it
                        set rtty to tty of it
                    end tell
                    return rsid & "||" & rtty
                end if
            end repeat
        end repeat
    end repeat
    return "not_found"
end tell
'''
    else:
        script = f'''
tell application "iTerm2"
    tell first window
        tell current session of current tab
            set newSession to ({split_cmd} with default profile)
        end tell
        tell newSession
            set rsid to id of it
            set rtty to tty of it
        end tell
    end tell
    return rsid & "||" & rtty
end tell
'''

    raw = await applescript.run(script)
    if raw == "not_found":
        return json.dumps({"error": "Session not found for splitting."})

    p = raw.split("||")
    session_id = p[0] if len(p) > 0 else ""

    await colors.apply(session_id, "split_pane")

    if name:
        await _set_session_name(session_id, name)

    if command:
        await _send_command(session_id, command)

    return json.dumps({
        "status": "created",
        "direction": direction,
        "session_id": session_id,
        "tty": p[1] if len(p) > 1 else "",
        "name": name,
    })
