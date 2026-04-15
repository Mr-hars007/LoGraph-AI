"""Baseline trainer for lightweight link prediction on prepared graph data."""

from __future__ import annotations

import csv
import json
import math
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from main import PreparedGraphData, prepare_graph_data
from graph_builder import normalize_service_name


@dataclass(frozen=True)
class DatasetSplit:
    train_x: List[List[float]]
    train_y: List[int]
    test_x: List[List[float]]
    test_y: List[int]


@dataclass(frozen=True)
class TrainingResult:
    weights: List[float]
    bias: float
    feature_mean: List[float]
    feature_std: List[float]
    train_metrics: Dict[str, float]
    test_metrics: Dict[str, float]


def sigmoid(value: float) -> float:
    # Stable sigmoid for large positive/negative values.
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def build_node_maps(prepared: PreparedGraphData) -> tuple[Dict[int, List[float]], Dict[int, Dict[str, float]]]:
    feature_map = {idx: prepared.node_features[idx] for idx in range(len(prepared.node_features))}
    detail_map = {
        detail["index"]: {
            "in_degree": float(detail["in_degree"]),
            "out_degree": float(detail["out_degree"]),
            "in_weight": float(detail["in_weight"]),
            "out_weight": float(detail["out_weight"]),
        }
        for detail in prepared.node_details
    }
    return feature_map, detail_map


def pair_features(
    src_idx: int,
    dst_idx: int,
    feature_map: Dict[int, List[float]],
    detail_map: Dict[int, Dict[str, float]],
) -> List[float]:
    src_feat = feature_map[src_idx]
    dst_feat = feature_map[dst_idx]
    src_deg = detail_map[src_idx]
    dst_deg = detail_map[dst_idx]

    return [
        src_feat[0], src_feat[1], src_feat[2],
        dst_feat[0], dst_feat[1], dst_feat[2],
        abs(src_feat[0] - dst_feat[0]),
        abs(src_feat[1] - dst_feat[1]),
        abs(src_feat[2] - dst_feat[2]),
        src_deg["out_degree"],
        dst_deg["in_degree"],
        src_deg["out_weight"],
        dst_deg["in_weight"],
    ]


def generate_link_dataset(prepared: PreparedGraphData, seed: int = 7) -> tuple[List[List[float]], List[int]]:
    random.seed(seed)
    node_count = len(prepared.node_names)
    if node_count < 2:
        return [], []

    feature_map, detail_map = build_node_maps(prepared)

    positive_edges = {(e["source_index"], e["target_index"]) for e in prepared.edge_details}
    negatives: set[Tuple[int, int]] = set()

    # 1:1 negative sampling with positives for balanced training.
    target_negative_count = len(positive_edges)
    attempts = 0
    max_attempts = max(5000, target_negative_count * 50)

    while len(negatives) < target_negative_count and attempts < max_attempts:
        src = random.randrange(node_count)
        dst = random.randrange(node_count)
        attempts += 1
        if src == dst:
            continue
        pair = (src, dst)
        if pair in positive_edges or pair in negatives:
            continue
        negatives.add(pair)

    samples_x: List[List[float]] = []
    samples_y: List[int] = []

    for src, dst in positive_edges:
        samples_x.append(pair_features(src, dst, feature_map, detail_map))
        samples_y.append(1)

    for src, dst in negatives:
        samples_x.append(pair_features(src, dst, feature_map, detail_map))
        samples_y.append(0)

    combined = list(zip(samples_x, samples_y))
    random.shuffle(combined)
    shuffled_x, shuffled_y = zip(*combined)
    return list(shuffled_x), list(shuffled_y)


def train_test_split(samples_x: List[List[float]], samples_y: List[int], test_ratio: float = 0.3) -> DatasetSplit:
    size = len(samples_x)
    if size == 0:
        return DatasetSplit([], [], [], [])

    split_idx = max(1, int(size * (1.0 - test_ratio)))
    split_idx = min(split_idx, size - 1)

    return DatasetSplit(
        train_x=samples_x[:split_idx],
        train_y=samples_y[:split_idx],
        test_x=samples_x[split_idx:],
        test_y=samples_y[split_idx:],
    )


def compute_scaler(train_x: List[List[float]]) -> tuple[List[float], List[float]]:
    feature_count = len(train_x[0])
    means: List[float] = []
    stds: List[float] = []

    for feature_idx in range(feature_count):
        column = [row[feature_idx] for row in train_x]
        mean = sum(column) / len(column)
        variance = sum((v - mean) ** 2 for v in column) / len(column)
        std = math.sqrt(variance)
        means.append(mean)
        stds.append(std if std > 1e-9 else 1.0)

    return means, stds


def apply_scaler(samples_x: List[List[float]], means: List[float], stds: List[float]) -> List[List[float]]:
    normalized: List[List[float]] = []
    for row in samples_x:
        normalized.append([(val - mean) / std for val, mean, std in zip(row, means, stds)])
    return normalized


