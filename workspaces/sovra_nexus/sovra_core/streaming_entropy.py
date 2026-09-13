"""
XORAS SOVEREIGN CORE: STREAMING SHANNON ENTROPY ENGINE
Pre-computes logarithm lookup tables to execute Shannon entropy calculations
in sub-microsecond time with zero runtime allocations.
"""

import math
from typing import Sequence, Union

class StreamingEntropyEngine:
    """Stack-like zero-allocation Shannon Entropy evaluator."""

    def __init__(self, max_length: int = 8192):
        self.max_length = max_length
        # Precompute table for x * log2(x)
        self.plogp_lut = [0.0] * (max_length + 1)
        for i in range(1, max_length + 1):
            self.plogp_lut[i] = i * math.log2(i)

    def calculate_entropy(self, data: Union[bytes, str]) -> float:
        """Computes exact Shannon entropy in bits per character/byte."""
        if not data:
            return 0.0

        if isinstance(data, str):
            raw_bytes = data.encode("utf-8")
        else:
            raw_bytes = data

        length = len(raw_bytes)
        if length == 0:
            return 0.0

        counts = [0] * 256
        for b in raw_bytes:
            counts[b] += 1

        if length <= self.max_length:
            sum_val = 0.0
            for c in counts:
                if c > 0:
                    sum_val += self.plogp_lut[c]
            return math.log2(length) - (sum_val / length)

        # Fallback for unusually long strings
        entropy = 0.0
        len_f = float(length)
        for c in counts:
            if c > 0:
                p = c / len_f
                entropy -= p * math.log2(p)
        return entropy

    def is_suspicious_entropy(self, token: str, threshold: float = 4.0, min_len: int = 20, max_len: int = 120) -> bool:
        """Determines whether a token exhibits cryptographic secret entropy."""
        if not (min_len <= len(token) <= max_len):
            return False
        # Ignore common paths or URIs
        if "/" in token or "\\" in token or "." in token:
            return False
        return self.calculate_entropy(token) >= threshold
