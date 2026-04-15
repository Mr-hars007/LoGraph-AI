"""Utilities for loading RPC maps and constructing a weighted service graph."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass(frozen=True)
class WeightedEdge:
	source: str
	target: str
	call_count: int


@dataclass(frozen=True)
class ServiceGraph:
	nodes: List[str]
	edges: List[WeightedEdge]


def _strip_parenthetical(text: str) -> str:
	return text.split("(", 1)[0].strip()


def normalize_service_name(raw_name: str) -> str:
	"""Map raw trace labels to canonical service names used as graph nodes."""
	cleaned = _strip_parenthetical(str(raw_name).strip())
	if "_" in cleaned:
		cleaned = cleaned.split("_", 1)[0].strip()
	return cleaned


def load_rpc_map(csv_path: str | Path) -> List[Tuple[str, str]]:
	"""Load service interaction mapping and return normalized source-target pairs."""
	path = Path(csv_path)
	if not path.exists():
		raise FileNotFoundError(f"RPC map not found: {path}")

	pairs: List[Tuple[str, str]] = []
	with path.open("r", encoding="utf-8", newline="") as handle:
		reader = csv.reader(handle, skipinitialspace=True)
		for row in reader:
			if len(row) < 2:
				continue
			source = normalize_service_name(row[0])
			target = normalize_service_name(row[1])
			if source and target:
				pairs.append((source, target))

	return pairs


def build_interaction_graph(edge_pairs: List[Tuple[str, str]]) -> ServiceGraph:
	"""Create a directed service graph and aggregate repeated calls as edge weights."""
	counts = Counter(edge_pairs)
	edges = [
		WeightedEdge(source=source, target=target, call_count=count)
		for (source, target), count in sorted(counts.items())
	]

	node_set = set()
	for edge in edges:
		node_set.add(edge.source)
		node_set.add(edge.target)

	return ServiceGraph(nodes=sorted(node_set), edges=edges)


def load_and_build_graph(csv_path: str | Path) -> ServiceGraph:
	edge_pairs = load_rpc_map(csv_path)
	return build_interaction_graph(edge_pairs)
