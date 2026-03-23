"""Data Generator for PTA Benchmark"""

import json
import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from .distributions import DurationDistribution, create_distribution
from ..config import (
    DataConfig, ACTIVITY_DISTRIBUTIONS, CONTEXT_TEMPLATES,
    RANDOM_SEED, get_activity_distributions
)


@dataclass
class PTASample:
    """A single PTA benchmark sample"""
    id: int
    activity: str
    context: str
    delta_t: float  # Elapsed time in minutes
    duration: Optional[float]  # True duration (for oracle, hidden from model)
    p_active: float  # P(activity still active)
    valid_actions: List[str]
    delta_t_region: str  # early/mid/late
    expected_duration: float  # E[d] for the activity


class PTADatasetGenerator:
    """Generator for PTA benchmark datasets"""
    
    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or DataConfig()
        self.rng = np.random.default_rng(self.config.seed)
        random.seed(self.config.seed)
        
        # Get activity distributions (expanded if configured)
        activity_dists = get_activity_distributions(
            use_expanded=self.config.use_expanded_activities
        )
        
        # Create distributions for each activity
        self.distributions: Dict[str, DurationDistribution] = {}
        for activity, dist_config in activity_dists.items():
            self.distributions[activity] = create_distribution(dist_config)
        
        self.activities = list(self.distributions.keys())
    
    def _select_delta_t_region(self) -> str:
        """Select a delta_t region based on weights"""
        regions = list(self.config.region_weights.keys())
        weights = list(self.config.region_weights.values())
        return self.rng.choice(regions, p=weights)
    
    def _sample_delta_t(self, expected_duration: float, region: str) -> float:
        """Sample delta_t based on region"""
        region_bounds = self.config.delta_t_regions[region]
        low, high = region_bounds
        
        # Sample ratio within region
        ratio = self.rng.uniform(low, high)
        delta_t = ratio * expected_duration
        
        return max(0.1, delta_t)  # Ensure positive
    
    def _compute_valid_actions(self, p_active: float) -> List[str]:
        """Compute valid actions based on P(active)"""
        if p_active > self.config.defer_threshold:
            return ["defer"]
        elif p_active < self.config.interrupt_threshold:
            return ["interrupt"]
        else:
            return ["check-in", "defer"]
    
    def _generate_context(self, activity: str) -> str:
        """Generate natural language context for activity"""
        templates = CONTEXT_TEMPLATES.get(activity, [f"I'm doing {activity}"])
        return random.choice(templates)
    
    def generate_sample(self, sample_id: int) -> PTASample:
        """Generate a single sample"""
        # 1. Sample activity
        activity = self.rng.choice(self.activities)
        dist = self.distributions[activity]
        
        # 2. Sample duration
        duration = dist.sample(self.rng, size=1)[0]
        expected_duration = dist.expected_value()
        
        # 3. Select region and sample delta_t
        region = self._select_delta_t_region()
        delta_t = self._sample_delta_t(expected_duration, region)
        
        # 4. Compute P(active)
        p_active = dist.p_active(delta_t)
        
        # 5. Compute valid actions
        valid_actions = self._compute_valid_actions(p_active)
        
        # 6. Generate context
        context = self._generate_context(activity)
        
        return PTASample(
            id=sample_id,
            activity=activity,
            context=context,
            delta_t=round(delta_t, 2),
            duration=round(duration, 2),
            p_active=round(p_active, 4),
            valid_actions=valid_actions,
            delta_t_region=region,
            expected_duration=round(expected_duration, 2)
        )
    
    def generate_dataset(self) -> List[PTASample]:
        """Generate full dataset"""
        samples = []
        for i in range(self.config.num_samples):
            sample = self.generate_sample(i)
            samples.append(sample)
        return samples
    
    def generate_paired_samples(self, num_pairs: int) -> List[Tuple[PTASample, PTASample]]:
        """Generate paired samples for TSU metric (same context, different delta_t)"""
        pairs = []
        
        for i in range(num_pairs):
            # Generate base sample
            sample1 = self.generate_sample(sample_id=i * 2)
            
            # Generate paired sample with same activity but different region
            regions = list(self.config.delta_t_regions.keys())
            current_region = sample1.delta_t_region
            other_regions = [r for r in regions if r != current_region]
            new_region = self.rng.choice(other_regions)
            
            dist = self.distributions[sample1.activity]
            delta_t2 = self._sample_delta_t(sample1.expected_duration, new_region)
            p_active2 = dist.p_active(delta_t2)
            valid_actions2 = self._compute_valid_actions(p_active2)
            
            sample2 = PTASample(
                id=i * 2 + 1,
                activity=sample1.activity,
                context=sample1.context,
                delta_t=round(delta_t2, 2),
                duration=sample1.duration,
                p_active=round(p_active2, 4),
                valid_actions=valid_actions2,
                delta_t_region=new_region,
                expected_duration=sample1.expected_duration
            )
            
            pairs.append((sample1, sample2))
        
        return pairs
    
    def save_dataset(self, samples: List[PTASample], filepath: str):
        """Save dataset to JSON"""
        data = [asdict(s) for s in samples]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_dataset(self, filepath: str) -> List[PTASample]:
        """Load dataset from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [PTASample(**d) for d in data]


def generate_ablation_dataset(
    samples: List[PTASample],
    ablation_type: str
) -> List[PTASample]:
    """Generate ablated dataset for ablation studies"""
    ablated = []
    
    for sample in samples:
        if ablation_type == "remove_time":
            # Set delta_t to 0 (ignore time)
            new_sample = PTASample(
                id=sample.id,
                activity=sample.activity,
                context=sample.context,
                delta_t=0.0,
                duration=sample.duration,
                p_active=sample.p_active,
                valid_actions=sample.valid_actions,
                delta_t_region=sample.delta_t_region,
                expected_duration=sample.expected_duration
            )
        elif ablation_type == "remove_commonsense":
            # Shuffle activity labels
            random_act = random.choice(list(ACTIVITY_DISTRIBUTIONS.keys()))
            new_sample = PTASample(
                id=sample.id,
                activity=random_act,
                context=sample.context,
                delta_t=sample.delta_t,
                duration=sample.duration,
                p_active=sample.p_active,
                valid_actions=sample.valid_actions,
                delta_t_region=sample.delta_t_region,
                expected_duration=sample.expected_duration
            )
        elif ablation_type == "deterministic_duration":
            # Replace duration with expected value
            new_sample = PTASample(
                id=sample.id,
                activity=sample.activity,
                context=sample.context,
                delta_t=sample.delta_t,
                duration=sample.expected_duration,
                p_active=sample.p_active,
                valid_actions=sample.valid_actions,
                delta_t_region=sample.delta_t_region,
                expected_duration=sample.expected_duration
            )
        else:
            new_sample = sample
        
        ablated.append(new_sample)
    
    return ablated
