"""PTA Benchmark Configuration"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Any

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Random Seeds
RANDOM_SEED = 42
NUMPY_SEED = 42

# Data Generation
@dataclass
class DataConfig:
    """Data generation configuration"""
    num_samples: int = 1000
    seed: int = RANDOM_SEED
    delta_t_regions: Dict[str, tuple] = field(default_factory=lambda: {
        "early": (0.0, 0.3),
        "mid": (0.3, 0.8),
        "late": (0.8, 1.5)
    })
    region_weights: Dict[str, float] = field(default_factory=lambda: {
        "early": 0.33,
        "mid": 0.34,
        "late": 0.33
    })
    # Action thresholds
    defer_threshold: float = 0.8
    interrupt_threshold: float = 0.3

# Activity Duration Distributions (in minutes)
ACTIVITY_DISTRIBUTIONS = {
    "nap": {"type": "uniform", "params": {"low": 10, "high": 60}},
    "meeting": {"type": "uniform", "params": {"low": 30, "high": 120}},
    "deep_sleep": {"type": "uniform", "params": {"low": 180, "high": 480}},
    "commute": {"type": "lognormal", "params": {"mean": 30, "std": 10}},
    "workout": {"type": "uniform", "params": {"low": 30, "high": 90}},
    "lunch_break": {"type": "uniform", "params": {"low": 20, "high": 60}},
    "phone_call": {"type": "lognormal", "params": {"mean": 10, "std": 5}},
    "cooking": {"type": "uniform", "params": {"low": 15, "high": 90}},
    "shower": {"type": "uniform", "params": {"low": 5, "high": 30}},
    "reading": {"type": "uniform", "params": {"low": 20, "high": 120}},
    "gaming": {"type": "uniform", "params": {"low": 30, "high": 180}},
    "meditation": {"type": "uniform", "params": {"low": 10, "high": 45}},
}

# Context templates for natural language generation
CONTEXT_TEMPLATES = {
    "nap": [
        "I'm going to take a quick nap",
        "Need to rest my eyes for a bit",
        "Gonna catch some sleep",
        "Time for a short rest",
    ],
    "meeting": [
        "Heading into a meeting",
        "Got a work discussion to attend",
        "Joining a conference call",
        "Meeting with the team",
    ],
    "deep_sleep": [
        "Time to go to bed",
        "Calling it a night",
        "Going to get some proper sleep",
        "Finally hitting the sack",
    ],
    "commute": [
        "Starting my journey home",
        "Heading to work",
        "On my way to the office",
        "Beginning my commute",
    ],
    "workout": [
        "Going to hit the gym",
        "Time for my exercise routine",
        "Starting my workout session",
        "Going for a run",
    ],
    "lunch_break": [
        "Taking my lunch break",
        "Going to grab some food",
        "Time for lunch",
        "Stepping out for a meal",
    ],
    "phone_call": [
        "Making a quick call",
        "Need to ring someone",
        "Got a phone call to make",
        "Calling back a colleague",
    ],
    "cooking": [
        "Starting to prepare dinner",
        "Going to cook something",
        "Time to make some food",
        "Preparing a meal",
    ],
    "shower": [
        "Going to take a shower",
        "Need to freshen up",
        "Time for a quick wash",
        "Hopping in the shower",
    ],
    "reading": [
        "Going to read for a while",
        "Starting my book",
        "Time for some reading",
        "Settling in with a novel",
    ],
    "gaming": [
        "Starting a gaming session",
        "Going to play some games",
        "Time for some gaming",
        "Hopping on the console",
    ],
    "meditation": [
        "Going to meditate",
        "Time for some mindfulness",
        "Starting my meditation practice",
        "Doing some breathing exercises",
    ],
}

# Evaluation
@dataclass
class EvalConfig:
    """Evaluation configuration"""
    tsu_pair_count: int = 100
    bas_tolerance: float = 0.1  # Tolerance for "near boundary" samples
    calibration_bins: int = 10

# Model Config
@dataclass
class ModelConfig:
    """Model configuration"""
    heuristic_early_threshold: float = 0.3
    heuristic_late_threshold: float = 0.8
