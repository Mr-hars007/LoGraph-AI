"""Loads CPU metric streams and derives per-service feature vectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

CPU_SUFFIX = "_container_cpu_usage_seconds_total"


def _to_points(metric_payload: list[list[float | str]]) -> list[tuple[float, float]]:
	points: list[tuple[float, float]] = []
	for row in metric_payload:
		if not isinstance(row, list) or len(row) != 2:
			continue
		try:
			ts = float(row[0])
			val = float(row[1])
			points.append((ts, val))
		except (TypeError, ValueError):
			continue

	points.sort(key=lambda item: item[0])
	return points


def _compute_cpu_features(points: list[tuple[float, float]]) -> Dict[str, float]:
	if not points:
		return {"cpu_last": 0.0, "cpu_mean": 0.0, "cpu_rate": 0.0}

	values = [value for _, value in points]
	last = float(values[-1])
	mean = float(sum(values) / len(values))

	start_t = points[0][0]
	end_t = points[-1][0]
	start_v = points[0][1]
	end_v = points[-1][1]

	# Counter slope gives average CPU-seconds consumed per second over the window.
	duration = max(end_t - start_t, 1e-9)
	rate = (end_v - start_v) / duration

	return {"cpu_last": last, "cpu_mean": mean, "cpu_rate": float(rate)}


def load_cpu_metrics(metrics_dir: str | Path) -> Dict[str, Dict[str, float]]:
	"""Load all *_container_cpu_usage_seconds_total files in a directory."""
	root = Path(metrics_dir)
	if not root.exists():
		raise FileNotFoundError(f"Metrics directory not found: {root}")

	features_by_service: Dict[str, Dict[str, float]] = {}
	for metric_file in root.glob(f"*{CPU_SUFFIX}"):
		service_name = metric_file.name[: -len(CPU_SUFFIX)]
		try:
			payload = json.loads(metric_file.read_text(encoding="utf-8"))
			points = _to_points(payload)
			features_by_service[service_name] = _compute_cpu_features(points)
		except (json.JSONDecodeError, OSError, ValueError, TypeError):
			# Keep the pipeline fault-tolerant if one metric file is malformed.
			continue

	return features_by_service


def attach_cpu_features(
	graph,
	features_by_service: Dict[str, Dict[str, float]],
	*,
	fill_value: float = 0.0,
):
	"""Attach CPU features to each node in-place with safe defaults."""
	for node in graph.nodes:
		node_features = features_by_service.get(node, {})
		graph.nodes[node]["cpu_last"] = float(node_features.get("cpu_last", fill_value))
		graph.nodes[node]["cpu_mean"] = float(node_features.get("cpu_mean", fill_value))
		graph.nodes[node]["cpu_rate"] = float(node_features.get("cpu_rate", fill_value))
	return graph
