from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from feature_extractor import load_cpu_metrics
from graph_builder import load_and_build_graph


@dataclass(frozen=True)
class PreparedGraphData:
	node_to_index: Dict[str, int]
	node_names: List[str]
	edge_index: List[List[int]]
	node_features: List[List[float]]
	node_details: List[Dict[str, Any]]
	edge_details: List[Dict[str, Any]]
	stats: Dict[str, float]


def prepare_graph_data(rpc_map_csv: str | Path, metrics_dir: str | Path) -> PreparedGraphData:
	"""Build graph + features and convert to arrays suitable for GNN frameworks."""
	graph = load_and_build_graph(rpc_map_csv)
	cpu_features = load_cpu_metrics(metrics_dir)

	nodes: List[str] = list(graph.nodes)
	node_to_index = {name: idx for idx, name in enumerate(nodes)}

	# edge_index shape: [2, E], expected by many GNN APIs.
	edge_pairs = [(node_to_index[e.source], node_to_index[e.target]) for e in graph.edges]
	if edge_pairs:
		src_indices = [src for src, _ in edge_pairs]
		dst_indices = [dst for _, dst in edge_pairs]
		edge_index = [src_indices, dst_indices]
	else:
		edge_index = [[], []]

	node_features = [
		[
			float(cpu_features.get(node, {}).get("cpu_last", 0.0)),
			float(cpu_features.get(node, {}).get("cpu_mean", 0.0)),
			float(cpu_features.get(node, {}).get("cpu_rate", 0.0)),
		]
		for node in nodes
	]

	in_degree: Dict[str, int] = {node: 0 for node in nodes}
	out_degree: Dict[str, int] = {node: 0 for node in nodes}
	in_weight: Dict[str, int] = {node: 0 for node in nodes}
	out_weight: Dict[str, int] = {node: 0 for node in nodes}

	edge_details: List[Dict[str, Any]] = []
	for edge in graph.edges:
		out_degree[edge.source] += 1
		in_degree[edge.target] += 1
		out_weight[edge.source] += edge.call_count
		in_weight[edge.target] += edge.call_count

		edge_details.append(
			{
				"source": edge.source,
				"target": edge.target,
				"call_count": edge.call_count,
				"source_index": node_to_index[edge.source],
				"target_index": node_to_index[edge.target],
			}
		)

	node_details: List[Dict[str, Any]] = []
	for node in nodes:
		cpu = cpu_features.get(node, {})
		node_details.append(
			{
				"name": node,
				"index": node_to_index[node],
				"in_degree": in_degree[node],
				"out_degree": out_degree[node],
				"in_weight": in_weight[node],
				"out_weight": out_weight[node],
				"cpu_last": float(cpu.get("cpu_last", 0.0)),
				"cpu_mean": float(cpu.get("cpu_mean", 0.0)),
				"cpu_rate": float(cpu.get("cpu_rate", 0.0)),
			}
		)

	weighted_edges = sum(edge.call_count for edge in graph.edges)
	nodes_with_cpu = sum(
		1 for node in nodes if cpu_features.get(node, {}).get("cpu_last", 0.0) > 0.0
	)

	stats = {
		"nodes": float(len(nodes)),
		"edges": float(len(graph.edges)),
		"weighted_edges": float(weighted_edges),
		"nodes_with_cpu": float(nodes_with_cpu),
	}

	return PreparedGraphData(
		node_to_index=node_to_index,
		node_names=nodes,
		edge_index=edge_index,
		node_features=node_features,
		node_details=node_details,
		edge_details=edge_details,
		stats=stats,
	)


if __name__ == "__main__":
	project_root = Path(__file__).resolve().parent.parent
	rpc_map = project_root / "data" / "compose_ms_rpc_map.csv"
	metrics_dir = project_root / "data"

	prepared = prepare_graph_data(rpc_map, metrics_dir)
	print("Prepared graph data summary:")
	print(f"- Nodes: {int(prepared.stats['nodes'])}")
	print(f"- Edges: {int(prepared.stats['edges'])}")
	print(f"- Weighted calls: {int(prepared.stats['weighted_edges'])}")
	print(f"- Nodes with CPU metrics: {int(prepared.stats['nodes_with_cpu'])}")
	edge_count = len(prepared.edge_index[0]) if prepared.edge_index else 0
	feature_rows = len(prepared.node_features)
	feature_cols = len(prepared.node_features[0]) if prepared.node_features else 0
	print(f"- edge_index shape: (2, {edge_count})")
	print(f"- node_features shape: ({feature_rows}, {feature_cols})")
