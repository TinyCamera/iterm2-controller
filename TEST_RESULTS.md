# iTerm2 Controller Plugin - Test Runbook

Functional tests for all 11 MCP tools. Run these manually against a live iTerm2 instance.

**Date last run:** 2026-02-16
**Plugin Version:** 0.1.0
**Score:** 33/33 passed (100%)

## Known Issues

All previously tracked issues have been fixed:

| # | Title | Link | Status |
|---|-------|------|--------|
| 1 | `name` param ignored in `iterm_new_tab` and `iterm_split_pane` | [#1](https://github.com/TinyCamera/iterm2-controller/issues/1) | Fixed |
| 2 | `command` param ignored in `iterm_new_tab` | [#2](https://github.com/TinyCamera/iterm2-controller/issues/2) | Fixed |
| 3 | Fuzzy matching silently misdirects `focus_session`, `read_output`, `watch_session` | [#3](https://github.com/TinyCamera/iterm2-controller/issues/3) | Fixed |
| 4 | `iterm_send_keys` accepts invalid key names without error | [#4](https://github.com/TinyCamera/iterm2-controller/issues/4) | Fixed |

---

## Setup

Before running tests, you need one iTerm2 window open. Note the TTY of your current
session (run `tty` in the terminal). All `$SESSION_ID` and `$TTY` placeholders below
should be replaced with real values from your environment as you go.

**Cleanup:** After testing, close all tabs/panes you created except the original.

---

## Test 1.1: List all sessions

**Tool:** `iterm_list_sessions` (no args)

**Expected:** JSON array where each object has these fields:
- `session_id` (UUID string)
- `name` (string)
- `tty` (e.g. `/dev/ttys001`)
- `window_id` (string)
- `window_name` (string)
- `tab_index` (integer)
- `registered` (boolean)

**Last result:** PASS

---

## Test 2.1: Register current session

**Tool:** `iterm_register_session`
**Args:** `tty_path` = your current TTY (run `tty` to find it)

**Expected:** Response contains:
```json
{"status": "registered", "tty": "/dev/ttys001", "iterm_session_id": "...", "session_name": "..."}
```

**Last result:** PASS

---

## Test 2.2: Register invalid TTY

**Tool:** `iterm_register_session`
**Args:** `tty_path` = `/dev/ttys999`

**Expected:** Error response:
```json
{"error": "No iTerm2 session found with tty /dev/ttys999. Make sure iTerm2 is running and the tty is correct."}
```

**Last result:** PASS

---

## Test 2.3: Re-register same TTY

**Tool:** `iterm_register_session`
**Args:** `tty_path` = same TTY as test 2.1

**Expected:** Same success response as 2.1, no error about duplicate registration.

**Last result:** PASS

---

## Test 1.2: List sessions shows registered flag

**Prereq:** Run after test 2.1.

**Tool:** `iterm_list_sessions` (no args)

**Expected:** The session you registered in 2.1 now shows `"registered": true`.

**Last result:** PASS

---

## Test 3.1: Find session by exact name

**Tool:** `iterm_get_session_by_name`
**Args:** `name` = the full name of an existing session from test 1.1 output

**Expected:** JSON array containing the matching session object.

**Last result:** PASS

---

## Test 3.2: Find session by partial name

**Tool:** `iterm_get_session_by_name`
**Args:** `name` = a substring of a session name (e.g. `"Plugin"` if session is named "iTerm2 Plugin Testing")

**Expected:** JSON array containing the matching session(s).

**Last result:** PASS

---

## Test 3.3: Find session with no match

**Tool:** `iterm_get_session_by_name`
**Args:** `name` = `"zzz_nonexistent_session_zzz"`

**Expected:** Error response:
```json
{"error": "No session matching 'zzz_nonexistent_session_zzz'."}
```

**Last result:** PASS

---

## Test 4.1: Create new tab (no args)

**Tool:** `iterm_new_tab` (no args)

**Expected:** Response contains `status: "created"`, `session_id`, and `tty`. A new tab appears in iTerm2.

**Save:** Note the `session_id` — you'll use it as `$TAB1_ID` in later tests.

**Last result:** PASS

---

## Test 4.2: Create new tab with name

**Tool:** `iterm_new_tab`
**Args:** `name` = `"test-tab"`

**Expected:** New tab created. Run `iterm_get_session_by_name(name="test-tab")` — it should find the session.

**Verify:** Also check `iterm_list_sessions` to see if the new session's name is "test-tab".

**Last result:** PASS

---

## Test 4.3: Create new tab with command

**Tool:** `iterm_new_tab`
**Args:** `command` = `"echo hello_from_new_tab"`

**Expected:** New tab created. Run `iterm_read_output(identifier=$NEW_SESSION_ID, lines=10)` — output should contain `hello_from_new_tab`.

**Last result:** PASS

---

## Test 4.4: Split pane vertically

**Tool:** `iterm_split_pane`
**Args:** `direction` = `"vertical"`

**Expected:** A new pane appears side-by-side. Response contains `status: "created"`, `direction: "vertical"`, `session_id`, `tty`.

**Save:** Note the `session_id` as `$VSPLIT_ID`.

**Last result:** PASS

---

## Test 4.5: Split pane horizontally

**Tool:** `iterm_split_pane`
**Args:** `direction` = `"horizontal"`

**Expected:** A new pane appears top/bottom. Response contains `direction: "horizontal"`.

**Last result:** PASS

---

## Test 4.6: Split pane with name

**Tool:** `iterm_split_pane`
**Args:** `name` = `"test-split"`

**Expected:** New pane created. Run `iterm_get_session_by_name(name="test-split")` — it should find the session.

**Last result:** PASS

---

## Test 4.7: Split pane with invalid direction

**Tool:** `iterm_split_pane`
**Args:** `direction` = `"diagonal"`

**Expected:** Error response:
```json
{"error": "direction must be 'vertical' or 'horizontal'."}
```

**Last result:** PASS

---

## Test 5.1: Rename session

**Prereq:** Use `$TAB1_ID` from test 4.1.

**Tool:** `iterm_set_session_name`
**Args:** `identifier` = `$TAB1_ID`, `new_name` = `"renamed-test-tab"`

**Expected:**
```json
{"status": "renamed", "session_id": "...", "old_name": "~ (-zsh)", "new_name": "renamed-test-tab"}
```

**Last result:** PASS

---

## Test 5.2: Focus session by ID

**Tool:** `iterm_focus_session`
**Args:** `identifier` = `$TAB1_ID`

**Expected:** That tab/pane comes to the foreground. Response contains `status: "focused"`.

**Last result:** PASS

---

## Test 5.3: Focus session by name

**Prereq:** Session was renamed in test 5.1.

**Tool:** `iterm_focus_session`
**Args:** `identifier` = `"renamed-test-tab"`

**Expected:** Same session is focused. Response contains the matching session_id.

**Last result:** PASS

---

## Test 5.4: Focus nonexistent session

**Tool:** `iterm_focus_session`
**Args:** `identifier` = `"nonexistent_xyz"`

**Expected:** Error indicating no session was found.

**Last result:** PASS

---

## Test 6.1: Send simple command

**Prereq:** Use `$TAB1_ID` from test 4.1.

**Tool:** `iterm_send_command`
**Args:** `identifier` = `$TAB1_ID`, `command` = `"echo test123"`

**Expected:** Response has `status: "sent"`. Then run `iterm_read_output(identifier=$TAB1_ID, lines=5)` and verify the output contains `test123`.

**Last result:** PASS

---

## Test 6.2: Send command with special characters

**Tool:** `iterm_send_command`
**Args:** `identifier` = `$TAB1_ID`, `command` = `"echo 'hello \"world\"'"`

**Expected:** Response has `status: "sent"`. Read output — it should contain `hello "world"` with quotes preserved.

**Last result:** PASS

---

## Test 6.3: Send ctrl+c to interrupt

**Step 1:** `iterm_send_command(identifier=$TAB1_ID, command="sleep 30")`
**Step 2:** `iterm_send_keys(identifier=$TAB1_ID, keys="ctrl+c")`
**Step 3:** `iterm_read_output(identifier=$TAB1_ID, lines=5)`

**Expected:** Output shows `^C` and a new prompt — the sleep was interrupted.

**Last result:** PASS

---

## Test 6.4: Send multiple keys

**Tool:** `iterm_send_keys`
**Args:** `identifier` = `$TAB1_ID`, `keys` = `"up up enter"`

**Expected:** Response has `status: "sent"`. The "up up" recalls shell history, "enter" executes it.

**Last result:** PASS

---

## Test 6.5: Send arrow keys

**Tool:** `iterm_send_keys`
**Args:** `identifier` = `$TAB1_ID`, `keys` = `"left right"`

**Expected:** Response has `status: "sent"`.

**Last result:** PASS

---

## Test 6.6: Send invalid key name

**Tool:** `iterm_send_keys`
**Args:** `identifier` = `$TAB1_ID`, `keys` = `"ctrl+invalid"`

**Expected:** Error response listing valid key names.

**Last result:** PASS

---

## Test 7.1: Read output

**Prereq:** Run `iterm_send_command(identifier=$TAB1_ID, command="echo READ_TEST")` first.

**Tool:** `iterm_read_output`
**Args:** `identifier` = `$TAB1_ID`

**Expected:** Response contains `session_id`, `name`, `line_count`, and `output` field with `READ_TEST` in it.

**Last result:** PASS

---

## Test 7.2: Read output with line limit

**Tool:** `iterm_read_output`
**Args:** `identifier` = `$TAB1_ID`, `lines` = `5`

**Expected:** `line_count` is 5. Only the last 5 lines of output are returned.

**Last result:** PASS

---

## Test 7.3: Watch session (first call)

**Tool:** `iterm_watch_session`
**Args:** `identifier` = `$TAB1_ID`

**Expected:** Response contains:
- `new_output` — the full visible buffer
- `is_first_read: true`
- `new_line_count` — total number of visible lines

**Last result:** PASS

---

## Test 7.4: Watch session (subsequent call)

**Step 1:** `iterm_send_command(identifier=$TAB1_ID, command="echo WATCH_DELTA")`
**Step 2:** `iterm_watch_session(identifier=$TAB1_ID)`

**Expected:** Response contains:
- `new_output` — only lines since the previous watch call, including `WATCH_DELTA`
- `is_first_read: false`
- `new_line_count` — a small number (just the new lines)

**Last result:** PASS

---

## Test 8.1: E2E — Create tab, run command, read output

**Step 1:** `iterm_new_tab()` — save the `session_id` as `$E2E_ID`
**Step 2:** `iterm_send_command(identifier=$E2E_ID, command="echo E2E_TEST")`
**Step 3:** `iterm_read_output(identifier=$E2E_ID, lines=10)`

**Expected:** Step 3 output contains `E2E_TEST`.

**Last result:** PASS

---

## Test 8.2: E2E — Split pane, watch for new output

**Step 1:** `iterm_split_pane(direction="horizontal")` — save `session_id` as `$SPLIT_ID`
**Step 2:** `iterm_watch_session(identifier=$SPLIT_ID)` — baseline read
**Step 3:** `iterm_send_command(identifier=$SPLIT_ID, command="echo WATCH_TEST")`
**Step 4:** `iterm_watch_session(identifier=$SPLIT_ID)`

**Expected:** Step 4 returns only new output containing `WATCH_TEST`, with `is_first_read: false`.

**Last result:** PASS

---

## Test 8.3: E2E — Create tab, rename, find by name

**Step 1:** `iterm_new_tab()` — save `session_id` as `$RENAME_ID`
**Step 2:** `iterm_set_session_name(identifier=$RENAME_ID, new_name="unique-test-name")`
**Step 3:** `iterm_get_session_by_name(name="unique-test")`

**Expected:** Step 3 returns an array that includes the session from step 1 (partial match on "unique-test").

**Last result:** PASS

---

## Test 9.1: Send empty command

**Tool:** `iterm_send_command`
**Args:** `identifier` = `$TAB1_ID`, `command` = `""`

**Expected:** No crash. Response has `status: "sent"`. Effectively just presses Enter.

**Last result:** PASS

---

## Test 9.2: Read output from invalid session ID

**Tool:** `iterm_read_output`
**Args:** `identifier` = `"INVALID-SESSION-ID-12345"`

**Expected:** Error response indicating no matching session.

**Last result:** PASS

---

## Test 9.3: Send command to invalid session

**Tool:** `iterm_send_command`
**Args:** `identifier` = `"INVALID-SESSION-ID-12345"`, `command` = `"echo SHOULD_NOT_RUN"`

**Expected:** Error listing available sessions:
```
No session found matching 'INVALID-SESSION-ID-12345'. Available sessions: [...]
```

**Last result:** PASS

---

## Test 9.4: Create tab in nonexistent window

**Tool:** `iterm_new_tab`
**Args:** `window_identifier` = `"NONEXISTENT_WINDOW_99999"`

**Expected:** Error listing available sessions:
```
No session found matching 'NONEXISTENT_WINDOW_99999'. Available sessions: [...]
```

**Last result:** PASS

---

## Tool Coverage

All 11 MCP tools exercised:

| Tool | Tests |
|------|-------|
| `iterm_list_sessions` | 1.1, 1.2 |
| `iterm_register_session` | 2.1, 2.2, 2.3 |
| `iterm_get_session_by_name` | 3.1, 3.2, 3.3 |
| `iterm_new_tab` | 4.1, 4.2, 4.3, 9.4 |
| `iterm_split_pane` | 4.4, 4.5, 4.6, 4.7 |
| `iterm_set_session_name` | 5.1 |
| `iterm_focus_session` | 5.2, 5.3, 5.4 |
| `iterm_send_command` | 6.1, 6.2, 9.1, 9.3 |
| `iterm_send_keys` | 6.3, 6.4, 6.5, 6.6 |
| `iterm_read_output` | 7.1, 7.2, 9.2 |
| `iterm_watch_session` | 7.3, 7.4 |
