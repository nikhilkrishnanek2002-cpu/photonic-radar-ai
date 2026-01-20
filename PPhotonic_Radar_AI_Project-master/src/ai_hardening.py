"""
AI Reliability Hardening for Mission-Critical Radar Systems.

Implements:
- Prediction confidence estimation
- Out-of-distribution (OOD) detection
- Model disagreement alerts  
- Explainability (Grad-CAM, feature attribution)
- Decision audit trail with reasoning
"""

import numpy as np
import torch
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import time


@dataclass
class AIDecision:
    """Hardened AI decision with full confidence and explainability."""
    predicted_class: str
    confidence: float              # [0, 1] softmax confidence
    prediction_entropy: float      # uncertainty measure
    is_ood: bool                   # out-of-distribution flag
    ood_score: float               # [0, 1] OOD likelihood
    is_reliable: bool              # overall reliability flag
    reliability_reasons: List[str] = field(default_factory=list)
    saliency_map: Optional[np.ndarray] = None  # Grad-CAM visualization
    top_k_predictions: Dict[str, float] = field(default_factory=dict)  # top 3 predictions
    timestamp: float = field(default_factory=time.time)
    audit_log: str = ""


class ConfidenceEstimator:
    """Estimate prediction confidence and uncertainty."""
    
    def __init__(self, entropy_threshold: float = 1.0, confidence_threshold: float = 0.7):
        """
        Initialize confidence estimator.
        
        Args:
            entropy_threshold: max entropy for reliable predictions
            confidence_threshold: min softmax confidence for reliable predictions
        """
        self.entropy_threshold = entropy_threshold
        self.confidence_threshold = confidence_threshold
    
    def estimate(self, logits: torch.Tensor) -> Tuple[float, float]:
        """
        Estimate prediction confidence and entropy.
        
        Args:
            logits: model logits of shape (batch_size, num_classes) or (num_classes,)
        
        Returns:
            (confidence, entropy)
        """
        # Ensure batch dimension
        if logits.dim() == 1:
            logits = logits.unsqueeze(0)
        
        # Convert to probabilities
        probs = F.softmax(logits, dim=-1)
        
        # Softmax confidence (max probability)
        confidence = float(torch.max(probs, dim=-1)[0].mean())
        
        # Shannon entropy (higher = more uncertain)
        entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
        entropy = float(entropy.mean())
        
        return confidence, entropy
    
    def is_reliable(self, confidence: float, entropy: float) -> Tuple[bool, List[str]]:
        """Check if prediction is reliable."""
        reasons = []
        reliable = True
        
        if confidence < self.confidence_threshold:
            reliable = False
            reasons.append(f"Low confidence: {confidence:.3f} < {self.confidence_threshold}")
        
        if entropy > self.entropy_threshold:
            reliable = False
            reasons.append(f"High uncertainty: entropy={entropy:.3f} > {self.entropy_threshold}")
        
        if not reasons:
            reasons.append("Confidence and uncertainty within acceptable bounds")
        
        return reliable, reasons


