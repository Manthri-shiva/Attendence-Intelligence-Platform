from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseFaceRecognitionProvider(ABC):
    """
    Abstract base class for Face Recognition services.
    Ensures substitution compatibility with InsightFace, DeepFace, FaceNet, etc.
    """
    @abstractmethod
    def verify_face(
        self,
        image_b64: str,
        user_reference_id: int,
        simulate_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Match a captured base64 image against the user's registered face template.
        Returns a dictionary containing:
          - "verified": bool
          - "confidence_score": float
          - "provider_name": str
        """
        pass

class BaseLivenessDetectionProvider(ABC):
    """
    Abstract base class for Liveness Detection (Anti-Spoofing) services.
    Ensures substitution compatibility with MediaPipe, OpenCV, custom ML, etc.
    """
    @abstractmethod
    def detect_liveness(
        self,
        image_b64: str,
        simulate_liveness: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze captured frame for liveness cues (checks for static photo, screen replays, etc.)
        Returns a dictionary containing:
          - "is_live": bool
          - "liveness_score": float
          - "provider_name": str
          - "error_message": Optional[str] (detailing spoof trigger details)
        """
        pass
