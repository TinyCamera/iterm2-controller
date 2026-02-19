---
name: using-iterm2
version: 1.0.0
description: This skill should be used when the user asks to "run something in iTerm", "open a terminal", "create a new tab", "split a pane", "run a background task", "monitor a process", "watch a running process", "check terminal output", "send a command to iTerm", "send ctrl+c", "set up a terminal layout", or when working with iTerm2 MCP tools (iterm_*). Also applies when orchestrating multi-terminal workflows or long-running processes.
---

# Using iTerm2 Controller

This plugin provides MCP tools to control iTerm2 terminals via AppleScript. Use these tools to create tabs, split panes, send commands, read output, and monitor sessions — all without leaving Claude Code.

## Prerequisites

- iTerm2 must be running
- macOS Automation permission must be granted (System Settings > Privacy & Security > Automation)

## Session Registration (Required First Step)

Before using any tools, register the current terminal session. The SessionStart hook displays the TTY path automatically:

```
iTerm2 session TTY: /dev/ttys004 — call iterm_register_session with this path to link this terminal.
```

Call `iterm_register_session` with that TTY path. This links the terminal to the session state so other tools can find it.

## Session Identifiers

All tools that take an `identifier` parameter accept three formats:
- **Session ID** — the iTerm2 internal ID (e.g. `w0t0p0:9B2F...`)
- **TTY path** — the device path (e.g. `/dev/ttys004`)
- **Session name** — full or partial, fuzzy-matched (e.g. `"server"` matches `"dev-server"`)

Prefer names for readability. Name sessions when creating them to make subsequent commands clearer.

## Tool Reference

### Terminal Creation

| Tool | Purpose | Key Args |
|------|---------|----------|
| `iterm_new_tab` | Create a new tab | `command`, `name`, `window_identifier` |
| `iterm_split_pane` | Split current/specified pane | `direction` (`vertical`/`horizontal`), `command`, `name`, `identifier` |

New tabs get a purple tab color; split panes get blue. Both accept an optional `command` to run immediately and a `name` for identification.

### Command Execution

| Tool | Purpose | Key Args |
|------|---------|----------|
| `iterm_send_command` | Send a command + Enter | `identifier`, `command` |
| `iterm_send_keys` | Send special keys/combos | `identifier`, `keys` |

`iterm_send_keys` supports: `enter`, `tab`, `escape`, `ctrl+c`, `ctrl+d`, `ctrl+z`, `ctrl+l`, `ctrl+a`, `ctrl+e`, `ctrl+k`, `ctrl+u`, `ctrl+w`, `ctrl+r`, `up`, `down`, `left`, `right`, `backspace`, `space`, and any `ctrl+<letter>`. Combine multiple keys with spaces: `"up up enter"`.

### Output Reading

| Tool | Purpose | Key Args |
|------|---------|----------|
| `iterm_read_output` | Read last N lines of visible output | `identifier`, `lines` (default 50) |
| `iterm_watch_session` | Get only new output since last call | `identifier` |

Use `iterm_read_output` for one-off checks. Use `iterm_watch_session` for polling long-running processes — it returns only lines added since the previous call.

### Session Management

| Tool | Purpose | Key Args |
|------|---------|----------|
| `iterm_register_session` | Register a TTY to session state | `tty_path` |
| `iterm_list_sessions` | List all sessions across all windows/tabs | — |
| `iterm_focus_session` | Bring a session to the foreground | `identifier` |
| `iterm_get_session_by_name` | Fuzzy-search sessions by name | `name` |
| `iterm_set_session_name` | Rename a session | `identifier`, `new_name` |

## Common Workflows

### Background Task

Run a long-running process in a separate tab, then poll for output:

1. `iterm_new_tab(command="npm run dev", name="dev-server")`
2. Wait, then `iterm_watch_session(identifier="dev-server")`
3. Repeat step 2 to get incremental output

### Multi-Pane Development

Set up a split layout for development:

1. `iterm_split_pane(direction="vertical", command="npm run dev", name="server")`
2. `iterm_split_pane(direction="horizontal", command="npm test -- --watch", name="tests")`
3. Monitor both: `iterm_watch_session(identifier="server")` and `iterm_watch_session(identifier="tests")`

### Interactive Process Control

Send keystrokes to an interactive program:

1. `iterm_send_command(identifier="server", command="node inspect app.js")`
2. `iterm_send_keys(identifier="server", keys="ctrl+c")` — to interrupt
3. `iterm_send_keys(identifier="server", keys="up enter")` — re-run last command

### Checking on a Running Process

Read recent output without disrupting:

1. `iterm_read_output(identifier="server", lines=20)` — last 20 lines
2. Or `iterm_watch_session(identifier="server")` — only what's new

## Tips

- Always name sessions when creating them — makes subsequent tool calls readable
- Use `iterm_list_sessions` to discover existing sessions if unsure what's running
- `iterm_watch_session` resets its cursor on each unique session — first call returns the full buffer
- Prefer `iterm_send_keys(keys="ctrl+c")` over sending raw escape characters
- The `command` parameter on `iterm_new_tab` and `iterm_split_pane` runs after tab creation — use it to immediately start processes

## Additional Resources

### Reference Files

For the complete list of supported key names and detailed tool parameters:
- **`references/tool-details.md`** — Full parameter documentation and return value schemas
