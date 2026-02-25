import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvModel(nn.Module):
    def __init__(self, in_features, window_size, hidden_features, num_classes=3):
        super(ConvModel, self).__init__()
        self.in_features = in_features
        self.window_size = window_size
        
        # 1D Convolution over the window_size dimension
        # Input to conv1d: [batch_size * num_nodes, in_features, window_size]
        # We'll use a small kernel size (e.g., 3)
        self.conv1 = nn.Conv1d(
            in_channels=in_features,
            out_channels=hidden_features,
            kernel_size=min(3, window_size),
            padding=1 if window_size >= 3 else 0
        )
        
        self.conv2 = nn.Conv1d(
            in_channels=hidden_features,
            out_channels=hidden_features,
            kernel_size=min(3, window_size),
            padding=1 if window_size >= 3 else 0
        )
        
        # Calculate feature map size after convolution
        # Since we use padding=1 and kernel_size=3, output length remains window_size
        # If window_size < 3, padding is 0, so length is window_size - kernel_size + 1
        conv_out_len = window_size if window_size >= 3 else (window_size - min(3, window_size) + 1)
        self.flat_size = hidden_features * conv_out_len
        
        self.fc1 = nn.Linear(self.flat_size, hidden_features)
        self.fc2 = nn.Linear(hidden_features, num_classes)
        
    def forward(self, x):
        # x shape: [batch_size, num_nodes, window_size, in_features]
        batch_size, num_nodes, w_size, f_size = x.shape
        
        # Reshape for conv1d: [batch_size * num_nodes, in_features, window_size]
        x_reshaped = x.permute(0, 1, 3, 2).reshape(batch_size * num_nodes, f_size, w_size)
        
        h = F.relu(self.conv1(x_reshaped))
        h = F.relu(self.conv2(h))
        
        # Flatten temporal and channel dimensions
        h_flat = h.reshape(batch_size * num_nodes, -1)
        
        # Dense layers
        out = F.relu(self.fc1(h_flat))
        logits = self.fc2(out) # [batch_size * num_nodes, num_classes]
        
        # Reshape back to [batch_size, num_nodes, num_classes]
        return logits.reshape(batch_size, num_nodes, -1)
