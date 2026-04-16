from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def utc_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class RunState:
    post_ids: list[str] = field(default_factory=list)
    title_hashes: list[str] = field(default_factory=list)
    daily_counts: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunState:
        return cls(
            post_ids=list(d.get("post_ids") or []),
            title_hashes=list(d.get("title_hashes") or []),
            daily_counts={str(k): int(v) for k, v in (d.get("daily_counts") or {}).items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "post_ids": self.post_ids,
            "title_hashes": self.title_hashes,
            "daily_counts": self.daily_counts,
        }


def load_state(path: Path) -> RunState:
    if not path.exists():
        return RunState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return RunState.from_dict(data)
    except Exception as e:
        log.warning("State load failed %s: %s", path, e)
    return RunState()


def save_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def trim_state(state: RunState, max_ids: int) -> None:
    if len(state.post_ids) > max_ids:
        state.post_ids = state.post_ids[-max_ids:]
    if len(state.title_hashes) > max_ids:
        state.title_hashes = state.title_hashes[-max_ids:]
    keys = sorted(state.daily_counts.keys())[-14:]
    state.daily_counts = {k: state.daily_counts[k] for k in keys}


def daily_count(state: RunState) -> int:
    return state.daily_counts.get(utc_date_str(), 0)


def increment_daily(state: RunState) -> None:
    d = utc_date_str()
    state.daily_counts[d] = state.daily_counts.get(d, 0) + 1
