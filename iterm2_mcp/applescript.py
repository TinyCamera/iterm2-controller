"""AppleScript execution and iTerm2 session enumeration."""

import asyncio


async def run(script: str) -> str:
    """Execute an AppleScript snippet and return its stdout."""
    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"AppleScript error: {stderr.decode().strip()}")
    return stdout.decode().strip()


def escape(text: str) -> str:
    """Escape a string for embedding inside AppleScript double-quotes."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


async def list_all_sessions() -> list[dict]:
    """Return a list of dicts describing every iTerm2 session."""
    script = '''
tell application "iTerm2"
    set output to ""
    repeat with w in windows
        set wid to id of w
        set wname to name of w
        set tlist to tabs of w
        set tcount to 0
        repeat with t in tlist
            set tcount to tcount + 1
            set slist to sessions of t
            repeat with s in slist
                set sid to id of s
                set sname to name of s
                set stty to tty of s
                set output to output & sid & "||" & sname & "||" & stty & "||" & wid & "||" & wname & "||" & tcount & linefeed
            end repeat
        end repeat
    end repeat
    return output
end tell
'''
    raw = await run(script)
    sessions = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("||")
        if len(parts) < 6:
            continue
        sessions.append({
            "session_id": parts[0],
            "name": parts[1],
            "tty": parts[2],
            "window_id": parts[3],
            "window_name": parts[4],
            "tab_index": int(parts[5]),
        })
    return sessions
