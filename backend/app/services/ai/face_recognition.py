import os
from typing import Optional, Dict, Any
from app.services.ai.base import BaseFaceRecognitionProvider

class MockFaceRecognitionProvider(BaseFaceRecognitionProvider):
    """
    Mock high-fidelity implementation of FaceRecognitionProvider.
    Decoupled and substitutes for production libraries (DeepFace, FaceNet) in the future.
    """
    def __init__(self):
        # Load default threshold from env variables (defaults to 0.85)
        self.default_threshold = float(os.getenv("FACE_CONFIDENCE_THRESHOLD", "0.85"))
        self.provider_name = os.getenv("AI_PROVIDER", "MockFaceRecognition")

    def verify_face(
        self,
        image_b64: str,
        user_reference_id: int,
        simulate_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Verify face matching.
        Accepts custom simulate_confidence values from test payloads to verify threshold triggers.
        """
        # Determine confidence score (simulated or matching standard)
        confidence = 0.95 if simulate_confidence is None else simulate_confidence
        
        # Determine verified status based on threshold
        verified = confidence >= self.default_threshold

        return {
            "verified": verified,
            "confidence_score": confidence,
            "provider_name": self.provider_name
        }
