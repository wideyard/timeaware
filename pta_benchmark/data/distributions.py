"""Duration Distribution Classes"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional


class DurationDistribution(ABC):
    """Base class for duration distributions"""
    
    @abstractmethod
    def sample(self, rng: np.random.Generator, size: int = 1) -> np.ndarray:
        """Sample from distribution"""
        pass
    
    @abstractmethod
    def expected_value(self) -> float:
        """Return expected value E[d]"""
        pass
    
    @abstractmethod
    def pdf(self, x: float) -> float:
        """Probability density function"""
        pass
    
    @abstractmethod
    def cdf(self, x: float) -> float:
        """Cumulative distribution function"""
        pass
    
    def p_active(self, delta_t: float) -> float:
        """P(activity still active at delta_t) = P(d > delta_t)"""
        return 1.0 - self.cdf(delta_t)


class UniformDistribution(DurationDistribution):
    """Uniform distribution: U(low, high)"""
    
    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high
    
    def sample(self, rng: np.random.Generator, size: int = 1) -> np.ndarray:
        return rng.uniform(self.low, self.high, size)
    
    def expected_value(self) -> float:
        return (self.low + self.high) / 2.0
    
    def pdf(self, x: float) -> float:
        if self.low <= x <= self.high:
            return 1.0 / (self.high - self.low)
        return 0.0
    
    def cdf(self, x: float) -> float:
        if x < self.low:
            return 0.0
        elif x > self.high:
            return 1.0
        else:
            return (x - self.low) / (self.high - self.low)


class NormalDistribution(DurationDistribution):
    """Normal distribution: N(mean, std)"""
    
    def __init__(self, mean: float, std: float, min_val: float = 0.0):
        self.mean = mean
        self.std = std
        self.min_val = min_val  # Truncation minimum
    
    def sample(self, rng: np.random.Generator, size: int = 1) -> np.ndarray:
        samples = rng.normal(self.mean, self.std, size)
        # Truncate at minimum
        return np.maximum(samples, self.min_val)
    
    def expected_value(self) -> float:
        return self.mean
    
    def pdf(self, x: float) -> float:
        if x < self.min_val:
            return 0.0
        z = (x - self.mean) / self.std
        return np.exp(-0.5 * z**2) / (self.std * np.sqrt(2 * np.pi))
    
    def cdf(self, x: float) -> float:
        if x < self.min_val:
            return 0.0
        from scipy import stats
        # Truncated normal CDF
        cdf_at_x = stats.norm.cdf(x, loc=self.mean, scale=self.std)
        cdf_at_min = stats.norm.cdf(self.min_val, loc=self.mean, scale=self.std)
        return (cdf_at_x - cdf_at_min) / (1.0 - cdf_at_min)


class LogNormalDistribution(DurationDistribution):
    """Log-Normal distribution with given mean and std"""
    
    def __init__(self, mean: float, std: float):
        """
        Args:
            mean: Desired mean of the log-normal distribution
            std: Desired std of the log-normal distribution
        """
        self.mean = mean
        self.std = std
        # Compute mu and sigma for underlying normal
        # If X ~ LogNormal, then E[X] = exp(mu + sigma^2/2)
        # Var[X] = (exp(sigma^2) - 1) * exp(2*mu + sigma^2)
        self.sigma_sq = np.log(1 + (std / mean) ** 2)
        self.mu = np.log(mean) - self.sigma_sq / 2
        self.sigma = np.sqrt(self.sigma_sq)
    
    def sample(self, rng: np.random.Generator, size: int = 1) -> np.ndarray:
        return rng.lognormal(self.mu, self.sigma, size)
    
    def expected_value(self) -> float:
        return self.mean
    
    def pdf(self, x: float) -> float:
        if x <= 0:
            return 0.0
        z = (np.log(x) - self.mu) / self.sigma
        return np.exp(-0.5 * z**2) / (x * self.sigma * np.sqrt(2 * np.pi))
    
    def cdf(self, x: float) -> float:
        if x <= 0:
            return 0.0
        from scipy import stats
        return stats.lognorm.cdf(x, s=self.sigma, scale=np.exp(self.mu))


def create_distribution(dist_config: dict) -> DurationDistribution:
    """Factory function to create distribution from config"""
    dist_type = dist_config["type"]
    params = dist_config["params"]
    
    if dist_type == "uniform":
        return UniformDistribution(**params)
    elif dist_type == "normal":
        return NormalDistribution(**params)
    elif dist_type == "lognormal":
        return LogNormalDistribution(**params)
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")
