from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_CONFIG: Dict[str, Any] = {
    "telemetry": {
        "mode": "jsonl",
        "endpoint": "http://127.0.0.1:4318/v1/logs",
        "jsonl_path": "data/otel_logs.jsonl",
        "poll_seconds": 30,
        "lookback_seconds": 600,
    },
    "training": {
        "negative_ratio": 1,
        "epochs": 500,
        "learning_rate": 0.05,
        "message_passing_steps": 2,
        "embedding_size": 4,
        "anomaly_threshold": 0.25,
    },
    "actions": [
        {
            "name": "notify-low-probability-edge",
            "when": {
                "type": "low_link_probability",
                "threshold": 0.25,
            },
            "exec": {
                "command": "python",
                "args": ["scripts/handle_incident.py", "{source}", "{target}", "{probability}"],
                "timeout_seconds": 20,
            },
        }
    ],
}


@dataclass
class ToolConfig:
    telemetry: Dict[str, Any] = field(default_factory=dict)
    training: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _deep_merge(base[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: Path) -> ToolConfig:
    user_data: Dict[str, Any] = {}
    if config_path.exists():
        user_data = json.loads(config_path.read_text(encoding="utf-8"))

    merged = _deep_merge(DEFAULT_CONFIG, user_data)
    return ToolConfig(
        telemetry=merged.get("telemetry", {}),
        training=merged.get("training", {}),
        actions=merged.get("actions", []),
    )


def write_default_config(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        return
    config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
