# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iTerm2 Controller is a Claude Code plugin that exposes iTerm2 terminal control as MCP tools via AppleScript. It lets Claude create tabs/panes, send commands, read output, and monitor sessions in iTerm2.

## Running the Server

The MCP server runs automatically when loaded as a Claude Code plugin. To run manually:

```bash
.venv/bin/python3 server.py
```

## Development Setup

Python 3.12 with a local venv. Key dependency: `mcp` (FastMCP framework).

```bash
# Recreate venv if needed
python3 -m venv .venv
.venv/bin/pip install mcp pydantic httpx
```

## Testing

No automated tests. Testing is manual per `TEST_RESULTS.md` which documents 33 test cases across all 11 tools. Run tools interactively through Claude Code to verify behavior.

## Architecture

**Entry point:** `server.py` → creates FastMCP server, registers tools, runs stdio transport.

**Package layout (`iterm2_mcp/`):**

- `_server.py` — Singleton `FastMCP("iterm2-mcp")` instance shared across modules
- `applescript.py` — AppleScript execution bridge to iTerm2 (session enumeration, command execution)
- `sessions.py` — Session state persisted to `/tmp/iterm2-mcp-sessions.json`, fuzzy name matching via `difflib.SequenceMatcher`
- `colors.py` — Tab coloring via iTerm2 escape sequences (purple for background tasks, blue for split panes)
- `tools/` — MCP tool definitions, each module registers tools via `@mcp.tool()` decorator:
  - `session_mgmt.py` — register, list, focus, get-by-name, rename
  - `terminals.py` — new tab, split pane
  - `commands.py` — send command, send keys
  - `output.py` — read output, watch session (incremental via in-memory cursors)

**Key pattern:** Tools resolve sessions flexibly — by session ID, TTY path, or fuzzy name match. All tool functions are async and return JSON strings.

**Plugin structure:** `.claude-plugin/plugin.json` defines plugin metadata. `.mcp.json` configures the MCP server command. `hooks/hooks.json` displays the TTY path on session start to help with session registration.

## Known Issues

See `TEST_RESULTS.md` for current status. All previously tracked issues (Issues #1–#4) have been fixed. Test score: 33/33 (100%).
