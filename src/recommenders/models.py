"""
Data models for the recommendation system
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class UserInput:
    """User input for recommendations"""
    # Fit style preference (same as before)
    fit_preference: Optional[str]  # "relaxed", "slim", "tapered", "straight", "bootcut", "skinny"

    # Reference: which brand the user wears (or "none")
    reference_brand: str  # "nf" | "nudie" | "levis" | "none"
    reference_fit_or_model: Optional[str] = None  # fit_id (e.g. "weird_guy", "grim_tim") or Levi's model ("501", "511")
    reference_size: int = 32  # waist size they wear (or general size if reference_brand == "none")

    gender: str = "mens"

    # Q&A fine-tuning
    rise_preference: Optional[str] = None  # "higher", "lower", "similar"
    thigh_preference: Optional[str] = None  # "more", "less", "similar"
    leg_opening_preference: Optional[str] = None  # "wider", "narrower", "similar"


@dataclass
class CandidateProduct:
    """Candidate product for recommendation (any brand)"""
    brand: str  # "nf" | "nudie" | "levis"
    product_id: str
    product_name: str
    fit_id: str
    product_url: str
    tag_size: int
    measurements: Dict[str, float]  # waist, front_rise, knee, leg_opening
    price: Optional[str] = None  # display price (e.g. "242.00" or None)
    score: float = 0.0
    score_breakdown: Optional[Dict[str, float]] = field(default=None)
