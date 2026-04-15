from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: handle_incident.py <source> <target> <probability>")
        return 1

    source = sys.argv[1]
    target = sys.argv[2]
    probability = sys.argv[3]

    record = {
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "target": target,
        "probability": probability,
        "action": "python_incident_handler_executed",
    }

    out_path = Path("models") / "incident_events.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"Incident handler executed for {source}->{target} (p={probability})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
