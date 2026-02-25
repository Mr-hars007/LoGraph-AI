import torch
import torch.nn as nn
import torch.nn.functional as F

class GraphConv(nn.Module):
    """
    A simple Graph Convolutional Layer.
    Computes: H^{(l+1)} = ReLU(D^{-1/2} A D^{-1/2} H^{(l)} W^{(l)})
    """
    def __init__(self, in_features, out_features):
        super(GraphConv, self).__init__()
        self.linear = nn.Linear(in_features, out_features, bias=False)
        
    def forward(self, x, norm_adj):
        # x shape: [batch_size, num_nodes, in_features] or [num_nodes, in_features]
        # norm_adj shape: [num_nodes, num_nodes]
        
        # Aggregate neighbor features
        # If batch_size is present, we perform batch matrix multiplication
        if len(x.shape) == 3:
            # norm_adj is 2D, we can expand it for batch multiplication
            # or just do torch.matmul(norm_adj, x) which broadcasts
            aggregated = torch.matmul(norm_adj, x)
        else:
            aggregated = torch.matmul(norm_adj, x)
            
        # Apply linear transformation
        out = self.linear(aggregated)
        return out

class GNNModel(nn.Module):
    def __init__(self, in_features, hidden_features, num_classes=3):
        super(GNNModel, self).__init__()
        # 3 mock backends form a fully connected triangle (or cyclic graph)
        # A = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]
        # A_tilde (with self loops) = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        # D_tilde = diag(3, 3, 3)
        # D_tilde^{-1/2} A_tilde D_tilde^{-1/2} = A_tilde / 3
        adj = torch.tensor([
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0]
        ], dtype=torch.float32)
        # Normalize: D^{-1/2} A D^{-1/2}
        deg = adj.sum(dim=1)
        deg_inv_sqrt = torch.diag(1.0 / torch.sqrt(deg))
        self.norm_adj = torch.matmul(torch.diag(1.0 / torch.sqrt(deg)), torch.matmul(adj, deg_inv_sqrt))
        
        # Keep adjacency matrix as buffer so it moves to device with model
        self.register_buffer("adj_matrix", self.norm_adj)
        
        # GNN layers
        self.gcn1 = GraphConv(in_features, hidden_features)
        self.gcn2 = GraphConv(hidden_features, hidden_features)
        
        # Fully connected layer for node classification
        # We classify each of the 3 nodes independently into num_classes
        self.fc = nn.Linear(hidden_features, num_classes)
        
    def forward(self, x):
        # x shape can be: [batch_size, num_nodes, window_size, in_features]
        # or [batch_size, num_nodes, in_features]
        if len(x.shape) == 4:
            batch_size, num_nodes, w_size, f_size = x.shape
            x = x.reshape(batch_size, num_nodes, w_size * f_size)
            
        h = F.relu(self.gcn1(x, self.adj_matrix))
        h = F.relu(self.gcn2(h, self.adj_matrix))
        logits = self.fc(h) # [batch_size, num_nodes, num_classes]
        return logits
