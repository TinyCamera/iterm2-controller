"""Command execution tools: send_command, send_keys."""

import json

from .. import applescript
from ..sessions import resolve_session
from .._server import mcp

KEY_MAP: dict[str, str] = {
    "enter":     'write text ""',
    "return":    'write text ""',
    "tab":       "write text (ASCII character 9)",
    "escape":    "write text (ASCII character 27)",
    "esc":       "write text (ASCII character 27)",
    "ctrl+c":    "write text (ASCII character 3)",
    "ctrl+d":    "write text (ASCII character 4)",
    "ctrl+z":    "write text (ASCII character 26)",
    "ctrl+l":    "write text (ASCII character 12)",
    "ctrl+a":    "write text (ASCII character 1)",
    "ctrl+e":    "write text (ASCII character 5)",
    "ctrl+k":    "write text (ASCII character 11)",
    "ctrl+u":    "write text (ASCII character 21)",
    "ctrl+w":    "write text (ASCII character 23)",
    "ctrl+r":    "write text (ASCII character 18)",
    "ctrl+p":    "write text (ASCII character 16)",
    "ctrl+n":    "write text (ASCII character 14)",
    "up":        'write text (ASCII character 27) & "[A"',
    "down":      'write text (ASCII character 27) & "[B"',
    "right":     'write text (ASCII character 27) & "[C"',
    "left":      'write text (ASCII character 27) & "[D"',
    "backspace": "write text (ASCII character 127)",
    "delete":    "write text (ASCII character 127)",
    "space":     'write text " "',
}


@mcp.tool()
async def iterm_send_command(identifier: str, command: str) -> str:
    """Send a shell command (with Enter) to an iTerm2 session.

    The command text is sent followed by a newline, exactly as if
    the user typed it and pressed Enter.

    Args:
        identifier: A session ID, TTY path, or (partial) session name.
        command:    The command string to execute.
    """
    session = await resolve_session(identifier)
    sid = applescript.escape(session["session_id"])
    safe_cmd = applescript.escape(command)

    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s to write text "{safe_cmd}"
                    return "sent"
                end if
            end repeat
        end repeat
    end repeat
    return "not_found"
end tell
'''
    result = await applescript.run(script)
    return json.dumps({
        "status": "sent" if result == "sent" else "not_found",
        "session_id": session["session_id"],
        "command": command,
    })


@mcp.tool()
async def iterm_send_keys(identifier: str, keys: str) -> str:
    """Send special keys or key-combos to an iTerm2 session.

    Useful for sending Ctrl+C, arrow keys, Enter, etc.

    Args:
        identifier: A session ID, TTY path, or (partial) session name.
        keys:       Key name such as "ctrl+c", "up", "enter", "tab",
                    "escape", "ctrl+d", "ctrl+z", "ctrl+l", "space",
                    "backspace". Multiple keys can be separated by spaces
                    (e.g. "up up enter").
    """
    session = await resolve_session(identifier)
    sid = applescript.escape(session["session_id"])

    key_list = keys.strip().split()
    commands: list[str] = []
    for k in key_list:
        kl = k.lower()
        if kl in KEY_MAP:
            commands.append(KEY_MAP[kl])
        elif kl.startswith("ctrl+") and len(kl) == 6:
            char_code = ord(kl[-1].lower()) - ord("a") + 1
            commands.append(f"write text (ASCII character {char_code})")
        else:
            commands.append(f'write text "{applescript.escape(k)}" without newline')

    tell_lines = "\n                    ".join(commands)

    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s
                    {tell_lines}
                    end tell
                    return "sent"
                end if
            end repeat
        end repeat
    end repeat
    return "not_found"
end tell
'''
    result = await applescript.run(script)
    return json.dumps({
        "status": "sent" if result == "sent" else "not_found",
        "session_id": session["session_id"],
        "keys": keys,
    })
