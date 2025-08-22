"""Shared utilities for benchmark tests."""

import time


class Timer:
    """Context manager for timing code execution in microseconds."""
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.elapsed = (self.end - self.start) * 1_000_000  # Convert to microseconds
    
    def __float__(self):
        return self.elapsed
    
    def __str__(self):
        return f"{self.elapsed:.1f}μs"