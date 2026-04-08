"""
Advanced Negative Sampling (ANS) - Paper Section 3.4

Addresses class imbalance by weighting negative sample selection based on node degree.
This ensures the model learns from challenging, meaningful negative samples rather
than trivial non-connections.

Paper Reference: Eq. 6
    p(v) = dv^α / Σ(du^α)
    where α is tunable parameter controlling influence of node centrality
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from .otel_ingest import EdgeEvent


def compute_node_degrees(
    events: List[EdgeEvent],
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Compute in-degree and out-degree for each node.

    Args:
        events: List of EdgeEvent objects

    Returns:
        (out_degree, in_degree) dicts mapping service name → degree count
    """
    out_degree: Dict[str, int] = defaultdict(int)
    in_degree: Dict[str, int] = defaultdict(int)

    for event in events:
        out_degree[event.source] += 1
        in_degree[event.target] += 1

    return dict(out_degree), dict(in_degree)


def compute_degree_probabilities(
    nodes: List[str],
    degrees: Dict[str, int],
    alpha: float = 0.1,
) -> Dict[str, float]:
    """
    Compute sampling probability for each node based on degree.

    Paper: p(v) = dv^α / Σ(du^α)

    Args:
        nodes: List of all service names
        degrees: Mapping of service name → degree
        alpha: Tunable parameter (0.1 default). Higher α prioritizes hub nodes.

    Returns:
        Dict mapping service name → sampling probability (sum = 1.0)
    """
    if not nodes:
        return {}

    # Compute dv^α for each node
    powered_degrees = {
        node: (float(degrees.get(node, 0)) ** alpha) for node in nodes
    }

    # Normalize to probabilities
    total = sum(powered_degrees.values())
    if total == 0:
        # If all degrees are 0, use uniform distribution
        uniform_prob = 1.0 / len(nodes)
        return {node: uniform_prob for node in nodes}

    return {node: (pd / total) for node, pd in powered_degrees.items()}


def advanced_negative_sampling(
    positive_edges: Set[Tuple[str, str]],
    nodes: List[str],
    degree_probs: Dict[str, float],
    target_count: int | None = None,
    seed: int = 42,
) -> List[Tuple[str, str]]:
    """
    Generate negative samples (non-existent edges) weighted by node degree.

    Algorithm (Paper Section 3.4):
    1. For each potential negative edge:
       - Sample source node v with probability p(v) = dv^α
       - Sample destination randomly from all nodes
       - Reject if edge already exists (positive or previously sampled negative)
    2. Continue until target_count negatives collected

    Args:
        positive_edges: Set of (source, target) pairs that exist
        nodes: List of all service names
        degree_probs: Pre-computed degree probability distribution
        target_count: Number of negatives to generate (default: |positive_edges|)
        seed: Random seed for reproducibility

    Returns:
        List of (source, target) tuples representing non-existent edges

    Complexity: O(attempts) where attempts ≤ max_attempts to avoid infinite loops
    """
    if not nodes or not positive_edges:
        return []

    random.seed(seed)

    if target_count is None:
        target_count = len(positive_edges)

    negative_edges: Set[Tuple[str, str]] = set()
    excluded_edges = positive_edges.copy()

    # Max attempts = 50x target to avoid unbounded loops
    max_attempts = max(5000, target_count * 50)
    attempts = 0

    while len(negative_edges) < target_count and attempts < max_attempts:
        attempts += 1

        # Sample source with degree weighting
        src = random.choices(nodes, weights=[degree_probs[n] for n in nodes], k=1)[0]

        # Sample destination uniformly
        dst = random.choice(nodes)

        if src == dst:
            # Skip self-loops
            continue

        edge_pair = (src, dst)

        if edge_pair in excluded_edges:
            # Already exist or previously sampled
            continue

        negative_edges.add(edge_pair)
        excluded_edges.add(edge_pair)  # Exclude from future sampling

    return list(negative_edges)


def simple_negative_sampling(
    positive_edges: Set[Tuple[str, str]],
    nodes: List[str],
    target_ratio: float = 1.0,
    seed: int = 42,
) -> List[Tuple[str, str]]:
    """
    Generate negative samples with uniform probability (simpler baseline).

    Paper: "Simple Negative Sampling" for moderately imbalanced datasets
    Ns = {(vi, vj) | vi, vj ∈ V, (vi, vj) ∉ E}  with |Ns| ≈ |P|

    Args:
        positive_edges: Set of (source, target) pairs that exist
        nodes: List of all service names
        target_ratio: Ratio of negatives to positives (default: 1.0 for balanced)
        seed: Random seed for reproducibility

    Returns:
        List of (source, target) tuples representing non-existent edges
    """
    random.seed(seed)

    target_count = max(1, int(len(positive_edges) * target_ratio))
    negative_edges: Set[Tuple[str, str]] = set()
    excluded_edges = positive_edges.copy()

    max_attempts = max(5000, target_count * 50)
    attempts = 0

    while len(negative_edges) < target_count and attempts < max_attempts:
        attempts += 1

        src = random.choice(nodes)
        dst = random.choice(nodes)

        if src == dst:
            continue

        edge_pair = (src, dst)

        if edge_pair in excluded_edges:
            continue

        negative_edges.add(edge_pair)
        excluded_edges.add(edge_pair)

    return list(negative_edges)


def balance_samples(
    positive_edges: List[Tuple[str, str]],
    negative_edges: List[Tuple[str, str]],
    strategy: str = "advanced",
) -> Tuple[List[Tuple[str, str]], List[int]]:
    """
    Combine positive and negative samples and create labels.

    Args:
        positive_edges: List of existing edges
        negative_edges: List of non-existing edges
        strategy: "advanced", "simple", or "none" (determines sampling used)

    Returns:
        (samples, labels) where samples are (src, dst) and labels are 0/1
    """
    samples: List[Tuple[str, str]] = []
    labels: List[int] = []

    # Add positive samples (label = 1)
    for edge in positive_edges:
        samples.append(edge)
        labels.append(1)

    # Add negative samples (label = 0)
    for edge in negative_edges:
        samples.append(edge)
        labels.append(0)

    # Shuffle
    combined = list(zip(samples, labels))
    random.shuffle(combined)
    shuffled_samples, shuffled_labels = zip(*combined) if combined else ([], [])

    return list(shuffled_samples), list(shuffled_labels)


def get_sampling_statistics(
    positive_edges: List[Tuple[str, str]],
    negative_edges: List[Tuple[str, str]],
) -> Dict[str, float]:
    """
    Compute statistics about sampled dataset balance.

    Returns:
        Dict with keys: total_samples, positive_count, negative_count,
        imbalance_ratio, positive_ratio
    """
    total = len(positive_edges) + len(negative_edges)
    pos_count = len(positive_edges)
    neg_count = len(negative_edges)

    return {
        "total_samples": float(total),
        "positive_samples": float(pos_count),
        "negative_samples": float(neg_count),
        "imbalance_ratio": float(neg_count / max(1, pos_count)),
        "positive_ratio": float(pos_count / max(1, total)),
    }
