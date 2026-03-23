"""Base Model Interface for PTA Benchmark"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..data import PTASample


class BaseModel(ABC):
    """Base class for all PTA models"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        """
        Make a prediction for a given sample.
        
        Args:
            sample: A PTASample containing context and delta_t
            
        Returns:
            Dict with keys:
                - action: str (one of "defer", "check-in", "interrupt")
                - confidence: float (optional, 0-1)
                - p_active: float (optional, predicted probability of activity being active)
        """
        pass
    
    def predict_batch(self, samples: list[PTASample]) -> list[Dict[str, Any]]:
        """Predict for a batch of samples"""
        return [self.predict(s) for s in samples]
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
