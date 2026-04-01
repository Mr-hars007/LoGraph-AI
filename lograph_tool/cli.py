from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import List

from .automation import evaluate_and_trigger
from .config import load_config, write_default_config
from .graph_model import build_snapshot, save_model, train_link_predictor
from .otel_ingest import EdgeEvent, fetch_from_jsonl, fetch_from_otel_http, filter_by_lookback


def _load_events(config_path: Path) -> List[EdgeEvent]:
    cfg = load_config(config_path)
    telemetry = cfg.telemetry
    mode = str(telemetry.get("mode", "jsonl")).lower()
    lookback = int(telemetry.get("lookback_seconds", 600))

    if mode == "http":
        endpoint = str(telemetry.get("endpoint", "")).strip()
        events = fetch_from_otel_http(endpoint) if endpoint else []
    else:
        jsonl_rel = str(telemetry.get("jsonl_path", "data/otel_logs.jsonl"))
        jsonl_path = config_path.parent / jsonl_rel
        events = fetch_from_jsonl(jsonl_path)

    return filter_by_lookback(events, lookback)


def run_once(config_path: Path, model_path: Path) -> None:
    cfg = load_config(config_path)
    events = _load_events(config_path)
    if not events:
        print("No events fetched from telemetry source")
        return

    train_cfg = cfg.training
    snapshot = build_snapshot(events)
    model = train_link_predictor(
        snapshot=snapshot,
        steps=int(train_cfg.get("message_passing_steps", 2)),
        epochs=int(train_cfg.get("epochs", 500)),
        lr=float(train_cfg.get("learning_rate", 0.05)),
        negative_ratio=int(train_cfg.get("negative_ratio", 1)),
        threshold=float(train_cfg.get("anomaly_threshold", 0.25)),
    )
    save_model(model, model_path)

    triggered = evaluate_and_trigger(events, model, cfg.actions)

    print("Run completed")
    print(f"- events: {len(events)}")
    print(f"- nodes: {len(snapshot.nodes)}")
    print(f"- weighted edges: {sum(snapshot.edge_weights.values())}")
    print(f"- model: {model_path}")
    print(f"- triggered actions: {len(triggered)}")
    if triggered:
        print(json.dumps([t.__dict__ for t in triggered], indent=2))


def run_monitor(config_path: Path, model_path: Path) -> None:
    cfg = load_config(config_path)
    poll = int(cfg.telemetry.get("poll_seconds", 30))
    print(f"Monitoring telemetry every {poll}s")
    while True:
        run_once(config_path, model_path)
        time.sleep(max(1, poll))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoGraph deploy-and-use automation tool")
    parser.add_argument("command", choices=["init", "run", "monitor"], help="Tool command")
    parser.add_argument("--config", default="lograph-tool.json", help="Path to tool config JSON")
    parser.add_argument("--model", default="models/lograph_tool_model.json", help="Path to output model JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    model_path = Path(args.model).resolve()

    if args.command == "init":
        write_default_config(config_path)
        print(f"Config ready at {config_path}")
        return

    if not config_path.exists():
        write_default_config(config_path)

    if args.command == "run":
        run_once(config_path, model_path)
        return

    run_monitor(config_path, model_path)


if __name__ == "__main__":
    main()
