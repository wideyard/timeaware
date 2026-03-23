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
    # Whether to use expanded activities from MCTACO
    use_expanded_activities: bool = False

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

# Expanded Activity Distributions from MCTACO (higher quality activities)
EXPANDED_ACTIVITY_DISTRIBUTIONS = {
    # ===== 原始活动 =====
    "commute": {"type": "lognormal", "params": {"mean": 30, "std": 10}},
    "cooking": {"type": "uniform", "params": {"low": 15, "high": 90}},
    "deep_sleep": {"type": "uniform", "params": {"low": 180, "high": 480}},
    "gaming": {"type": "uniform", "params": {"low": 30, "high": 180}},
    "lunch_break": {"type": "uniform", "params": {"low": 20, "high": 60}},
    "meditation": {"type": "uniform", "params": {"low": 10, "high": 45}},
    "meeting": {"type": "uniform", "params": {"low": 30, "high": 120}},
    "nap": {"type": "uniform", "params": {"low": 10, "high": 60}},
    "phone_call": {"type": "lognormal", "params": {"mean": 10, "std": 5}},
    "reading": {"type": "uniform", "params": {"low": 20, "high": 120}},
    "shower": {"type": "uniform", "params": {"low": 5, "high": 30}},
    "workout": {"type": "uniform", "params": {"low": 30, "high": 90}},
    # ===== MCTACO扩充活动 =====
    "do_the_laundry": {"type": "uniform", "params": {"low": 60.0, "high": 120.0}},
    "write_the_letter": {"type": "uniform", "params": {"low": 15.0, "high": 30.0}},
    "the_tour": {"type": "uniform", "params": {"low": 45.0, "high": 60.0}},
    "the_drive": {"type": "uniform", "params": {"low": 120.0, "high": 360.0}},
    "the_meeting": {"type": "uniform", "params": {"low": 180.0, "high": 300.0}},
    "the_interview": {"type": "uniform", "params": {"low": 30.0, "high": 300.0}},
    "the_hearing": {"type": "uniform", "params": {"low": 90.0, "high": 480.0}},
    "the_fight": {"type": "uniform", "params": {"low": 60.0, "high": 300.0}},
    "the_award_ceremony": {"type": "uniform", "params": {"low": 60.0, "high": 120.0}},
    "in_the_interview": {"type": "uniform", "params": {"low": 30.0, "high": 60.0}},
    "at_the_courthouse": {"type": "uniform", "params": {"low": 180.0, "high": 300.0}},
    "enjoy_under_the_sun": {"type": "uniform", "params": {"low": 60.0, "high": 120.0}},
    "sleep": {"type": "uniform", "params": {"low": 120.0, "high": 480.0}},
    "cook_meat": {"type": "uniform", "params": {"low": 15.0, "high": 60.0}},
    "story_time": {"type": "uniform", "params": {"low": 30.0, "high": 60.0}},
    "the_game_of_tag": {"type": "uniform", "params": {"low": 10.0, "high": 30.0}},
    "would_a_bus_ride_normally": {"type": "uniform", "params": {"low": 15.0, "high": 60.0}},
    "lost_in_thoughts": {"type": "uniform", "params": {"low": 10.0, "high": 20.0}},
    "roberta_sit_at_the_computer": {"type": "uniform", "params": {"low": 120.0, "high": 180.0}},
    "their_average_plane_flight": {"type": "uniform", "params": {"low": 300.0, "high": 360.0}},
}

def get_activity_distributions(use_expanded: bool = False) -> Dict[str, Any]:
    """Get activity distributions, optionally including expanded ones"""
    if use_expanded:
        return EXPANDED_ACTIVITY_DISTRIBUTIONS.copy()
    return ACTIVITY_DISTRIBUTIONS.copy()

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
    # MCTACO扩充活动的默认模板
    "do_the_laundry": ["Going to do the laundry", "Time to wash clothes"],
    "write_the_letter": ["Going to write a letter", "Sitting down to write"],
    "the_tour": ["Starting the tour", "Going on a tour"],
    "the_drive": ["Starting the drive", "Going for a drive"],
    "the_interview": ["Going into the interview", "Starting the interview"],
    "the_hearing": ["Attending the hearing", "Going to the hearing"],
    "the_fight": ["The fight is starting", "Getting into the fight"],
    "the_award_ceremony": ["Attending the ceremony", "Going to the award ceremony"],
    "in_the_interview": ["In the interview", "During the interview"],
    "at_the_courthouse": ["At the courthouse", "Spending time at court"],
    "enjoy_under_the_sun": ["Enjoying the sun", "Soaking up the sunshine"],
    "sleep": ["Going to sleep", "Time to rest"],
    "cook_meat": ["Cooking the meat", "Preparing the meat"],
    "story_time": ["Story time begins", "Starting story time"],
    "the_game_of_tag": ["Playing tag", "Starting a game of tag"],
    "lost_in_thoughts": ["Lost in thought", "Thinking deeply"],
    "roberta_sit_at_the_computer": ["Sitting at the computer", "Working on the computer"],
    "their_average_plane_flight": ["On the plane", "During the flight"],
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
