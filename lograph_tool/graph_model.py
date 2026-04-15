from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from .otel_ingest import EdgeEvent


@dataclass(frozen=True)
class GraphSnapshot:
    nodes: List[str]
    edge_weights: Dict[Tuple[int, int], int]
    out_neighbors: Dict[int, List[int]]
    in_degree: List[int]
    out_degree: List[int]


@dataclass(frozen=True)
class TrainedModel:
    node_to_index: Dict[str, int]
    embeddings: List[List[float]]
    weights: List[float]
    bias: float
    threshold: float


def build_snapshot(events: Sequence[EdgeEvent]) -> GraphSnapshot:
    nodes = sorted({e.source for e in events} | {e.target for e in events})
    node_to_idx = {name: idx for idx, name in enumerate(nodes)}

    edge_weights: Dict[Tuple[int, int], int] = defaultdict(int)
    for e in events:
        edge_weights[(node_to_idx[e.source], node_to_idx[e.target])] += 1

    out_neighbors: Dict[int, List[int]] = defaultdict(list)
    in_degree = [0] * len(nodes)
    out_degree = [0] * len(nodes)

    for (src, dst), _ in edge_weights.items():
        out_neighbors[src].append(dst)
        out_degree[src] += 1
        in_degree[dst] += 1

    return GraphSnapshot(
        nodes=nodes,
        edge_weights=dict(edge_weights),
        out_neighbors={k: sorted(v) for k, v in out_neighbors.items()},
        in_degree=in_degree,
        out_degree=out_degree,
    )


def _base_features(snapshot: GraphSnapshot) -> List[List[float]]:
    node_count = max(1, len(snapshot.nodes))
    feats: List[List[float]] = []
    for idx in range(len(snapshot.nodes)):
        feats.append([
            snapshot.in_degree[idx] / node_count,
            snapshot.out_degree[idx] / node_count,
            (snapshot.in_degree[idx] + snapshot.out_degree[idx]) / node_count,
            1.0,
        ])
    return feats


def _matvec_scale(v: Sequence[float], scale: float) -> List[float]:
    return [x * scale for x in v]


def _vec_add(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [x + y for x, y in zip(a, b)]


def _relu(v: Sequence[float]) -> List[float]:
    return [x if x > 0 else 0.0 for x in v]


def message_passing_embeddings(snapshot: GraphSnapshot, steps: int = 2, self_w: float = 0.7, neigh_w: float = 0.3) -> List[List[float]]:
    emb = _base_features(snapshot)
    for _ in range(max(1, steps)):
        next_emb: List[List[float]] = []
        for idx in range(len(snapshot.nodes)):
            neigh = snapshot.out_neighbors.get(idx, [])
            if neigh:
                acc = [0.0] * len(emb[0])
                for n in neigh:
                    acc = _vec_add(acc, emb[n])
                neigh_avg = [x / len(neigh) for x in acc]
            else:
                neigh_avg = [0.0] * len(emb[0])

            mixed = _vec_add(_matvec_scale(emb[idx], self_w), _matvec_scale(neigh_avg, neigh_w))
            next_emb.append(_relu(mixed))
        emb = next_emb
    return emb


def _pair_features(src_emb: Sequence[float], dst_emb: Sequence[float]) -> List[float]:
    dot = sum(a * b for a, b in zip(src_emb, dst_emb))
    src_norm = math.sqrt(sum(a * a for a in src_emb)) + 1e-9
    dst_norm = math.sqrt(sum(b * b for b in dst_emb)) + 1e-9
    cosine = dot / (src_norm * dst_norm)
    return [dot, cosine, abs(src_norm - dst_norm), 1.0]


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def train_link_predictor(snapshot: GraphSnapshot, steps: int, epochs: int, lr: float, negative_ratio: int, threshold: float) -> TrainedModel:
    if len(snapshot.nodes) < 2:
        raise ValueError("Not enough nodes to train model")

    emb = message_passing_embeddings(snapshot, steps=steps)
    positives = list(snapshot.edge_weights.keys())
    if not positives:
        raise ValueError("No edges available for training")

    all_pairs = {(i, j) for i in range(len(snapshot.nodes)) for j in range(len(snapshot.nodes)) if i != j}
    positive_set = set(positives)
    negatives_pool = [p for p in all_pairs if p not in positive_set]
    random.shuffle(negatives_pool)

    target_neg = min(len(negatives_pool), len(positives) * max(1, negative_ratio))
    negatives = negatives_pool[:target_neg]

    x: List[List[float]] = []
    y: List[int] = []
    for src, dst in positives:
        x.append(_pair_features(emb[src], emb[dst]))
        y.append(1)
    for src, dst in negatives:
        x.append(_pair_features(emb[src], emb[dst]))
        y.append(0)

    weights = [0.0] * len(x[0])
    bias = 0.0

    for _ in range(max(1, epochs)):
        grad_w = [0.0] * len(weights)
        grad_b = 0.0
        for row, label in zip(x, y):
            pred = _sigmoid(sum(w * v for w, v in zip(weights, row)) + bias)
            err = pred - label
            for i, v in enumerate(row):
                grad_w[i] += err * v
            grad_b += err

        n = len(x)
        for i in range(len(weights)):
            weights[i] -= lr * (grad_w[i] / n)
        bias -= lr * (grad_b / n)

    node_to_index = {name: idx for idx, name in enumerate(snapshot.nodes)}
    return TrainedModel(node_to_index=node_to_index, embeddings=emb, weights=weights, bias=bias, threshold=threshold)


def predict_edge_probability(model: TrainedModel, source: str, target: str) -> float:
    if source not in model.node_to_index or target not in model.node_to_index:
        return 0.0
    s = model.node_to_index[source]
    t = model.node_to_index[target]
    feat = _pair_features(model.embeddings[s], model.embeddings[t])
    return _sigmoid(sum(w * v for w, v in zip(model.weights, feat)) + model.bias)


def save_model(model: TrainedModel, model_path: Path) -> None:
    payload = {
        "node_to_index": model.node_to_index,
        "embeddings": model.embeddings,
        "weights": model.weights,
        "bias": model.bias,
        "threshold": model.threshold,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
