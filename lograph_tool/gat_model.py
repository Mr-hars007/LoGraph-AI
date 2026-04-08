"""
Graph Attention Network (GAT) for Link Prediction - Paper Section 3.5

Implements a GAT with temporal windowing to predict future microservice interactions.
Uses multi-head attention to capture complex relationships from multiple perspectives.

Paper Reference: Eq. 7-9
    αij = exp(LeakyReLU(a^T[Whi||Whj])) / Σk∈N(i) exp(LeakyReLU(a^T[Whi||Whk]))
    h'i = σ(Σj∈N(i) αij W hj)
    h'i = ||k=1^K σ(Σj∈N(i) α(k)ij W(k) hj)  [multi-head concatenation]
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Sequence


@dataclass(frozen=True)
class AttentionWeights:
    """Store attention coefficients from GAT layer."""
    layer_id: int
    head_id: int
    node_i: int
    node_j: int
    weight: float


def leaky_relu(x: float, alpha: float = 0.2) -> float:
    """Leaky ReLU activation: max(alpha*x, x)"""
    return max(alpha * x, x)


def sigmoid(x: float) -> float:
    """Sigmoid activation with numerical stability."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def elu(x: float, alpha: float = 1.0) -> float:
    """Exponential Linear Unit activation."""
    return x if x > 0 else alpha * (math.exp(x) - 1.0)


class MatrixOps:
    """Basic linear algebra operations for GAT computation."""

    @staticmethod
    def dot_product(a: Sequence[float], b: Sequence[float]) -> float:
        """Compute dot product a · b"""
        return sum(x * y for x, y in zip(a, b))

    @staticmethod
    def matrix_vector_mult(
        matrix: Sequence[Sequence[float]],
        vector: Sequence[float],
    ) -> List[float]:
        """Multiply matrix W by vector h: Wh"""
        return [
            sum(matrix[i][j] * vector[j] for j in range(len(vector)))
            for i in range(len(matrix))
        ]

    @staticmethod
    def concatenate(a: Sequence[float], b: Sequence[float]) -> List[float]:
        """Concatenate vectors: [a||b]"""
        return list(a) + list(b)

    @staticmethod
    def vector_sum(vectors: Sequence[Sequence[float]]) -> List[float]:
        """Sum multiple vectors."""
        if not vectors:
            return []
        result = [0.0] * len(vectors[0])
        for vec in vectors:
            for i, val in enumerate(vec):
                result[i] += val
        return result

    @staticmethod
    def vector_scale(vec: Sequence[float], scale: float) -> List[float]:
        """Scale vector by scalar: scale * v"""
        return [x * scale for x in vec]

    @staticmethod
    def vector_apply(vec: Sequence[float], fn) -> List[float]:
        """Apply function element-wise: [fn(x) for x in vec]"""
        return [fn(x) for x in vec]


