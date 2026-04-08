"""
Scoring algorithm for candidate products
"""

from typing import List
from .models import CandidateProduct, UserInput


def score_candidates(
    candidates: List[CandidateProduct], 
    user_input: UserInput
) -> List[CandidateProduct]:
    """
    Score candidates with equal weights, tie-breaking by priority:
    1. Rise (highest priority)
    2. Thigh (medium priority)  
    3. Leg opening (lowest priority)
    
    Args:
        candidates: List of candidate products to score
        user_input: User input with preferences
    
    Returns:
        List of scored and sorted candidates
    """
    if not candidates:
        return candidates
    
    # If no preferences, return all with equal scores
    if not any([user_input.rise_preference, user_input.thigh_preference, user_input.leg_opening_preference]):
        return candidates
    
    # Find max values for normalization
    max_rise = max((c.measurements.get('front_rise', 0) or 0 for c in candidates), default=1)
    max_knee = max((c.measurements.get('knee', 0) or 0 for c in candidates), default=1)
    max_leg_opening = max((c.measurements.get('leg_opening', 0) or 0 for c in candidates), default=1)
    
    for candidate in candidates:
        score = 0.0
        breakdown = {}
        
        # Equal weight scoring (each contributes up to 100 points)
        if user_input.rise_preference:
            rise = candidate.measurements.get('front_rise', 0) or 0
            if user_input.rise_preference == "higher":
                rise_score = (rise / max_rise) * 100 if max_rise > 0 else 0
            elif user_input.rise_preference == "lower":
                rise_score = ((max_rise - rise) / max_rise) * 100 if max_rise > 0 else 0
            else:  # "similar"
                rise_score = 50  # Neutral
            score += rise_score
            breakdown['rise'] = rise_score
        
        if user_input.thigh_preference:
            knee = candidate.measurements.get('knee', 0) or 0
            if user_input.thigh_preference == "more":
                thigh_score = (knee / max_knee) * 100 if max_knee > 0 else 0
            elif user_input.thigh_preference == "less":
                thigh_score = ((max_knee - knee) / max_knee) * 100 if max_knee > 0 else 0
            else:  # "similar"
                thigh_score = 50
            score += thigh_score
            breakdown['thigh'] = thigh_score
        
        if user_input.leg_opening_preference:
            leg_opening = candidate.measurements.get('leg_opening', 0) or 0
            if user_input.leg_opening_preference == "wider":
                leg_score = (leg_opening / max_leg_opening) * 100 if max_leg_opening > 0 else 0
            elif user_input.leg_opening_preference == "narrower":
                leg_score = ((max_leg_opening - leg_opening) / max_leg_opening) * 100 if max_leg_opening > 0 else 0
            else:  # "similar"
                leg_score = 50
            score += leg_score
            breakdown['leg_opening'] = leg_score
        
        candidate.score = score
        candidate.score_breakdown = breakdown
    
    # Sort with tie-breaking
    # Primary: total score (descending)
    # Tie-break 1: rise (descending)
    # Tie-break 2: thigh/knee (descending)
    # Tie-break 3: leg opening (descending)
    candidates.sort(key=lambda c: (
        -c.score,  # Primary: total score (descending)
        -(c.measurements.get('front_rise', 0) or 0),  # Tie-break 1: rise (descending)
        -(c.measurements.get('knee', 0) or 0),  # Tie-break 2: thigh (descending)
        -(c.measurements.get('leg_opening', 0) or 0)  # Tie-break 3: leg opening (descending)
    ))
    
    return candidates