def evaluate(samples_x: List[List[float]], samples_y: List[int], weights: List[float], bias: float) -> Dict[str, float]:
    if not samples_x:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = fp = tn = fn = 0
    for row, label in zip(samples_x, samples_y):
        score = sigmoid(dot(weights, row) + bias)
        pred = 1 if score >= 0.5 else 0
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        else:
            fn += 1

    accuracy = (tp + tn) / max(1, (tp + tn + fp + fn))
    precision = tp / max(1, (tp + fp))
    recall = tp / max(1, (tp + fn))
    f1 = 2 * precision * recall / max(1e-9, (precision + recall))

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def train_logistic_regression(
    train_x: List[List[float]],
    train_y: List[int],
    test_x: List[List[float]],
    test_y: List[int],
    learning_rate: float = 0.06,
    epochs: int = 800,
    l2_penalty: float = 0.0005,
) -> TrainingResult:
    feature_mean, feature_std = compute_scaler(train_x)
    train_x_n = apply_scaler(train_x, feature_mean, feature_std)
    test_x_n = apply_scaler(test_x, feature_mean, feature_std)

    weights = [0.0 for _ in range(len(train_x_n[0]))]
    bias = 0.0

    for _ in range(epochs):
        grad_w = [0.0 for _ in weights]
        grad_b = 0.0

        for row, label in zip(train_x_n, train_y):
            pred = sigmoid(dot(weights, row) + bias)
            error = pred - label
            for i, value in enumerate(row):
                grad_w[i] += error * value
            grad_b += error

        batch_size = max(1, len(train_x_n))
        for i in range(len(weights)):
            grad = (grad_w[i] / batch_size) + (l2_penalty * weights[i])
            weights[i] -= learning_rate * grad
        bias -= learning_rate * (grad_b / batch_size)

    train_metrics = evaluate(train_x_n, train_y, weights, bias)
    test_metrics = evaluate(test_x_n, test_y, weights, bias)

    return TrainingResult(
        weights=weights,
        bias=bias,
        feature_mean=feature_mean,
        feature_std=feature_std,
        train_metrics=train_metrics,
        test_metrics=test_metrics,
    )


def save_model(result: TrainingResult, model_path: Path) -> None:
    payload = {
        "model_type": "logistic_link_predictor_baseline",
        "feature_schema": [
            "src_cpu_last",
            "src_cpu_mean",
            "src_cpu_rate",
            "dst_cpu_last",
            "dst_cpu_mean",
            "dst_cpu_rate",
            "abs_cpu_last_diff",
            "abs_cpu_mean_diff",
            "abs_cpu_rate_diff",
            "src_out_degree",
            "dst_in_degree",
            "src_out_weight",
            "dst_in_weight",
        ],
        "weights": result.weights,
        "bias": result.bias,
        "feature_mean": result.feature_mean,
        "feature_std": result.feature_std,
        "train_metrics": result.train_metrics,
        "test_metrics": result.test_metrics,
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def discover_default_rpc_files(data_dir: Path) -> List[Path]:
    rpc_files = sorted(data_dir.glob("*_ms_rpc_map.csv"))
    sample = data_dir / "sample.csv"
    if sample.exists():
        rpc_files.append(sample)
    return rpc_files


def _load_pairs(csv_path: Path) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, skipinitialspace=True)
        for row in reader:
            if len(row) < 2:
                continue

            left = str(row[0]).strip()
            right = str(row[1]).strip()

            # Skip simple header rows if present.
            if left.lower() == "source" and right.lower() == "target":
                continue

            source = normalize_service_name(left)
            target = normalize_service_name(right)
            if source and target:
                pairs.append((source, target))
    return pairs


def build_temp_merged_rpc_csv(rpc_files: List[Path]) -> Path:
    all_pairs: List[Tuple[str, str]] = []
    for rpc_file in rpc_files:
        if rpc_file.exists():
            all_pairs.extend(_load_pairs(rpc_file))

    if not all_pairs:
        raise ValueError("No valid source-target pairs found in provided RPC files.")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tmp:
        writer = csv.writer(tmp)
        for source, target in all_pairs:
            writer.writerow([source, target])
        return Path(tmp.name)


def train_with_current_data(
    rpc_map_csv: Path,
    metrics_dir: Path,
    model_output_path: Path,
) -> Dict[str, float]:
    prepared = prepare_graph_data(rpc_map_csv, metrics_dir)
    samples_x, samples_y = generate_link_dataset(prepared)

    if len(samples_x) < 6:
        raise ValueError("Not enough training samples generated. Add more trace edges for training.")

    split = train_test_split(samples_x, samples_y, test_ratio=0.3)
    result = train_logistic_regression(split.train_x, split.train_y, split.test_x, split.test_y)
    save_model(result, model_output_path)

    return {
        "samples": float(len(samples_x)),
        "train_samples": float(len(split.train_x)),
        "test_samples": float(len(split.test_x)),
        "train_accuracy": result.train_metrics["accuracy"],
        "test_accuracy": result.test_metrics["accuracy"],
        "test_f1": result.test_metrics["f1"],
    }


def train_with_rpc_files(
    rpc_files: List[Path],
    metrics_dir: Path,
    model_output_path: Path,
) -> Dict[str, float]:
    temp_csv = build_temp_merged_rpc_csv(rpc_files)
    try:
        return train_with_current_data(temp_csv, metrics_dir, model_output_path)
    finally:
        if temp_csv.exists():
            temp_csv.unlink()


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    rpc_files = discover_default_rpc_files(data_dir)
    metrics_dir = project_root / "data"
    model_output_path = project_root / "models" / "link_predictor_baseline.json"

    summary = train_with_rpc_files(rpc_files, metrics_dir, model_output_path)

    print("Training completed")
    print(f"- rpc files used: {len(rpc_files)}")
    print(f"- samples: {int(summary['samples'])}")
    print(f"- train samples: {int(summary['train_samples'])}")
    print(f"- test samples: {int(summary['test_samples'])}")
    print(f"- train accuracy: {summary['train_accuracy']:.4f}")
    print(f"- test accuracy: {summary['test_accuracy']:.4f}")
    print(f"- test f1: {summary['test_f1']:.4f}")
    print(f"- model saved to: {model_output_path}")


if __name__ == "__main__":
    main()
