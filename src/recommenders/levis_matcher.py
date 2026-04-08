"""
Levi's: rank fits (models) first from preference + scaled size-32 measurements,
then randomly pick SKUs among top-matched fits at the user's size.
Aligned with Nudie fit-first logic (without dry pass).
"""

import random
from typing import Dict, List, Tuple, Optional, Any

from .models import CandidateProduct, UserInput
from .fit_mapper import get_candidate_fits_for_brand
from .scorer import score_candidates

_SCORE_BAND = 40.0
_MAX_TOP_FITS = 5
_BASELINE_SIZE = 32


def _scaled_measurements_for_fit(
    fit_id: str,
    user_size: int,
    levis_measurements: Dict[str, Dict[str, float]],
) -> Optional[Dict[str, float]]:
    m = levis_measurements.get(fit_id)
    if not m:
        return None
    scale = user_size / float(_BASELINE_SIZE)
    return {
        "waist": float(user_size),
        "front_rise": (m.get("front_rise") or 0) * scale,
        "knee": (m.get("knee") or 0) * scale,
        "leg_opening": (m.get("leg_opening") or 0) * scale,
    }


def _product_to_candidate(
    product: dict,
    fit_id: str,
    tag_size: int,
    measurements: Dict[str, float],
) -> CandidateProduct:
    price = (product.get("price") or "").strip() or None
    return CandidateProduct(
        brand="levis",
        product_id=product.get("product_id", ""),
        product_name=product.get("product_name", ""),
        fit_id=fit_id,
        product_url=product.get("product_url", ""),
        tag_size=tag_size,
        measurements=measurements,
        price=price,
    )


def build_levis_recommendations(
    user_input: UserInput,
    user_size: int,
    gender: str,
    levis_products: List[Dict[str, Any]],
    levis_measurements: Dict[str, Dict[str, float]],
    rng: Optional[random.Random] = None,
) -> List[CandidateProduct]:
    """
    1. Candidate Levi's models from fit preference.
    2. Rank fits using scaled measurements at user_size + same scorer as Nudie/global.
    3. Top fits: score within _SCORE_BAND of best, up to _MAX_TOP_FITS.
    4. Randomly pick up to 5 distinct SKUs from products in those fits only.
    """
    rng = rng or random.Random()
    preference = user_input.fit_preference
    candidate_fits = get_candidate_fits_for_brand("levis", preference)
    if not candidate_fits:
        return []

    fit_rows: List[Tuple[str, Dict[str, float]]] = []
    for fit_id in candidate_fits:
        meas = _scaled_measurements_for_fit(fit_id, user_size, levis_measurements)
        if not meas:
            continue
        if not any(p for p in levis_products if (p.get("fit_id") or "").strip() == fit_id):
            continue
        fit_rows.append((fit_id, meas))

    if not fit_rows:
        return []

    dummies = [
        CandidateProduct(
            brand="levis",
            product_id=f"fit_rank:{fit_id}",
            product_name=fit_id,
            fit_id=fit_id,
            product_url="",
            tag_size=user_size,
            measurements=meas,
        )
        for fit_id, meas in fit_rows
    ]
    score_candidates(dummies, user_input)
    dummies.sort(
        key=lambda c: (
            -c.score,
            -(c.measurements.get("knee", 0) or 0),
            -(c.measurements.get("front_rise", 0) or 0),
            -(c.measurements.get("leg_opening", 0) or 0),
        )
    )

    best_score = dummies[0].score
    top_fit_ids: List[str] = []
    seen = set()
    for c in dummies:
        if c.fit_id in seen:
            continue
        if c.score >= best_score - _SCORE_BAND and len(top_fit_ids) < _MAX_TOP_FITS:
            seen.add(c.fit_id)
            top_fit_ids.append(c.fit_id)

    if not top_fit_ids:
        top_fit_ids = [dummies[0].fit_id]

    top_fit_set = set(top_fit_ids)
    meas_by_fit = {fid: m for fid, m in fit_rows if fid in top_fit_set}

    def eligible(p: dict) -> bool:
        fid = (p.get("fit_id") or "").strip()
        if fid not in top_fit_set:
            return False
        if (p.get("gender") or "").strip().lower() != gender:
            return False
        return bool((p.get("product_url") or "").strip())

    pool = [p for p in levis_products if eligible(p)]
    rng.shuffle(pool)

    chosen: List[CandidateProduct] = []
    chosen_urls = set()
    for p in pool:
        if len(chosen) >= 5:
            break
        url = p.get("product_url", "")
        if url in chosen_urls:
            continue
        fid = (p.get("fit_id") or "").strip()
        chosen.append(
            _product_to_candidate(p, fid, user_size, dict(meas_by_fit[fid]))
        )
        chosen_urls.add(url)

    return chosen
