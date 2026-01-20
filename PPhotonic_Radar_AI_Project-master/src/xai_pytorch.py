import torch
import torch.nn.functional as F
import numpy as np
import cv2

def grad_cam_pytorch(model, rd_map, spec, meta, target_layer):
    """
    Computes Grad-CAM for PyTorch model.
    rd_map, spec, meta are input tensors.
    target_layer is the layer to hook into (e.g. model.rd_branch.conv2)
    """
    feature_gradients = []
    feature_maps = []

    def save_gradient(grad):
        feature_gradients.append(grad)

    def save_feature_map(module, input, output):
        feature_maps.append(output)

    handle_grad = target_layer.register_full_backward_hook(lambda module, grad_input, grad_output: save_gradient(grad_output[0]))
    handle_feat = target_layer.register_forward_hook(save_feature_map)

    # Move inputs to model device
    device = next(model.parameters()).device
    rd_map = rd_map.to(device)
    spec = spec.to(device)
    meta = meta.to(device)

    output = model(rd_map, spec, meta)
    
    # We use softmax output in forward, so let's get the class index
    class_idx = torch.argmax(output, dim=1).item()
    
    model.zero_grad()
    # Ensure score is a scalar for backward()
    score = output[0, class_idx]
    
    try:
        score.backward(retain_graph=True)
    except Exception as e:
        print(f"Grad-CAM Backward Error: {e}")
        handle_grad.remove()
        handle_feat.remove()
        return np.zeros((128, 128))

    handle_grad.remove()
    handle_feat.remove()

    if not feature_gradients or not feature_maps:
        return np.zeros((128, 128))

    gradients = feature_gradients[0]
    features = feature_maps[0]

    weights = torch.mean(gradients, dim=(2, 3), keepdim=True)
    cam = torch.sum(weights * features, dim=1).squeeze()
    
    cam = F.relu(cam)
    cam = cam.detach().cpu().numpy()
    
    # Determine which branch to use based on target_layer
    is_rd = "rd_branch" in str(target_layer)
    is_spec = "spec_branch" in str(target_layer)

    if is_rd:
        input_data = rd_map
    elif is_spec:
        input_data = spec
    else:
        # Fallback if we can't determine
        input_data = rd_map

    # Ensure input_data has a single channel if it's (B, 1, H, W)
    # The visualization needs (H, W)
    display_img = input_data.squeeze().detach().cpu().numpy()
    if display_img.ndim > 2:
        display_img = display_img[0] # Take first channel if multiple

    # Robust normalization before return
    if np.max(cam) > 0:
        cam = cam / np.max(cam)
    else:
        cam = np.zeros_like(cam)

    return cv2.resize(cam, (display_img.shape[1], display_img.shape[0]))
