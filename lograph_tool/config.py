"""Configuration schema, defaults, and load/write helpers for LoGraph tool."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_CONFIG: Dict[str, Any] = {
    "setup": {
        "completed": False,
    },
    "telemetry": {
        "mode": "http",
        "endpoint": "",
        "jsonl_path": "",
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
        "failure_threshold": 0.75,
    },
    "actions": [],
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


def save_config_payload(config_path: Path, payload: Dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def is_setup_completed(config_path: Path) -> bool:
    if not config_path.exists():
        return False
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("setup", {}).get("completed", False))


def create_setup_payload(
    *,
    mode: str,
    jsonl_path: str,
    endpoint: str,
    incident_script: str = "",
    failure_script: str = "",
    poll_seconds: int = 30,
    lookback_seconds: int = 600,
) -> Dict[str, Any]:
    payload = _deep_merge(DEFAULT_CONFIG, {})
    payload["setup"] = {"completed": True}
    payload["telemetry"] = {
        "mode": mode,
        "endpoint": endpoint,
        "jsonl_path": jsonl_path,
        "poll_seconds": int(poll_seconds),
        "lookback_seconds": int(lookback_seconds),
    }
    payload["training"]["anomaly_threshold"] = float(payload["training"].get("anomaly_threshold", 0.25))
    payload["training"]["failure_threshold"] = float(payload["training"].get("failure_threshold", 0.75))
    actions: List[Dict[str, Any]] = []
    if incident_script.strip():
        actions.append(
            {
                "name": "gui-action",
                "when": {
                    "type": "low_link_probability",
                    "threshold": float(payload["training"]["anomaly_threshold"]),
                },
                "exec": {
                    "python_script": incident_script.strip(),
                    "args": ["{source}", "{target}", "{probability}"],
                    "timeout_seconds": 20,
                },
            }
        )
    if failure_script.strip():
        actions.append(
            {
                "name": "python-failure-handler",
                "when": {
                    "type": "high_failure_probability",
                    "threshold": float(payload["training"]["failure_threshold"]),
                },
                "exec": {
                    "python_script": failure_script.strip(),
                    "args": ["{source}", "{target}", "{failure_probability}", "{timestamp}"],
                    "timeout_seconds": 20,
                },
            }
        )
    payload["actions"] = actions
    return payload
