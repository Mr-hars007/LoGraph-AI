"""Interactive first-run setup wizard for deployable LoGraph usage.

Collects minimal input (local JSONL vs remote HTTP telemetry), writes a ready
config, and can immediately start one-shot or monitor execution.
"""

from __future__ import annotations

from pathlib import Path

from .cli import run_monitor, run_once
from .config import DEFAULT_CONFIG, create_setup_payload, save_config_payload


def _ask(prompt: str, default: str) -> str:
    text = input(f"{prompt} [{default}]: ").strip()
    return text or default


def run_setup_wizard_cli(config_path: Path, model_path: Path, *, start_command: str = "run") -> None:
    print("LoGraph Setup Wizard")
    print("Select telemetry source:")
    print("1) Local JSONL")
    print("2) Remote HTTP (OTLP endpoint)")

    choice = _ask("Enter choice", "1")
    mode = "jsonl" if choice != "2" else "http"

    telemetry_defaults = DEFAULT_CONFIG.get("telemetry", {})
    default_jsonl = str(telemetry_defaults.get("jsonl_path", ""))
    default_endpoint = str(telemetry_defaults.get("endpoint", ""))
    default_poll = str(telemetry_defaults.get("poll_seconds", 30))
    default_lookback = str(telemetry_defaults.get("lookback_seconds", 600))

    if mode == "jsonl":
        jsonl_path = _ask("JSONL path", default_jsonl)
        endpoint = ""
    else:
        endpoint = _ask("OTLP HTTP endpoint", default_endpoint)
        jsonl_path = ""

    incident_script = _ask("Incident handler script path (optional)", "")
    failure_script = _ask("Failure handler script path (optional)", "")

    poll_seconds = int(_ask("Poll interval seconds", default_poll))
    lookback_seconds = int(_ask("Lookback seconds", default_lookback))

    payload = create_setup_payload(
        mode=mode,
        jsonl_path=jsonl_path,
        endpoint=endpoint,
        incident_script=incident_script,
        failure_script=failure_script,
        poll_seconds=poll_seconds,
        lookback_seconds=lookback_seconds,
    )
    save_config_payload(config_path, payload)

    print(f"Setup complete. Config saved: {config_path}")
    print(f"Model output path: {model_path}")

    if start_command == "monitor":
        print("Starting monitor mode...")
        run_monitor(config_path, model_path)
        return

    print("Running one-shot mode...")
    run_once(config_path, model_path)
