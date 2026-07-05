import os
from typing import Optional, Dict, Any
from app.services.ai.base import BaseLivenessDetectionProvider

class MockLivenessDetectionProvider(BaseLivenessDetectionProvider):
    """
    Mock high-fidelity implementation of LivenessDetectionProvider.
    Decoupled and substitutes for MediaPipe, Custom ML, or OpenCV anti-spoofing models.
    """
    def __init__(self):
        self.default_threshold = float(os.getenv("LIVENESS_THRESHOLD", "0.90"))
        self.provider_name = "MockLivenessDetection"

    def detect_liveness(
        self,
        image_b64: str,
        simulate_liveness: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate liveness and trigger custom spoof-cases depending on test tags.
        """
        # If no simulation trigger is sent, default to high-liveness score
        score = 0.98
        is_live = True
        error_msg = None

        if simulate_liveness:
            sim_lower = simulate_liveness.strip().lower()
            if sim_lower == "static photo" or sim_lower == "photo":
                is_live = False
                score = 0.45
                error_msg = "Anti-Spoofing: Static photo detected."
            elif sim_lower == "replay attempt" or sim_lower == "replay":
                is_live = False
                score = 0.30
                error_msg = "Anti-Spoofing: Screen replay attack detected."
            elif sim_lower == "multiple faces" or sim_lower == "multi-face":
                is_live = False
                score = 0.50
                error_msg = "Anti-Spoofing: Multiple faces identified in the frame."
            elif sim_lower == "no face" or sim_lower == "none":
                is_live = False
                score = 0.00
                error_msg = "Anti-Spoofing: No face identified in the frame."
            elif sim_lower == "low lighting" or sim_lower == "dark":
                is_live = False
                score = 0.60
                error_msg = "Anti-Spoofing: Insufficient lighting, face scan failed."
            elif sim_lower == "spoof":
                is_live = False
                score = 0.10
                error_msg = "Anti-Spoofing: General spoofing signature matched."

        # Double check threshold comparison
        if is_live and score < self.default_threshold:
            is_live = False
            error_msg = "Anti-Spoofing: Liveness threshold check failed."

        return {
            "is_live": is_live,
            "liveness_score": score,
            "provider_name": self.provider_name,
            "error_message": error_msg
        }
