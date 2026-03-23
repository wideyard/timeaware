"""Baseline Models for PTA Benchmark"""

import numpy as np
from typing import Dict, Any, List

from .base import BaseModel
from ..data import PTASample
from ..data.distributions import create_distribution
from ..config import ACTIVITY_DISTRIBUTIONS, ModelConfig


class RandomModel(BaseModel):
    """Random baseline - selects action uniformly at random"""
    
    def __init__(self, seed: int = 42):
        super().__init__(name="Random")
        self.rng = np.random.default_rng(seed)
        self.actions = ["defer", "check-in", "interrupt"]
    
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        action = self.rng.choice(self.actions)
        return {
            "action": action,
            "confidence": 1.0 / 3.0,
            "p_active": None
        }


class MajorityModel(BaseModel):
    """Majority baseline - always predicts the most frequent action"""
    
    def __init__(self, majority_action: str = "defer"):
        super().__init__(name="Majority")
        self.majority_action = majority_action
    
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        return {
            "action": self.majority_action,
            "confidence": 1.0,
            "p_active": None
        }


class HeuristicModel(BaseModel):
    """Heuristic baseline - uses fixed thresholds on delta_t / E[d]"""
    
    def __init__(self, config: ModelConfig = None):
        super().__init__(name="Heuristic")
        self.config = config or ModelConfig()
        self.distributions = {
            activity: create_distribution(dist_config)
            for activity, dist_config in ACTIVITY_DISTRIBUTIONS.items()
        }
    
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        # Compute ratio of elapsed time to expected duration
        expected_duration = sample.expected_duration
        if expected_duration <= 0:
            ratio = 1.0
        else:
            ratio = sample.delta_t / expected_duration
        
        # Apply thresholds
        if ratio < self.config.heuristic_early_threshold:
            action = "defer"
            p_active = 0.9
        elif ratio > self.config.heuristic_late_threshold:
            action = "interrupt"
            p_active = 0.1
        else:
            action = "check-in"
            p_active = 0.5
        
        return {
            "action": action,
            "confidence": 0.7,
            "p_active": p_active
        }


class OracleModel(BaseModel):
    """Oracle model - has access to true duration distribution"""
    
    def __init__(self, config: ModelConfig = None):
        super().__init__(name="Oracle")
        self.config = config or ModelConfig()
        self.distributions = {
            activity: create_distribution(dist_config)
            for activity, dist_config in ACTIVITY_DISTRIBUTIONS.items()
        }
    
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        # Oracle knows the true distribution
        dist = self.distributions.get(sample.activity)
        
        if dist is None:
            # Fallback for unknown activities
            return {"action": "check-in", "confidence": 0.5, "p_active": 0.5}
        
        # Compute true P(active)
        p_active = dist.p_active(sample.delta_t)
        
        # Select action based on probability
        if p_active > 0.8:
            action = "defer"
        elif p_active < 0.3:
            action = "interrupt"
        else:
            action = "check-in"
        
        return {
            "action": action,
            "confidence": abs(p_active - 0.5) * 2,  # Higher confidence when further from 0.5
            "p_active": p_active
        }


class ThresholdModel(BaseModel):
    """Model with configurable probability thresholds"""
    
    def __init__(self, defer_threshold: float = 0.8, interrupt_threshold: float = 0.3):
        super().__init__(name="Threshold")
        self.defer_threshold = defer_threshold
        self.interrupt_threshold = interrupt_threshold
        self.distributions = {
            activity: create_distribution(dist_config)
            for activity, dist_config in ACTIVITY_DISTRIBUTIONS.items()
        }
    
    def predict(self, sample: PTASample) -> Dict[str, Any]:
        dist = self.distributions.get(sample.activity)
        
        if dist is None:
            return {"action": "check-in", "confidence": 0.5, "p_active": 0.5}
        
        p_active = dist.p_active(sample.delta_t)
        
        if p_active > self.defer_threshold:
            action = "defer"
        elif p_active < self.interrupt_threshold:
            action = "interrupt"
        else:
            action = "check-in"
        
        return {
            "action": action,
            "confidence": abs(p_active - 0.5) * 2,
            "p_active": p_active
        }
