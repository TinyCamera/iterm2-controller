# iTerm2 Controller

A Claude Code plugin that gives Claude control over iTerm2 terminals via AppleScript. Create tabs, split panes, send commands, read output, and monitor sessions — all from within Claude Code.

## Requirements

- macOS with iTerm2 installed
- Python 3.12+
- Claude Code

## Installation

```
/plugin marketplace add TinyCamera/iterm2-controller
/plugin install iterm2-controller
```

## Setup

On first use, macOS will prompt you to allow your terminal to control iTerm2 via AppleScript. Grant this permission — it's a one-time dialog.

On session start, the plugin displays your TTY path. Register it to link your terminal:

```
iterm_register_session("/dev/ttys004")
```

## Tools

### Session Management

| Tool | Description |
|------|-------------|
| `iterm_register_session` | Link a TTY to the current Claude session |
| `iterm_list_sessions` | List all iTerm2 sessions across windows, tabs, and panes |
| `iterm_get_session_by_name` | Find sessions by fuzzy name match |
| `iterm_focus_session` | Bring a session to the foreground |
| `iterm_set_session_name` | Rename a session |

### Terminal Creation

| Tool | Description |
|------|-------------|
| `iterm_new_tab` | Create a new tab (optionally with a command and name) |
| `iterm_split_pane` | Split a pane vertically or horizontally |

### Command Execution

| Tool | Description |
|------|-------------|
| `iterm_send_command` | Send a shell command to a session |
| `iterm_send_keys` | Send special keys (Ctrl+C, arrows, Enter, etc.) |

### Output Reading

| Tool | Description |
|------|-------------|
| `iterm_read_output` | Read recent terminal output (last N lines) |
| `iterm_watch_session` | Poll for new output since the last read |

All tools accept a session identifier as a session ID, TTY path, or fuzzy name match.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install mcp pydantic httpx
.venv/bin/python3 server.py
```

## License

MIT
