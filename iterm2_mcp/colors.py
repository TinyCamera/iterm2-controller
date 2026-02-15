"""Color schemes for Claude-created iTerm2 sessions."""

from . import applescript

# Tab colors: {r, g, b} in 8-bit (0-255) for iTerm2 escape sequences.

SCHEMES = {
    "background_task": {"tab": (124, 58, 237)},   # Purple
    "split_pane":      {"tab": (59, 130, 246)},    # Blue
}


async def apply(session_id: str, scheme_name: str) -> None:
    """Apply a tab color to a session by ID."""
    scheme = SCHEMES.get(scheme_name)
    if not scheme:
        return

    sid = applescript.escape(session_id)
    tab = scheme["tab"]

    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if id of s is "{sid}" then
                    tell s
                        set esc to ASCII character 27
                        set bel to ASCII character 7
                        write text esc & "]6;1;bg;red;brightness;{tab[0]}" & bel without newline
                        write text esc & "]6;1;bg;green;brightness;{tab[1]}" & bel without newline
                        write text esc & "]6;1;bg;blue;brightness;{tab[2]}" & bel without newline
                    end tell
                    return "ok"
                end if
            end repeat
        end repeat
    end repeat
end tell
'''
    await applescript.run(script)
