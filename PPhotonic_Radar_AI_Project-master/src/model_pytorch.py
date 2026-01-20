import torch
import torch.nn as nn
import torch.nn.functional as F

class RadarCNNBranch(nn.Module):
    """
    CNN Branch for processing 2D radar images (Range-Doppler or Spectrogram).
    """
    def __init__(self, input_shape=(128, 128)):
        super(RadarCNNBranch, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.3)
        
        # Calculate flattened size
        self.flattened_size = 64 * (input_shape[0] // 4) * (input_shape[1] // 4)

    def forward(self, x):
        # x is expected to be (B, 1, H, W)
        # If it's (B, H, W), add channel dimension
        if x.dim() == 3:
            x = x.unsqueeze(1)
        # Handle cases where it might have been unsqueezed too many times (B, 1, 1, H, W)
        while x.dim() > 4:
            x = x.squeeze(1)
        
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.dropout(x)
        x = x.view(-1, self.flattened_size)
        return x

class PhotonicRadarAI(nn.Module):
    """
    Multi-input Cognitive Photonic Radar AI Architecture.
    Fuses Range-Doppler map, Spectrogram, and Photonic metadata.
    """
    def __init__(self, num_classes=6, metadata_size=8):
        super(PhotonicRadarAI, self).__init__()
        
        # 1. Range-Doppler Branch
        self.rd_branch = RadarCNNBranch(input_shape=(128, 128))
        
        # 2. Spectrogram Branch
        # Assuming spectrogram is also resized to 128x128 or similar
        self.spec_branch = RadarCNNBranch(input_shape=(128, 128))
        
        # 3. Metadata Branch
        self.meta_branch = nn.Sequential(
            nn.Linear(metadata_size, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )
        
        # Fusion and Head
        combined_size = self.rd_branch.flattened_size + self.spec_branch.flattened_size + 16
        self.fc_fusion = nn.Linear(combined_size, 128)
        self.classifier = nn.Linear(128, num_classes)
        
    def forward(self, rd_map, spectrogram, metadata):
        rd_feat = self.rd_branch(rd_map)
        spec_feat = self.spec_branch(spectrogram)
        meta_feat = self.meta_branch(metadata)
        
        # Fuse features
        combined = torch.cat((rd_feat, spec_feat, meta_feat), dim=1)
        
        x = F.relu(self.fc_fusion(combined))
        x = self.classifier(x)
        return x # Return logits instead of softmax for training stability

def build_pytorch_model(num_classes=6):
    return PhotonicRadarAI(num_classes=num_classes)

if __name__ == "__main__":
    # Quick test
    model = build_pytorch_model()
    rd = torch.randn(1, 128, 128)
    spec = torch.randn(1, 128, 128)
    meta = torch.randn(1, 8)
    out = model(rd, spec, meta)
    print(f"Output shape: {out.shape}")
