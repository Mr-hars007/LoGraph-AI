"""Default user action script executed for high failure-probability triggers.

Appends triggered events to models/failure_events.jsonl for later inspection.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 5:
        print("Usage: handle_failure.py <source> <target> <failure_probability> <timestamp>")
        return 1

    source = sys.argv[1]
    target = sys.argv[2]
    failure_probability = sys.argv[3]
    event_timestamp = sys.argv[4]

    record = {
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "target": target,
        "failure_probability": failure_probability,
        "event_timestamp": event_timestamp,
        "action": "python_failure_handler_executed",
    }

    out_path = Path("models") / "failure_events.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"Failure handler executed for {source}->{target} (p_fail={failure_probability})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
