# iTerm2 MCP Tool Details

Complete parameter and return value documentation for all 11 tools.

## iterm_register_session

Register a TTY as belonging to the current Claude Code session.

**Parameters:**
- `tty_path` (str, required) — The TTY device path (e.g. `/dev/ttys004`)

**Returns:** `{status, tty, iterm_session_id, session_name}` or `{error}`

**Notes:** Call once per session. The SessionStart hook prints the TTY path automatically.

---

## iterm_list_sessions

List all iTerm2 sessions across every window, tab, and pane.

**Parameters:** None

**Returns:** JSON array of session objects:
```json
{
  "session_id": "w0t0p0:9B2F...",
  "name": "Default",
  "tty": "/dev/ttys004",
  "window_id": 1234,
  "tab_index": 0,
  "registered": true
}
```

---

## iterm_focus_session

Bring an iTerm2 session to the foreground.

**Parameters:**
- `identifier` (str, required) — Session ID, TTY path, or partial name

**Returns:** `{status, session_id, name}` where status is `"focused"` or `"not_found"`

---

## iterm_get_session_by_name

Find sessions by fuzzy name match.

**Parameters:**
- `name` (str, required) — Full or partial session name

**Returns:** Array of up to 5 matching session objects, sorted by match quality. Partial substring matches are boosted in scoring.

---

## iterm_set_session_name

Rename an iTerm2 session.

**Parameters:**
- `identifier` (str, required) — Session ID, TTY path, or partial name
- `new_name` (str, required) — The new display name

**Returns:** `{status, session_id, old_name, new_name}`

---

## iterm_new_tab

Create a new tab in an iTerm2 window.

**Parameters:**
- `command` (str, optional) — Shell command to run immediately
- `name` (str, optional) — Display name for the session
- `window_identifier` (str, optional) — Session ID, TTY, or name identifying which window. Defaults to frontmost window.

**Returns:** `{status, session_id, tty, name}`

**Notes:** New tabs receive a purple tab color automatically.

---

## iterm_split_pane

Split the current or specified pane.

**Parameters:**
- `direction` (str, optional) — `"vertical"` (side-by-side, default) or `"horizontal"` (top/bottom)
- `command` (str, optional) — Shell command to run
- `name` (str, optional) — Display name
- `identifier` (str, optional) — Session to split. Defaults to current session of frontmost window.

**Returns:** `{status, direction, session_id, tty, name}`

**Notes:** Split panes receive a blue tab color automatically.

---

## iterm_send_command

Send a shell command followed by Enter.

**Parameters:**
- `identifier` (str, required) — Session ID, TTY path, or partial name
- `command` (str, required) — The command string

**Returns:** `{status, session_id, command}`

---

## iterm_send_keys

Send special keys or key combinations.

**Parameters:**
- `identifier` (str, required) — Session ID, TTY path, or partial name
- `keys` (str, required) — Space-separated key names

**Supported keys:**

| Category | Keys |
|----------|------|
| Control | `ctrl+c`, `ctrl+d`, `ctrl+z`, `ctrl+l`, `ctrl+a`, `ctrl+e`, `ctrl+k`, `ctrl+u`, `ctrl+w`, `ctrl+r`, `ctrl+p`, `ctrl+n`, `ctrl+<any letter>` |
| Navigation | `up`, `down`, `left`, `right` |
| Editing | `enter`/`return`, `tab`, `escape`/`esc`, `backspace`/`delete`, `space` |

**Examples:**
- `"ctrl+c"` — Interrupt running process
- `"up enter"` — Re-run last command
- `"ctrl+a ctrl+k"` — Go to start of line, kill to end
- `"up up up enter"` — Navigate history 3 entries back, run it

**Returns:** `{status, session_id, keys}` or `{error}` if invalid key names

---

## iterm_read_output

Read the last N lines of visible terminal content.

**Parameters:**
- `identifier` (str, required) — Session ID, TTY path, or partial name
- `lines` (int, optional) — Max lines to return (default 50)

**Returns:** `{session_id, name, line_count, output}`

**Notes:** Returns visible buffer content. Terminal escape sequences are automatically stripped.

---

## iterm_watch_session

Get only new output since the last watch call.

**Parameters:**
- `identifier` (str, required) — Session ID, TTY path, or partial name

**Returns:**
```json
{
  "session_id": "...",
  "name": "...",
  "new_line_count": 5,
  "new_output": "...",
  "is_first_read": false
}
```

**Notes:**
- First call returns the full visible buffer (`is_first_read: true`)
- Subsequent calls return only new lines
- Cursor state is stored in-memory per session ID — resets if the MCP server restarts
- Ideal for polling long-running processes in a loop
