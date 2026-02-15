"""Session state persistence and resolution."""

import json
from difflib import SequenceMatcher
from pathlib import Path

from .applescript import list_all_sessions

SESSION_FILE = Path("/tmp/iterm2-mcp-sessions.json")


def load_state() -> dict:
    """Load the registered-sessions state file."""
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"sessions": {}}


def save_state(state: dict) -> None:
    """Write the registered-sessions state file."""
    SESSION_FILE.write_text(json.dumps(state, indent=2))


def fuzzy_match(query: str, candidates: list[dict], key: str = "name") -> list[dict]:
    """Return candidates sorted by fuzzy similarity to *query*."""
    scored = []
    q = query.lower()
    for c in candidates:
        val = (c.get(key) or "").lower()
        ratio = SequenceMatcher(None, q, val).ratio()
        if q in val:
            ratio += 0.4
        scored.append((ratio, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for r, c in scored if r > 0.25]


async def resolve_session(identifier: str) -> dict:
    """Resolve a session_id, tty path, or name to a session dict.

    Raises RuntimeError if nothing matches.
    """
    all_sessions = await list_all_sessions()

    for s in all_sessions:
        if s["session_id"] == identifier:
            return s

    for s in all_sessions:
        if s["tty"] == identifier:
            return s

    matches = fuzzy_match(identifier, all_sessions)
    if matches:
        return matches[0]

    raise RuntimeError(
        f"No session found matching '{identifier}'. "
        f"Available sessions: {[s['name'] for s in all_sessions]}"
    )
