"""
Nudie Jeans: rank at fit level (measurements are per fit), then pick
1 dry per top-matched fit + random fill to 5 recommendations.
"""

import random
from typing import Dict, List, Tuple, Optional

from .models import CandidateProduct, UserInput
from .fit_mapper import get_candidate_fits_for_brand
from .scorer import score_candidates

# Fits within this score drop from the best are considered "top matched" (0–300 scale).
_SCORE_BAND = 40.0
_MAX_TOP_FITS_FOR_DRY = 5


def _best_tag_for_fit(
    fit_id: str,
    target_waist: float,
    nudie_measurements: Dict[str, Dict[int, Dict[str, float]]],
) -> Optional[Tuple[int, Dict[str, float]]]:
    """Best tag size for target waist (same logic as legacy nudie product matcher)."""
    if fit_id not in nudie_measurements:
        return None
    by_size = nudie_measurements[fit_id]
    best_tag = None
    best_score = float("inf")
    estimated_tag = int(round(target_waist))
    for tag_size, m in by_size.items():
        waist = m.get("waist")
        if waist is not None and waist >= target_waist:
            score = abs(tag_size - estimated_tag) * 10 + (waist - target_waist)
            if score < best_score:
                best_score = score
                best_tag = (tag_size, m)
    if not best_tag:
        min_diff = float("inf")
        for tag_size, m in by_size.items():
            waist = m.get("waist")
            if waist is not None:
                d = abs(waist - target_waist)
                if d < min_diff:
                    min_diff = d
                    best_tag = (tag_size, m)
    return best_tag


def _is_dry_product(product: dict) -> bool:
    ws = (product.get("wash_state") or "").strip().lower()
    return ws == "dry"


def _product_to_candidate(
    product: dict,
    fit_id: str,
    tag_size: int,
    measurements: Dict[str, float],
) -> CandidateProduct:
    return CandidateProduct(
        brand="nudie",
        product_id=product.get("product_id", ""),
        product_name=product.get("product_name", ""),
        fit_id=fit_id,
        product_url=product.get("product_url", ""),
        tag_size=tag_size,
        measurements=measurements,
        price=product.get("price"),
    )


def build_nudie_recommendations(
    user_input: UserInput,
    target_waist: float,
    gender: str,
    nudie_products: Dict[str, list],
    nudie_measurements: Dict[str, Dict[int, Dict[str, float]]],
    rng: Optional[random.Random] = None,
) -> List[CandidateProduct]:
    """
    1. Candidate fits from preference.
    2. Rank fits using fit-level measurements + same scorer as global flow.
    3. Top-matched fits: score within _SCORE_BAND of best, up to 5 fits.
    4. At least one dry per top fit (if no dry, one random regular product for that fit).
    5. Random fill to 5 total from products in those fits (correct tag per fit).
    """
    rng = rng or random.Random()
    preference = user_input.fit_preference
    candidate_fits = get_candidate_fits_for_brand("nudie", preference)
    if not candidate_fits:
        return []

    fit_rows: List[Tuple[str, int, Dict[str, float]]] = []
    for fit_id in candidate_fits:
        bt = _best_tag_for_fit(fit_id, target_waist, nudie_measurements)
        if not bt:
            continue
        tag_size, measurements = bt
        if fit_id not in nudie_products:
            continue
        fit_rows.append((fit_id, tag_size, measurements))

    if not fit_rows:
        return []

    # One dummy candidate per fit for scoring
    dummies = [
        CandidateProduct(
            brand="nudie",
            product_id=f"fit_rank:{fit_id}",
            product_name=fit_id,
            fit_id=fit_id,
            product_url="",
            tag_size=tag_size,
            measurements=measurements,
        )
        for fit_id, tag_size, measurements in fit_rows
    ]
    score_candidates(dummies, user_input)
    # Sort fits: score, then waist proximity to target (when prefs tie all at 0)
    dummies.sort(
        key=lambda c: (
            -c.score,
            -abs(float(c.measurements.get("waist") or 0) - target_waist),
            -(c.measurements.get("front_rise", 0) or 0),
            -(c.measurements.get("knee", 0) or 0),
            -(c.measurements.get("leg_opening", 0) or 0),
        )
    )

    best_score = dummies[0].score
    top_fits: List[Tuple[str, int, Dict[str, float]]] = []
    seen_fit = set()
    for c in dummies:
        if c.fit_id in seen_fit:
            continue
        if c.score >= best_score - _SCORE_BAND and len(top_fits) < _MAX_TOP_FITS_FOR_DRY:
            seen_fit.add(c.fit_id)
            tag = c.tag_size
            m = dict(c.measurements)
            top_fits.append((c.fit_id, tag, m))

    if not top_fits:
        top_fits = [(dummies[0].fit_id, dummies[0].tag_size, dict(dummies[0].measurements))]

    def eligible_products(fit_id: str) -> List[dict]:
        out = []
        for p in nudie_products.get(fit_id, []):
            if p.get("gender") != gender or p.get("status") != "regular":
                continue
            if not (p.get("product_url") or "").strip():
                continue
            out.append(p)
        return out

    chosen: List[CandidateProduct] = []
    chosen_urls = set()

    # Pass 1: one dry (or fallback) per top fit
    for fit_id, tag_size, measurements in top_fits:
        pool = eligible_products(fit_id)
        dry_pool = [p for p in pool if _is_dry_product(p)]
        if dry_pool:
            p = rng.choice(dry_pool)
        elif pool:
            p = rng.choice(pool)
        else:
            continue
        url = p.get("product_url", "")
        if url in chosen_urls:
            continue
        chosen.append(_product_to_candidate(p, fit_id, tag_size, measurements))
        chosen_urls.add(url)

    # Pass 2: random fill to 5
    all_pool: List[Tuple[dict, str, int, Dict[str, float]]] = []
    for fit_id, tag_size, measurements in top_fits:
        for p in eligible_products(fit_id):
            all_pool.append((p, fit_id, tag_size, measurements))

    rng.shuffle(all_pool)
    for p, fit_id, tag_size, measurements in all_pool:
        if len(chosen) >= 5:
            break
        url = p.get("product_url", "")
        if url in chosen_urls:
            continue
        chosen.append(_product_to_candidate(p, fit_id, tag_size, measurements))
        chosen_urls.add(url)

    return chosen[:5]
