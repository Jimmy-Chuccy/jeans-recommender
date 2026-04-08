"""
Compute target measurements from user's reference brand + fit/model + size.
"""

from typing import Dict, Optional, Any
from .models import UserInput


def get_target_measurements(
    user_input: UserInput,
    nf_products: Dict[str, list],
    nf_size_charts: Dict[str, Dict[int, Dict[str, float]]],
    nudie_measurements: Dict[str, Dict[int, Dict[str, float]]],
    levis_measurements: Dict[str, Dict[str, float]],
) -> Dict[str, Optional[float]]:
    """
    Get target waist, front_rise, knee, leg_opening from the user's reference.
    Returns dict with keys waist, front_rise, knee, leg_opening (value None if unknown).
    """
    target = {"waist": None, "front_rise": None, "knee": None, "leg_opening": None}
    brand = (user_input.reference_brand or "").strip().lower()
    size = user_input.reference_size
    fit_or_model = (user_input.reference_fit_or_model or "").strip()

    if brand == "none" or not brand:
        target["waist"] = float(size)
        return target

    if brand == "nf":
        # Find any product in this fit that has size chart with this size
        if fit_or_model not in nf_products:
            target["waist"] = float(size)
            return target
        for product in nf_products[fit_or_model]:
            url = product.get("product_url")
            if not url or url not in nf_size_charts:
                continue
            charts = nf_size_charts[url]
            if size in charts:
                m = charts[size]
                target["waist"] = m.get("waist")
                target["front_rise"] = m.get("front_rise")
                target["knee"] = m.get("knee")
                target["leg_opening"] = m.get("leg_opening")
                return target
            # Find closest size
            best_sz = None
            best_diff = float("inf")
            for tag_size, m in charts.items():
                w = m.get("waist")
                if w is not None and abs(w - size) < best_diff:
                    best_diff = abs(w - size)
                    best_sz = tag_size
            if best_sz is not None:
                m = charts[best_sz]
                target["waist"] = m.get("waist")
                target["front_rise"] = m.get("front_rise")
                target["knee"] = m.get("knee")
                target["leg_opening"] = m.get("leg_opening")
                return target
        target["waist"] = float(size)
        return target

    if brand == "nudie":
        if fit_or_model not in nudie_measurements:
            target["waist"] = float(size)
            return target
        by_size = nudie_measurements[fit_or_model]
        if size in by_size:
            m = by_size[size]
            target["waist"] = m.get("waist")
            target["front_rise"] = m.get("front_rise")
            target["knee"] = m.get("knee")
            target["leg_opening"] = m.get("leg_opening")
            return target
        best_sz = None
        best_diff = float("inf")
        for tag_size, m in by_size.items():
            w = m.get("waist")
            if w is not None and abs(w - size) < best_diff:
                best_diff = abs(w - size)
                best_sz = tag_size
        if best_sz is not None:
            m = by_size[best_sz]
            target["waist"] = m.get("waist")
            target["front_rise"] = m.get("front_rise")
            target["knee"] = m.get("knee")
            target["leg_opening"] = m.get("leg_opening")
            return target
        target["waist"] = float(size)
        return target

    if brand == "levis":
        if fit_or_model not in levis_measurements:
            target["waist"] = float(size)
            return target
        m = levis_measurements[fit_or_model]
        # Baseline is size 32; scale to user size
        base_waist = m.get("waist") or 32
        scale = size / 32.0 if base_waist else size / 32.0
        target["waist"] = float(size)  # Levi's waist = tag size
        target["front_rise"] = (m.get("front_rise") or 0) * scale if m.get("front_rise") else None
        target["knee"] = (m.get("knee") or 0) * scale if m.get("knee") else None
        target["leg_opening"] = (m.get("leg_opening") or 0) * scale if m.get("leg_opening") else None
        return target

    target["waist"] = float(size)
    return target