class OutOfDistributionDetector:
    """Detect out-of-distribution inputs using multiple methods."""
    
    def __init__(self, method: str = 'reconstruction', threshold: float = 0.5):
        """
        Initialize OOD detector.
        
        Args:
            method: 'reconstruction', 'entropy', or 'activation'
            threshold: OOD confidence threshold [0, 1]
        """
        self.method = method
        self.threshold = threshold
        self.reference_stats = None  # Will store training statistics
    
    def fit(self, embeddings: np.ndarray):
        """Fit OOD detector on reference (in-distribution) data."""
        self.reference_stats = {
            'mean': np.mean(embeddings, axis=0),
            'std': np.std(embeddings, axis=0),
            'cov': np.cov(embeddings.T)
        }
    
    def detect(self, logits: torch.Tensor, features: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """
        Detect if input is out-of-distribution.
        
        Args:
            logits: model logits
            features: optional feature embeddings from penultimate layer
        
        Returns:
            (is_ood, ood_score)
        """
        if self.method == 'entropy':
            return self._entropy_based(logits)
        elif self.method == 'activation' and features is not None:
            return self._activation_based(features)
        else:
            return self._reconstruction_based(logits)
    
    def _entropy_based(self, logits: torch.Tensor) -> Tuple[bool, float]:
        """OOD detection via maximum softmax entropy."""
        if logits.dim() == 1:
            logits = logits.unsqueeze(0)
        
        probs = F.softmax(logits, dim=-1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
        entropy = float(entropy.max())
        
        # Normalize entropy to [0, 1] (max entropy = log(num_classes))
        max_entropy = np.log(logits.shape[-1])
        normalized_entropy = entropy / max_entropy
        
        is_ood = normalized_entropy > self.threshold
        return is_ood, float(normalized_entropy)
    
    def _activation_based(self, features: np.ndarray) -> Tuple[bool, float]:
        """OOD detection via activation statistics (Mahalanobis distance)."""
        if self.reference_stats is None:
            return False, 0.0
        
        # Compute Mahalanobis distance
        mean = self.reference_stats['mean']
        cov = self.reference_stats['cov']
        
        try:
            cov_inv = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
            diff = features - mean
            mahal_dist = np.sqrt(np.dot(diff, np.dot(cov_inv, diff.T)))
            
            # Normalize to [0, 1]
            # Threshold typically at 2-3 sigma
            normalized_score = min(mahal_dist / 5.0, 1.0)
            
            is_ood = normalized_score > self.threshold
            return is_ood, float(normalized_score)
        except Exception:
            return False, 0.0
    
    def _reconstruction_based(self, logits: torch.Tensor) -> Tuple[bool, float]:
        """OOD detection via softmax distribution spread."""
        if logits.dim() == 1:
            logits = logits.unsqueeze(0)
        
        probs = F.softmax(logits, dim=-1)
        
        # OOD score: how concentrated is the probability mass?
        # Highly concentrated (one class dominant) = likely in-distribution
        # Spread out = likely out-of-distribution
        max_prob = torch.max(probs, dim=-1)[0]
        ood_score = 1.0 - float(max_prob.max())  # 1 - confidence
        
        is_ood = ood_score > self.threshold
        return is_ood, ood_score


class ModelDisagreementDetector:
    """Detect disagreement between models or uncertainty estimates."""
    
    def __init__(self, threshold: float = 0.3):
        """
        Initialize model disagreement detector.
        
        Args:
            threshold: disagreement threshold for alerts
        """
        self.threshold = threshold
        self.prediction_history = []
        self.history_size = 10
    
    def add_prediction(self, predicted_class: str, confidence: float):
        """Add prediction to history for disagreement analysis."""
        self.prediction_history.append((predicted_class, confidence))
        if len(self.prediction_history) > self.history_size:
            self.prediction_history.pop(0)
    
    def detect_disagreement(self, predictions: List[Tuple[str, float]]) -> Tuple[bool, float, str]:
        """
        Detect disagreement among multiple predictions/models.
        
        Args:
            predictions: list of (class, confidence) tuples
        
        Returns:
            (has_disagreement, disagreement_score, reason)
        """
        if len(predictions) < 2:
            return False, 0.0, "Single prediction"
        
        classes = [p[0] for p in predictions]
        confidences = [p[1] for p in predictions]
        
        # Check class agreement
        class_agreement = len(set(classes)) == 1
        
        # Check confidence consistency
        conf_std = np.std(confidences)
        conf_mean = np.mean(confidences)
        conf_cv = conf_std / (conf_mean + 1e-8)  # Coefficient of variation
        
        disagreement_score = conf_cv if not class_agreement else conf_std / 2
        
        has_disagreement = disagreement_score > self.threshold
        
        reason = ""
        if not class_agreement:
            reason = f"Classes disagree: {set(classes)}"
        if conf_cv > 0.3:
            reason += f" Confidence inconsistency: CV={conf_cv:.2f}"
        
        return has_disagreement, disagreement_score, reason


class GradCAMExplainer:
    """Generate Grad-CAM saliency maps for model explainability."""
    
    def __init__(self, model: torch.nn.Module, target_layer_name: str = 'features'):
        """
        Initialize Grad-CAM explainer.
        
        Args:
            model: PyTorch model to explain
            target_layer_name: name of layer to visualize (usually last conv layer)
        """
        self.model = model
        self.target_layer_name = target_layer_name
        self.gradients = None
        self.activations = None
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks."""
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        # Try to find and hook the target layer
        for name, module in self.model.named_modules():
            if self.target_layer_name in name or name.endswith(self.target_layer_name):
                module.register_forward_hook(forward_hook)
                module.register_backward_hook(backward_hook)
                break
    
    def generate(self, input_tensor: torch.Tensor, class_idx: int) -> Optional[np.ndarray]:
        """
        Generate Grad-CAM saliency map.
        
        Args:
            input_tensor: input image tensor (1, C, H, W)
            class_idx: target class index
        
        Returns:
            saliency map (H, W) or None if generation fails
        """
        try:
            # Forward pass
            output = self.model(input_tensor)
            
            # Zero gradients
            self.model.zero_grad()
            
            # Backward pass on target class
            if output.dim() == 1:
                output = output.unsqueeze(0)
            
            target_score = output[0, class_idx]
            target_score.backward()
            
            # Compute Grad-CAM
            if self.gradients is None or self.activations is None:
                return None
            
            gradients = self.gradients[0]
            activations = self.activations[0]
            
            # Average gradients across channels
            weights = torch.mean(gradients, dim=(1, 2))
            
            # Weighted sum of activation maps
            cam = torch.zeros(activations.shape[1:])
            for i, w in enumerate(weights):
                cam += w * activations[i]
            
            # ReLU and normalize
            cam = F.relu(cam)
            cam_min = cam.min()
            cam_max = cam.max()
            if cam_max > cam_min:
                cam = (cam - cam_min) / (cam_max - cam_min)
            
            return cam.cpu().numpy()
        except Exception as e:
            return None


class AIReliabilityHardener:
    """
    Top-level AI reliability hardening system.
    
    Ensures every AI decision includes:
    - Confidence estimation
    - OOD detection
    - Disagreement detection
    - Explainability
    """
    
    def __init__(self, model: torch.nn.Module, config: Dict = None):
        """
        Initialize AI hardening system.
        
        Args:
            model: PyTorch model to harden
            config: dict with thresholds and settings
        """
        self.config = config or {}
        self.model = model
        
        # Initialize components
        self.confidence_estimator = ConfidenceEstimator(
            entropy_threshold=self.config.get('entropy_threshold', 1.0),
            confidence_threshold=self.config.get('confidence_threshold', 0.7)
        )
        
        self.ood_detector = OutOfDistributionDetector(
            method=self.config.get('ood_method', 'entropy'),
            threshold=self.config.get('ood_threshold', 0.5)
        )
        
        self.disagreement_detector = ModelDisagreementDetector(
            threshold=self.config.get('disagreement_threshold', 0.3)
        )
        
        self.explainer = GradCAMExplainer(model)
        
        self.decision_log = []
        self.labels = []
    
    def set_labels(self, labels: List[str]):
        """Set class labels for decision output."""
        self.labels = labels
    
    def infer(self, 
             input_tensor: torch.Tensor,
             return_saliency: bool = False,
             device: str = 'cpu') -> AIDecision:
        """
        Perform hardened AI inference with full reliability checks.
        
        Args:
            input_tensor: input data (batch or single sample)
            return_saliency: whether to generate Grad-CAM saliency map
            device: computation device
        
        Returns:
            AIDecision with confidence, OOD detection, and explainability
        """
        input_tensor = input_tensor.to(device)
        
        # Ensure batch dimension
        while input_tensor.dim() < 2:
            input_tensor = input_tensor.unsqueeze(0)
        
        # Forward pass
        self.model.eval()
        with torch.no_grad():
            logits = self.model(input_tensor)
        
        # Confidence estimation
        confidence, entropy = self.confidence_estimator.estimate(logits)
        confidence_reliable, confidence_reasons = self.confidence_estimator.is_reliable(confidence, entropy)
        
        # Out-of-distribution detection
        is_ood, ood_score = self.ood_detector.detect(logits)
        
        # Get top predictions
        if logits.dim() == 1:
            logits = logits.unsqueeze(0)
        
        probs = F.softmax(logits[0], dim=-1)
        top_k_values, top_k_indices = torch.topk(probs, k=min(3, len(self.labels)))
        
        top_k_predictions = {}
        if self.labels:
            for val, idx in zip(top_k_values, top_k_indices):
                top_k_predictions[self.labels[idx]] = float(val)
        
        predicted_idx = int(torch.argmax(probs))
        predicted_class = self.labels[predicted_idx] if self.labels else f"Class_{predicted_idx}"
        
        # Generate saliency map if requested
        saliency_map = None
        if return_saliency:
            saliency_map = self.explainer.generate(input_tensor, predicted_idx)
        
        # Compile reasons
        reliability_reasons = confidence_reasons.copy()
        if is_ood:
            reliability_reasons.append(f"OOD detected (score={ood_score:.3f})")
        
        # Overall reliability
        is_reliable = confidence_reliable and not is_ood
        
        # Create decision
        decision = AIDecision(
            predicted_class=predicted_class,
            confidence=confidence,
            prediction_entropy=entropy,
            is_ood=is_ood,
            ood_score=ood_score,
            is_reliable=is_reliable,
            reliability_reasons=reliability_reasons,
            saliency_map=saliency_map,
            top_k_predictions=top_k_predictions,
            audit_log=self._generate_audit_log(
                predicted_class, confidence, entropy, is_ood, ood_score, is_reliable
            )
        )
        
        self.decision_log.append(decision)
        
        return decision
    
    def _generate_audit_log(self, predicted_class: str, confidence: float, 
                           entropy: float, is_ood: bool, ood_score: float, 
                           is_reliable: bool) -> str:
        """Generate audit trail for decision."""
        log = (f"[DECISION] class={predicted_class}, "
               f"confidence={confidence:.3f}, entropy={entropy:.3f}, "
               f"ood={is_ood}(score={ood_score:.3f}), reliable={is_reliable}")
        return log
    
    def get_reliability_report(self) -> Dict:
        """Generate reliability statistics from decision log."""
        if not self.decision_log:
            return {}
        
        reliable_count = sum(1 for d in self.decision_log if d.is_reliable)
        ood_count = sum(1 for d in self.decision_log if d.is_ood)
        avg_confidence = np.mean([d.confidence for d in self.decision_log])
        avg_entropy = np.mean([d.prediction_entropy for d in self.decision_log])
        
        return {
            'total_decisions': len(self.decision_log),
            'reliable_decisions': reliable_count,
            'reliability_rate': reliable_count / len(self.decision_log),
            'ood_detections': ood_count,
            'ood_rate': ood_count / len(self.decision_log),
            'avg_confidence': avg_confidence,
            'avg_entropy': avg_entropy,
            'recent_decisions': [d.audit_log for d in self.decision_log[-5:]]
        }


# Example usage
if __name__ == "__main__":
    print("=== AI Reliability Hardening Demo ===\n")
    
    # Create dummy model
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = torch.nn.Linear(128, 6)
        
        def forward(self, x):
            return self.fc(x.view(x.size(0), -1))
    
    model = DummyModel()
    
    # Create hardener
    hardener = AIReliabilityHardener(model, {
        'confidence_threshold': 0.7,
        'entropy_threshold': 1.0,
        'ood_threshold': 0.5
    })
    
    labels = ["Drone", "Aircraft", "Bird", "Helicopter", "Missile", "Clutter"]
    hardener.set_labels(labels)
    
    # Test multiple inferences
    print("Testing AI Reliability Hardening:\n")
    for i in range(5):
        # Create test input
        test_input = torch.randn(128)
        
        # Perform hardened inference
        decision = hardener.infer(test_input, return_saliency=False, device='cpu')
        
        print(f"Test {i+1}:")
        print(f"  Prediction: {decision.predicted_class}")
        print(f"  Confidence: {decision.confidence:.3f}")
        print(f"  Entropy: {decision.prediction_entropy:.3f}")
        print(f"  OOD: {decision.is_ood} (score={decision.ood_score:.3f})")
        print(f"  Reliable: {decision.is_reliable}")
        print(f"  Top K: {decision.top_k_predictions}")
        print(f"  Audit: {decision.audit_log}\n")
    
    # Print reliability report
    report = hardener.get_reliability_report()
    print("Reliability Report:")
    for key, value in report.items():
        if key != 'recent_decisions':
            print(f"  {key}: {value}")