class GATLayer:
    """
    Single Graph Attention layer with configurable heads.

    Implements multi-head attention mechanism from Paper Eq. 7-9.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 1,
        use_elu: bool = True,
    ):
        """
        Initialize GAT layer.

        Args:
            input_dim: Dimension of input node features
            output_dim: Dimension of output per head (concatenated if multi-head)
            num_heads: Number of attention heads (default: 1)
            use_elu: Use ELU activation (True for Layer1, False for Layer2)
        """
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.use_elu = use_elu

        # Initialize weight matrices for each head: W ∈ R^(out_dim × in_dim)
        random.seed(42)
        self.weights: List[List[List[float]]] = [
            self._init_weight_matrix() for _ in range(num_heads)
        ]

        # Attention parameter vectors: a ∈ R^(2*out_dim)
        self.attention_layers: List[List[float]] = [
            self._init_attention_vector() for _ in range(num_heads)
        ]

    def _init_weight_matrix(self) -> List[List[float]]:
        """Initialize weight matrix with Xavier initialization."""
        limit = math.sqrt(6.0 / (self.input_dim + self.output_dim))
        return [
            [random.uniform(-limit, limit) for _ in range(self.input_dim)]
            for _ in range(self.output_dim)
        ]

    def _init_attention_vector(self) -> List[float]:
        """Initialize attention vector."""
        limit = math.sqrt(6.0 / (2 * self.output_dim))
        return [random.uniform(-limit, limit) for _ in range(2 * self.output_dim)]

    def compute_attention_coefficient(
        self,
        hi: Sequence[float],
        hj: Sequence[float],
        head_id: int,
    ) -> float:
        """
        Compute attention coefficient αij for nodes i and j.

        Paper Eq. 7:
        αij = exp(LeakyReLU(a^T[Whi||Whj])) / Σk∈N(i) ...

        Args:
            hi: Node i features
            hj: Neighbor j features
            head_id: Which attention head

        Returns:
            Unnormalized attention logit (normalization happens in forward pass)
        """
        W = self.weights[head_id]
        a = self.attention_layers[head_id]

        # Compute Whi and Whj
        Whi = MatrixOps.matrix_vector_mult(W, hi)
        Whj = MatrixOps.matrix_vector_mult(W, hj)

        # Concatenate: [Whi||Whj]
        concat = MatrixOps.concatenate(Whi, Whj)

        # Compute a^T[Whi||Whj]
        logit = MatrixOps.dot_product(a, concat)

        # Apply LeakyReLU
        activated = leaky_relu(logit, alpha=0.2)

        # Return unnormalized exponential
        return math.exp(activated)

    def forward(
        self,
        node_features: Dict[int, List[float]],
        edge_index: List[Tuple[int, int]],
        neighbors: Dict[int, List[int]],
    ) -> Tuple[Dict[int, List[float]], List[AttentionWeights]]:
        """
        Forward pass: compute new node embeddings with multi-head attention.

        Paper Eq. 8-9:
        h'i = σ(Σj∈N(i) αij W hj)  [single head]
        h'i = ||k=1^K σ(Σj∈N(i) α(k)ij W(k) hj)  [multi-head concat]

        Args:
            node_features: Dict mapping node_id → feature vector
            edge_index: List of (source, target) edge pairs
            neighbors: Dict mapping node_id → list of neighbor node_ids

        Returns:
            (new_node_features, attention_weights) with aggregated features
        """
        new_features: Dict[int, List[float]] = {}
        attention_records: List[AttentionWeights] = []

        # Compute outputs for each node
        for node_i in node_features.keys():
            head_outputs: List[List[float]] = []

            # Process each attention head independently
            for head_id in range(self.num_heads):
                neighbor_list = neighbors.get(node_i, [])

                if not neighbor_list:
                    # No neighbors: use identity
                    head_output = [0.0] * self.output_dim
                else:
                    # Compute attention coefficients for all neighbors
                    attention_logits: List[float] = []
                    neighbor_embeddings: List[List[float]] = []

                    for node_j in neighbor_list:
                        hi = node_features[node_i]
                        hj = node_features[node_j]
                        logit = self.compute_attention_coefficient(hi, hj, head_id)
                        attention_logits.append(logit)
                        neighbor_embeddings.append(
                            MatrixOps.matrix_vector_mult(self.weights[head_id], hj)
                        )

                    # Normalize attention coefficients
                    sum_logits = sum(attention_logits)
                    alphas = [
                        logit / max(sum_logits, 1e-9) for logit in attention_logits
                    ]

                    # Record attention weights
                    for j_idx, node_j in enumerate(neighbor_list):
                        attention_records.append(
                            AttentionWeights(
                                layer_id=0,  # Single layer for now
                                head_id=head_id,
                                node_i=node_i,
                                node_j=node_j,
                                weight=alphas[j_idx],
                            )
                        )

                    # Aggregate: Σj αij Wh j
                    weighted_neighbors = [
                        MatrixOps.vector_scale(emb, alpha)
                        for emb, alpha in zip(neighbor_embeddings, alphas)
                    ]
                    aggregated = MatrixOps.vector_sum(weighted_neighbors)

                    # Apply activation
                    if self.use_elu:
                        head_output = MatrixOps.vector_apply(aggregated, elu)
                    else:
                        head_output = aggregated

                head_outputs.append(head_output)

            # Concatenate multi-head outputs
            if len(head_outputs) == 1:
                final_embedding = head_outputs[0]
            else:
                final_embedding = MatrixOps.concatenate(
                    *[tuple(h) for h in head_outputs]
                )

            new_features[node_i] = final_embedding

        return new_features, attention_records


class GAT:
    """
    Complete Graph Attention Network for link prediction.

    Two-layer GAT as per Paper Section 3.5.1:
    - Layer 1: Multi-head attention with 2 heads → ELU activation
    - Layer 2: Single-head attention → consolidation
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 32,
        output_dim: int = 16,
    ):
        """
        Initialize GAT model.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension (after first GAT layer)
            output_dim: Output embedding dimension
        """
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Layer 1: 2-head attention with ELU
        self.gat_layer1 = GATLayer(input_dim, hidden_dim, num_heads=2, use_elu=True)

        # Layer 2: 1-head attention, consolidation
        self.gat_layer2 = GATLayer(hidden_dim * 2, output_dim, num_heads=1, use_elu=False)

        # Link prediction head: scalar projection + sigmoid
        self.link_weight = [random.uniform(-0.1, 0.1) for _ in range(output_dim)]
        self.link_bias = 0.0

    def forward(
        self,
        node_features: Dict[int, List[float]],
        edge_index: List[Tuple[int, int]],
    ) -> Tuple[Dict[int, List[float]], List[AttentionWeights]]:
        """
        Forward pass through both GAT layers.

        Args:
            node_features: Dict mapping node_id → feature vector
            edge_index: List of (source, target) edges

        Returns:
            (final_embeddings, all_attention_weights)
        """
        # Build neighbor graph from edges
        neighbors: Dict[int, List[int]] = {}
        for src, dst in edge_index:
            if src not in neighbors:
                neighbors[src] = []
            neighbors[src].append(dst)

        # Layer 1: Apply first GAT layer with 2 heads
        layer1_features, layer1_attention = self.gat_layer1.forward(
            node_features, edge_index, neighbors
        )

        # Layer 2: Apply second GAT layer with 1 head
        layer2_features, layer2_attention = self.gat_layer2.forward(
            layer1_features, edge_index, neighbors
        )

        all_attention = layer1_attention + layer2_attention
        return layer2_features, all_attention

    def predict_link_probability(
        self,
        embedding_i: Sequence[float],
        embedding_j: Sequence[float],
    ) -> float:
        """
        Predict probability of link between nodes i and j.

        Paper Eq. 11-12:
        sij = hi^T · hj
        pij = σ(sij)

        Args:
            embedding_i: Output embedding for node i
            embedding_j: Output embedding for node j

        Returns:
            Probability ∈ [0, 1]
        """
        # Dot product
        dot = MatrixOps.dot_product(embedding_i, embedding_j)

        # Add learned weight
        weighted = dot + MatrixOps.dot_product(self.link_weight, embedding_i)
        weighted += self.link_bias

        # Sigmoid
        return sigmoid(weighted)
