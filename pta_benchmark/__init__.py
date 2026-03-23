"""
PTA Benchmark - Probabilistic Temporal Alignment Benchmark

A benchmark for evaluating LLMs on time-aware decision making
under implicit commonsense uncertainty.
"""

from .data import PTADatasetGenerator, PTASample
from .models import BaseModel, RandomModel, MajorityModel, HeuristicModel, OracleModel, ThresholdModel
from .metrics import compute_ppa, compute_tsu, compute_bas, compute_ce, compute_all_metrics
from .analysis import generate_analysis_report

__version__ = "1.0.0"

__all__ = [
    "PTADatasetGenerator",
    "PTASample",
    "BaseModel",
    "RandomModel",
    "MajorityModel",
    "HeuristicModel",
    "OracleModel",
    "ThresholdModel",
    "compute_ppa",
    "compute_tsu",
    "compute_bas",
    "compute_ce",
    "compute_all_metrics",
    "generate_analysis_report"
]
