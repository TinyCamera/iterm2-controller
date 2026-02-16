"""Color schemes for Claude-created iTerm2 sessions."""

from . import applescript

# Tab colors: {r, g, b} in 8-bit (0-255) for iTerm2 escape sequences.

SCHEMES = {
    "background_task": {"tab": (124, 58, 237)},   # Purple
    "split_pane":      {"tab": (59, 130, 246)},    # Blue
}


async def apply(session_id: str, scheme_name: str) -> None:
    """Apply a tab color to a session by ID.

    Writes iTerm2 proprietary OSC sequences directly to the session's
    TTY to avoid them appearing as visible text in the terminal.
    """
    scheme = SCHEMES.get(scheme_name)
    if not scheme:
        return

    # Resolve the TTY path for this session
    sid = applescript.escape(session_id)
    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    return tty of s
                end if
            end repeat
        end repeat
    end repeat
    return ""
end tell
'''
    tty = await applescript.run(script)
    if not tty:
        return

    tab = scheme["tab"]
    payload = (
        f"\x1b]6;1;bg;red;brightness;{tab[0]}\x07"
        f"\x1b]6;1;bg;green;brightness;{tab[1]}\x07"
        f"\x1b]6;1;bg;blue;brightness;{tab[2]}\x07"
    )

    # Write directly to TTY — bypasses the shell so nothing is echoed
    with open(tty, "w") as f:
        f.write(payload)
        f.flush()
