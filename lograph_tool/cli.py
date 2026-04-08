"""Command-line execution flow for telemetry fetch, training, and triggering."""

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
from .reset import reset_generated_data


def _compute_classification_metrics(y_true: List[int], y_pred_scores: List[float], threshold: float) -> dict:
    y_pred = [1 if s >= threshold else 0 for s in y_pred_scores]
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    accuracy = (tp + tn) / max(1, len(y_true))
    precision = tp / max(1, (tp + fp))
    recall = tp / max(1, (tp + fn))
    f1 = 0.0 if (precision + recall) == 0 else (2.0 * precision * recall) / (precision + recall)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _save_baseline_from_logs(snapshot, model, output_path: Path) -> None:
    # Features correspond to graph_model._pair_features
    feature_schema = [
        "emb_dot",
        "emb_cosine",
        "emb_norm_abs_diff",
        "bias_term",
    ]

    positives = list(snapshot.edge_weights.keys())
    all_pairs = [(i, j) for i in range(len(snapshot.nodes)) for j in range(len(snapshot.nodes)) if i != j]
    positive_set = set(positives)
    negatives_pool = [p for p in all_pairs if p not in positive_set]
    negatives = negatives_pool[: len(positives)]

    rows: List[List[float]] = []
    y_true: List[int] = []
    y_scores: List[float] = []

    for src, dst in positives:
        src_emb = model.embeddings[src]
        dst_emb = model.embeddings[dst]
        dot = sum(a * b for a, b in zip(src_emb, dst_emb))
        src_norm = sum(a * a for a in src_emb) ** 0.5
        dst_norm = sum(b * b for b in dst_emb) ** 0.5
        cosine = 0.0 if src_norm == 0 or dst_norm == 0 else dot / (src_norm * dst_norm)
        row = [dot, cosine, abs(src_norm - dst_norm), 1.0]
        score = 1.0 / (1.0 + (2.718281828459045 ** (-(sum(w * v for w, v in zip(model.weights, row)) + model.bias))))
        rows.append(row)
        y_true.append(1)
        y_scores.append(score)

    for src, dst in negatives:
        src_emb = model.embeddings[src]
        dst_emb = model.embeddings[dst]
        dot = sum(a * b for a, b in zip(src_emb, dst_emb))
        src_norm = sum(a * a for a in src_emb) ** 0.5
        dst_norm = sum(b * b for b in dst_emb) ** 0.5
        cosine = 0.0 if src_norm == 0 or dst_norm == 0 else dot / (src_norm * dst_norm)
        row = [dot, cosine, abs(src_norm - dst_norm), 1.0]
        score = 1.0 / (1.0 + (2.718281828459045 ** (-(sum(w * v for w, v in zip(model.weights, row)) + model.bias))))
        rows.append(row)
        y_true.append(0)
        y_scores.append(score)

    if rows:
        cols = list(zip(*rows))
        means = [sum(c) / len(c) for c in cols]
        stds = []
        for i, c in enumerate(cols):
            m = means[i]
            var = sum((x - m) ** 2 for x in c) / len(c)
            s = var ** 0.5
            stds.append(s if s > 0 else 1.0)
    else:
        means = [0.0, 0.0, 0.0, 1.0]
        stds = [1.0, 1.0, 1.0, 1.0]

    metrics = _compute_classification_metrics(y_true, y_scores, model.threshold)
    payload = {
        "model_type": "logistic_link_predictor_baseline",
        "source": "otel_logs_runtime",
        "feature_schema": feature_schema,
        "weights": model.weights,
        "bias": model.bias,
        "feature_mean": means,
        "feature_std": stds,
        "train_metrics": metrics,
        "test_metrics": metrics,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_events(config_path: Path) -> List[EdgeEvent]:
    cfg = load_config(config_path)
    telemetry = cfg.telemetry
    mode = str(telemetry["mode"]).lower()
    lookback = int(telemetry["lookback_seconds"])

    if mode == "http":
        endpoint = str(telemetry["endpoint"]).strip()
        events = fetch_from_otel_http(endpoint) if endpoint else []
    else:
        jsonl_rel = str(telemetry["jsonl_path"])
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
    _save_baseline_from_logs(snapshot, model, config_path.parent / "models" / "link_predictor_baseline.json")

    triggered = evaluate_and_trigger(events, model, cfg.actions)

    print("Run completed")
    print(f"- events: {len(events)}")
    print(f"- nodes: {len(snapshot.nodes)}")
    print(f"- weighted edges: {sum(snapshot.edge_weights.values())}")
    print(f"- model: {model_path}")
    print(f"- baseline: {config_path.parent / 'models' / 'link_predictor_baseline.json'}")
    print(f"- triggered actions: {len(triggered)}")
    if triggered:
        print(json.dumps([t.__dict__ for t in triggered], indent=2))


def run_monitor(config_path: Path, model_path: Path) -> None:
    cfg = load_config(config_path)
    poll = int(cfg.telemetry["poll_seconds"])
    print(f"Monitoring telemetry every {poll}s")
    while True:
        run_once(config_path, model_path)
        time.sleep(max(1, poll))


def run_reset(config_path: Path, model_path: Path) -> None:
    summary = reset_generated_data(config_path.parent, model_path)
    print("Reset completed")
    print(f"- deleted files: {summary['deleted_count']}")
    if summary["errors"]:
        print("- errors:")
        for item in summary["errors"]:
            print(f"  - {item}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoGraph deploy-and-use automation tool")
    parser.add_argument("command", choices=["init", "run", "monitor", "reset"], help="Tool command")
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

    if args.command == "reset":
        run_reset(config_path, model_path)
        return

    run_monitor(config_path, model_path)


if __name__ == "__main__":
    main()
