"""
Main recommendation engine: reference one brand, get top 5 from each of the 3 brands.
"""

from typing import List, Dict, Optional
from .models import UserInput, CandidateProduct
from .data_loader import (
    load_nf_products,
    load_nf_size_charts,
    load_nudie_products,
    load_nudie_measurements,
    load_levis_products,
    load_levis_measurements,
)
from .fit_mapper import get_candidate_fits_for_brand
from .targets import get_target_measurements
from .size_matcher import find_matching_sizes_nf
from .nudie_matcher import build_nudie_recommendations
from .levis_matcher import build_levis_recommendations
from .scorer import score_candidates

# Cache loaded data
_cache = {}


def _load_data():
    global _cache
    if not _cache:
        _cache["nf_products"] = load_nf_products()
        _cache["nf_size_charts"] = load_nf_size_charts()
        _cache["nudie_products"] = load_nudie_products()
        _cache["nudie_measurements"] = load_nudie_measurements()
        _cache["levis_products"] = load_levis_products()
        _cache["levis_measurements"] = load_levis_measurements()
    return _cache


def recommend(user_input: UserInput) -> List[Dict[str, str]]:
    """
    Recommend jeans from all 3 brands: top 5 per brand (15 total).
    Uses reference brand + fit/model + size to get target measurements, then matches
    across N&F, Nudie, and Levi's; scores by rise/thigh/leg preferences; returns
    product name, size, price, URL per recommendation.
    """
    data = _load_data()
    nf_products = data["nf_products"]
    nf_size_charts = data["nf_size_charts"]
    nudie_products = data["nudie_products"]
    nudie_measurements = data["nudie_measurements"]
    levis_products = data["levis_products"]
    levis_measurements = data["levis_measurements"]

    target = get_target_measurements(
        user_input,
        nf_products,
        nf_size_charts,
        nudie_measurements,
        levis_measurements,
    )
    target_waist = target.get("waist")
    if target_waist is None:
        target_waist = float(user_input.reference_size)
    else:
        target_waist = float(target_waist)

    gender = user_input.gender or "mens"
    preference = user_input.fit_preference

    all_candidates: List[CandidateProduct] = []

    # N&F
    nf_fits = get_candidate_fits_for_brand("nf", preference)
    if nf_fits:
        nf_candidates = find_matching_sizes_nf(
            nf_fits, target_waist, gender, nf_products, nf_size_charts
        )
        all_candidates.extend(nf_candidates)

    # Nudie: fit-level rank, 1 dry per top fit + random to 5 (N&F / Levi's unchanged)
    nudie_candidates = build_nudie_recommendations(
        user_input, target_waist, gender, nudie_products, nudie_measurements
    )
    all_candidates.extend(nudie_candidates)

    # Levi's: fit-level rank, random SKUs among top fits at user's size
    levis_candidates = build_levis_recommendations(
        user_input,
        user_input.reference_size,
        gender,
        levis_products,
        levis_measurements,
    )
    all_candidates.extend(levis_candidates)

    if not all_candidates:
        return []

    scored = score_candidates(all_candidates, user_input)

    # Top 5 per brand
    by_brand: Dict[str, List[CandidateProduct]] = {"nf": [], "nudie": [], "levis": []}
    for c in scored:
        if c.brand in by_brand and len(by_brand[c.brand]) < 5:
            by_brand[c.brand].append(c)

    results = []
    for brand in ["nf", "nudie", "levis"]:
        for c in by_brand[brand]:
            results.append({
                "brand": brand,
                "product_name": c.product_name,
                "tag_size": c.tag_size,
                "price": c.price or "",
                "product_url": c.product_url,
            })
    return results
