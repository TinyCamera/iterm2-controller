#!/usr/bin/env python3
"""Automated test runner for iTerm2 MCP tools against a live iTerm2 instance."""

import asyncio
import json
import sys

# Import all tool functions directly
from iterm2_mcp.tools import register_all
from iterm2_mcp._server import mcp

register_all(mcp)

from iterm2_mcp.tools.session_mgmt import (
    iterm_list_sessions,
    iterm_register_session,
    iterm_focus_session,
    iterm_get_session_by_name,
    iterm_set_session_name,
)
from iterm2_mcp.tools.terminals import iterm_new_tab, iterm_split_pane
from iterm2_mcp.tools.commands import iterm_send_command, iterm_send_keys
from iterm2_mcp.tools.output import iterm_read_output, iterm_watch_session


passed = 0
failed = 0
errors = []


def result(test_id: str, name: str, ok: bool, detail: str = ""):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
        errors.append((test_id, name, detail))
    print(f"  [{status}] {test_id}: {name}" + (f" — {detail}" if detail else ""))


async def run_tests():
    print("=" * 60)
    print("iTerm2 MCP Tool Test Suite")
    print("=" * 60)

    # ── Test 1.1: List all sessions ──
    print("\n── Session Listing ──")
    raw = await iterm_list_sessions()
    sessions = json.loads(raw)
    ok = isinstance(sessions, list) and len(sessions) > 0
    result("1.1", "List all sessions", ok,
           f"got {len(sessions)} sessions" if ok else f"unexpected: {raw[:100]}")
    if not ok:
        print("FATAL: No sessions found. Is iTerm2 running?")
        return

    # Grab a known session for later tests
    first_session = sessions[0]
    first_tty = first_session["tty"]
    has_fields = all(k in first_session for k in
                     ["session_id", "name", "tty", "window_id", "window_name", "tab_index"])
    result("1.1b", "Session has all required fields", has_fields,
           "" if has_fields else f"missing fields in {list(first_session.keys())}")

    # ── Test 2.1: Register current session ──
    print("\n── Session Registration ──")
    raw = await iterm_register_session(first_tty)
    data = json.loads(raw)
    ok = data.get("status") == "registered" and data.get("tty") == first_tty
    result("2.1", "Register session by TTY", ok, str(data.get("status", data.get("error", ""))))

    # ── Test 2.2: Register invalid TTY ──
    raw = await iterm_register_session("/dev/ttys999")
    data = json.loads(raw)
    ok = "error" in data
    result("2.2", "Register invalid TTY returns error", ok,
           data.get("error", "no error returned")[:80])

    # ── Test 2.3: Re-register same TTY ──
    raw = await iterm_register_session(first_tty)
    data = json.loads(raw)
    ok = data.get("status") == "registered"
    result("2.3", "Re-register same TTY succeeds", ok)

    # ── Test 1.2: List sessions shows registered flag ──
    raw = await iterm_list_sessions()
    sessions = json.loads(raw)
    registered = [s for s in sessions if s.get("registered")]
    ok = len(registered) > 0
    result("1.2", "List sessions shows registered flag", ok,
           f"{len(registered)} registered" if ok else "none registered")

    # ── Test 3.1: Find session by exact name ──
    print("\n── Session Lookup by Name ──")
    target_name = first_session["name"]
    raw = await iterm_get_session_by_name(target_name)
    data = json.loads(raw)
    ok = isinstance(data, list) and len(data) > 0
    result("3.1", "Find session by exact name", ok,
           f"found {len(data)} match(es)" if ok else str(data))

    # ── Test 3.2: Find session by partial name ──
    partial = target_name[:max(4, len(target_name) // 2)]
    raw = await iterm_get_session_by_name(partial)
    data = json.loads(raw)
    ok = isinstance(data, list) and len(data) > 0
    result("3.2", f"Find session by partial name '{partial}'", ok,
           f"found {len(data)} match(es)" if ok else str(data))

    # ── Test 3.3: Find session with no match ──
    raw = await iterm_get_session_by_name("zzz_nonexistent_session_zzz")
    data = json.loads(raw)
    ok = "error" in data
    result("3.3", "Find nonexistent session returns error", ok,
           data.get("error", "no error returned")[:80])

    # ── Test 4.1: Create new tab (no args) ──
    print("\n── Tab/Pane Creation ──")
    raw = await iterm_new_tab()
    data = json.loads(raw)
    tab1_id = data.get("session_id", "")
    ok = data.get("status") == "created" and tab1_id and data.get("tty")
    result("4.1", "Create new tab (no args)", ok,
           f"session_id={tab1_id[:20]}..." if ok else str(data))

    await asyncio.sleep(0.5)  # let tab settle

    # ── Test 4.2: Create new tab with name ──
    raw = await iterm_new_tab(name="test-tab-named")
    data = json.loads(raw)
    named_tab_id = data.get("session_id", "")
    ok_create = data.get("status") == "created"

    # Verify the name was actually set
    await asyncio.sleep(0.5)
    raw2 = await iterm_get_session_by_name("test-tab-named")
    lookup = json.loads(raw2)
    ok_name = isinstance(lookup, list) and len(lookup) > 0
    result("4.2", "Create new tab with name", ok_create and ok_name,
           "name set correctly" if ok_name else f"name lookup failed: {str(lookup)[:80]}")

    # ── Test 4.3: Create new tab with command ──
    raw = await iterm_new_tab(command="echo hello_from_new_tab_test")
    data = json.loads(raw)
    cmd_tab_id = data.get("session_id", "")
    await asyncio.sleep(1)  # let command run
    raw2 = await iterm_read_output(cmd_tab_id, lines=10)
    out = json.loads(raw2)
    ok = "hello_from_new_tab_test" in out.get("output", "")
    result("4.3", "Create new tab with command", ok,
           "command output found" if ok else f"output: {out.get('output', '')[:80]}")

    # ── Test 4.4: Split pane vertically ──
    raw = await iterm_split_pane(direction="vertical")
    data = json.loads(raw)
    vsplit_id = data.get("session_id", "")
    ok = data.get("status") == "created" and data.get("direction") == "vertical"
    result("4.4", "Split pane vertically", ok)

    await asyncio.sleep(0.5)

    # ── Test 4.5: Split pane horizontally ──
    raw = await iterm_split_pane(direction="horizontal")
    data = json.loads(raw)
    ok = data.get("status") == "created" and data.get("direction") == "horizontal"
    result("4.5", "Split pane horizontally", ok)

    await asyncio.sleep(0.5)

    # ── Test 4.6: Split pane with name ──
    raw = await iterm_split_pane(name="test-split-named")
    data = json.loads(raw)
    ok_create = data.get("status") == "created"
    await asyncio.sleep(0.5)
    raw2 = await iterm_get_session_by_name("test-split-named")
    lookup = json.loads(raw2)
    ok_name = isinstance(lookup, list) and len(lookup) > 0
    result("4.6", "Split pane with name", ok_create and ok_name,
           "name set correctly" if ok_name else f"name lookup failed: {str(lookup)[:80]}")

    # ── Test 4.7: Split pane with invalid direction ──
    raw = await iterm_split_pane(direction="diagonal")
    data = json.loads(raw)
    ok = "error" in data
    result("4.7", "Split pane invalid direction returns error", ok,
           data.get("error", "")[:60])

    # ── Test 5.1: Rename session ──
    print("\n── Session Rename & Focus ──")
    raw = await iterm_set_session_name(tab1_id, "renamed-test-tab")
    data = json.loads(raw)
    ok = data.get("status") == "renamed" and data.get("new_name") == "renamed-test-tab"
    result("5.1", "Rename session", ok, str(data.get("status")))

    await asyncio.sleep(0.3)

    # ── Test 5.2: Focus session by ID ──
    raw = await iterm_focus_session(tab1_id)
    data = json.loads(raw)
    ok = data.get("status") == "focused"
    result("5.2", "Focus session by ID", ok)

    # ── Test 5.3: Focus session by name ──
    raw = await iterm_focus_session("renamed-test-tab")
    data = json.loads(raw)
    ok = data.get("status") == "focused" and data.get("session_id") == tab1_id
    result("5.3", "Focus session by name", ok,
           f"matched {data.get('session_id', '')[:20]}" if ok else str(data))

    # ── Test 5.4: Focus nonexistent session ──
    try:
        raw = await iterm_focus_session("nonexistent_xyz_99999")
        data = json.loads(raw)
        # Should have gotten an error either as exception or in response
        ok = "error" in data or data.get("status") == "not_found"
        result("5.4", "Focus nonexistent session returns error", ok,
               f"got status={data.get('status')}" if not ok else "")
    except RuntimeError as e:
        # resolve_session raised — this is the correct behavior
        ok = "No session found" in str(e)
        result("5.4", "Focus nonexistent session returns error", ok, str(e)[:80])

    # ── Test 6.1: Send simple command ──
    print("\n── Command Execution ──")
    raw = await iterm_send_command(tab1_id, "echo test123_marker")
    data = json.loads(raw)
    ok_sent = data.get("status") == "sent"
    await asyncio.sleep(0.5)
    raw2 = await iterm_read_output(tab1_id, lines=5)
    out = json.loads(raw2)
    ok = ok_sent and "test123_marker" in out.get("output", "")
    result("6.1", "Send simple command", ok,
           "output verified" if ok else f"output: {out.get('output', '')[:60]}")

    # ── Test 6.2: Send command with special characters ──
    raw = await iterm_send_command(tab1_id, """echo 'hello "world"'""")
    data = json.loads(raw)
    await asyncio.sleep(0.5)
    raw2 = await iterm_read_output(tab1_id, lines=5)
    out = json.loads(raw2)
    ok = 'hello "world"' in out.get("output", "")
    result("6.2", "Send command with special characters", ok,
           "quotes preserved" if ok else f"output: {out.get('output', '')[:60]}")

    # ── Test 6.3: Send ctrl+c to interrupt ──
    await iterm_send_command(tab1_id, "sleep 30")
    await asyncio.sleep(0.5)
    raw = await iterm_send_keys(tab1_id, "ctrl+c")
    data = json.loads(raw)
    ok = data.get("status") == "sent"
    await asyncio.sleep(0.5)
    raw2 = await iterm_read_output(tab1_id, lines=5)
    out = json.loads(raw2)
    ok = ok and ("^C" in out.get("output", "") or "interrupt" in out.get("output", "").lower())
    result("6.3", "Send ctrl+c to interrupt", ok,
           "interrupt confirmed" if ok else f"output: {out.get('output', '')[:60]}")

    # ── Test 6.4: Send multiple keys ──
    raw = await iterm_send_keys(tab1_id, "up up enter")
    data = json.loads(raw)
    ok = data.get("status") == "sent"
    result("6.4", "Send multiple keys (up up enter)", ok)

    # ── Test 6.5: Send arrow keys ──
    raw = await iterm_send_keys(tab1_id, "left right")
    data = json.loads(raw)
    ok = data.get("status") == "sent"
    result("6.5", "Send arrow keys", ok)

    # ── Test 6.6: Send invalid key name ──
    raw = await iterm_send_keys(tab1_id, "ctrl+invalid")
    data = json.loads(raw)
    ok = "error" in data
    result("6.6", "Send invalid key name returns error", ok,
           data.get("error", "no error")[:60] if ok else f"got: {data}")

    # ── Test 7.1: Read output ──
    print("\n── Output Reading ──")
    await iterm_send_command(tab1_id, "echo READ_TEST_MARKER")
    await asyncio.sleep(0.5)
    raw = await iterm_read_output(tab1_id)
    data = json.loads(raw)
    ok = "READ_TEST_MARKER" in data.get("output", "") and "session_id" in data
    result("7.1", "Read output contains expected text", ok)

    # ── Test 7.2: Read output with line limit ──
    raw = await iterm_read_output(tab1_id, lines=5)
    data = json.loads(raw)
    ok = data.get("line_count", 0) <= 5
    result("7.2", "Read output with line limit", ok,
           f"line_count={data.get('line_count')}")

    # ── Test 7.3: Watch session (first call) ──
    # Use a fresh tab for clean watch test
    raw = await iterm_new_tab(command="echo WATCH_BASELINE")
    watch_tab = json.loads(raw)
    watch_id = watch_tab.get("session_id", "")
    await asyncio.sleep(1)

    raw = await iterm_watch_session(watch_id)
    data = json.loads(raw)
    ok = data.get("is_first_read") is True and data.get("new_line_count", 0) > 0
    result("7.3", "Watch session first call", ok,
           f"is_first_read={data.get('is_first_read')}, lines={data.get('new_line_count')}")

    # ── Test 7.4: Watch session (subsequent call) ──
    await iterm_send_command(watch_id, "echo WATCH_DELTA_MARKER")
    await asyncio.sleep(0.5)
    raw = await iterm_watch_session(watch_id)
    data = json.loads(raw)
    ok = (data.get("is_first_read") is False and
          "WATCH_DELTA_MARKER" in data.get("new_output", ""))
    result("7.4", "Watch session incremental output", ok,
           f"is_first_read={data.get('is_first_read')}, has_delta={'WATCH_DELTA_MARKER' in data.get('new_output', '')}")

    # ── Test 8.1: E2E — Create tab, run command, read output ──
    print("\n── End-to-End ──")
    raw = await iterm_new_tab()
    e2e_tab = json.loads(raw)
    e2e_id = e2e_tab.get("session_id", "")
    await asyncio.sleep(0.5)
    await iterm_send_command(e2e_id, "echo E2E_TEST_MARKER")
    await asyncio.sleep(0.5)
    raw = await iterm_read_output(e2e_id, lines=10)
    data = json.loads(raw)
    ok = "E2E_TEST_MARKER" in data.get("output", "")
    result("8.1", "E2E: create tab → send command → read output", ok)

    # ── Test 8.2: E2E — Split pane, watch for new output ──
    raw = await iterm_split_pane(direction="horizontal")
    split_data = json.loads(raw)
    split_id = split_data.get("session_id", "")
    await asyncio.sleep(0.5)
    await iterm_watch_session(split_id)  # baseline
    await iterm_send_command(split_id, "echo WATCH_E2E_MARKER")
    await asyncio.sleep(0.5)
    raw = await iterm_watch_session(split_id)
    data = json.loads(raw)
    ok = (data.get("is_first_read") is False and
          "WATCH_E2E_MARKER" in data.get("new_output", ""))
    result("8.2", "E2E: split pane → watch incremental output", ok)

    # ── Test 8.3: E2E — Create tab, rename, find by name ──
    raw = await iterm_new_tab()
    rename_tab = json.loads(raw)
    rename_id = rename_tab.get("session_id", "")
    await asyncio.sleep(0.3)
    await iterm_set_session_name(rename_id, "unique-e2e-test-name")
    await asyncio.sleep(0.3)
    raw = await iterm_get_session_by_name("unique-e2e-test")
    data = json.loads(raw)
    ok = isinstance(data, list) and any(
        s.get("session_id") == rename_id for s in data
    )
    result("8.3", "E2E: create tab → rename → find by partial name", ok,
           f"found={ok}, matches={len(data) if isinstance(data, list) else data}")

    # ── Test 9.1: Send empty command ──
    print("\n── Edge Cases ──")
    raw = await iterm_send_command(tab1_id, "")
    data = json.loads(raw)
    ok = data.get("status") == "sent"
    result("9.1", "Send empty command (just Enter)", ok)

    # ── Test 9.2: Read output from invalid session ID ──
    try:
        raw = await iterm_read_output("INVALID-SESSION-ID-12345")
        data = json.loads(raw)
        ok = "error" in data
        result("9.2", "Read output from invalid session errors", ok,
               f"got response without error: {str(data)[:60]}" if not ok else "")
    except RuntimeError as e:
        ok = "No session found" in str(e)
        result("9.2", "Read output from invalid session errors", ok, str(e)[:80])

    # ── Test 9.3: Send command to invalid session ──
    try:
        raw = await iterm_send_command("INVALID-SESSION-ID-12345", "echo SHOULD_NOT_RUN")
        data = json.loads(raw)
        ok = "error" in data
        result("9.3", "Send command to invalid session errors", ok,
               f"got response without error: {str(data)[:60]}" if not ok else "")
    except RuntimeError as e:
        ok = "No session found" in str(e)
        result("9.3", "Send command to invalid session errors", ok, str(e)[:80])

    # ── Test 9.4: Create tab in nonexistent window ──
    try:
        raw = await iterm_new_tab(window_identifier="NONEXISTENT_WINDOW_99999")
        data = json.loads(raw)
        ok = "error" in data
        result("9.4", "Create tab in nonexistent window errors", ok,
               f"got response without error: {str(data)[:60]}" if not ok else "")
    except RuntimeError as e:
        ok = "No session found" in str(e)
        result("9.4", "Create tab in nonexistent window errors", ok, str(e)[:80])

    # ── Summary ──
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{passed + failed} passed ({100 * passed // (passed + failed)}%)")
    print("=" * 60)
    if errors:
        print(f"\n{len(errors)} FAILURE(S):")
        for tid, name, detail in errors:
            print(f"  {tid}: {name}")
            if detail:
                print(f"         {detail}")
    print()


if __name__ == "__main__":
    asyncio.run(run_tests())
