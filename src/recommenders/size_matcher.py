"""
Size matching utilities for N&F, Nudie, and Levi's
"""

from typing import List, Dict, Optional
from .models import CandidateProduct


def find_matching_sizes_nf(
    candidate_fits: List[str],
    target_waist: float,
    gender: str,
    nf_products: Dict,
    nf_size_charts: Dict,
) -> List[CandidateProduct]:
    """
    Find N&F products with waist >= target_waist. One candidate per product (best size).
    """
    candidates = []
    for fit_id in candidate_fits:
        if fit_id not in nf_products:
            continue
        for product in nf_products[fit_id]:
            if product.get("gender") != gender or product.get("status") != "regular":
                continue
            product_url = product.get("product_url")
            if not product_url or product_url not in nf_size_charts:
                continue
            best_match = None
            best_score = float("inf")
            estimated_tag = int(round(target_waist))
            for tag_size, measurements in nf_size_charts[product_url].items():
                waist = measurements.get("waist")
                if waist is not None and waist >= target_waist:
                    score = abs(tag_size - estimated_tag) * 10 + (waist - target_waist)
                    if score < best_score:
                        best_score = score
                        best_match = (tag_size, measurements)
            if best_match:
                tag_size, measurements = best_match
                candidates.append(CandidateProduct(
                    brand="nf",
                    product_id=product.get("product_id", ""),
                    product_name=product.get("product_name", ""),
                    fit_id=fit_id,
                    product_url=product_url,
                    tag_size=tag_size,
                    measurements=measurements,
                    price=product.get("price"),
                ))
    if not candidates:
        for fit_id in candidate_fits:
            if fit_id not in nf_products:
                continue
            for product in nf_products[fit_id]:
                if product.get("gender") != gender or product.get("status") != "regular":
                    continue
                product_url = product.get("product_url")
                if not product_url or product_url not in nf_size_charts:
                    continue
                best_match = None
                min_diff = float("inf")
                for tag_size, measurements in nf_size_charts[product_url].items():
                    waist = measurements.get("waist")
                    if waist is not None:
                        d = abs(waist - target_waist)
                        if d < min_diff:
                            min_diff = d
                            best_match = (tag_size, measurements)
                if best_match:
                    tag_size, measurements = best_match
                    candidates.append(CandidateProduct(
                        brand="nf",
                        product_id=product.get("product_id", ""),
                        product_name=product.get("product_name", ""),
                        fit_id=fit_id,
                        product_url=product_url,
                        tag_size=tag_size,
                        measurements=measurements,
                        price=product.get("price"),
                    ))
    return candidates


def find_matching_sizes_nudie(
    candidate_fits: List[str],
    target_waist: float,
    gender: str,
    nudie_products: Dict[str, list],
    nudie_measurements: Dict[str, Dict[int, Dict[str, float]]],
) -> List[CandidateProduct]:
    """
    Find Nudie products with waist >= target_waist. Measurements are per fit_id.
    Returns one candidate per product (best tag_size for that fit).
    """
    candidates = []
    for fit_id in candidate_fits:
        if fit_id not in nudie_products or fit_id not in nudie_measurements:
            continue
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
            best_tag = None
            min_diff = float("inf")
            for tag_size, m in by_size.items():
                waist = m.get("waist")
                if waist is not None:
                    d = abs(waist - target_waist)
                    if d < min_diff:
                        min_diff = d
                        best_tag = (tag_size, m)
        if not best_tag:
            continue
        tag_size, measurements = best_tag
        for product in nudie_products[fit_id]:
            if product.get("gender") != gender or product.get("status") != "regular":
                continue
            candidates.append(CandidateProduct(
                brand="nudie",
                product_id=product.get("product_id", ""),
                product_name=product.get("product_name", ""),
                fit_id=fit_id,
                product_url=product.get("product_url", ""),
                tag_size=tag_size,
                measurements=measurements,
                price=product.get("price"),
            ))
    return candidates


def find_matching_sizes_levis(
    candidate_fits: List[str],
    target_waist: float,
    user_size: int,
    gender: str,
    levis_products: List[Dict],
    levis_measurements: Dict[str, Dict[str, float]],
) -> List[CandidateProduct]:
    """
    Levi's: products have fit_id; measurements are baseline (size 32). Scale to user_size.
    Returns one candidate per product with virtual measurements at user_size.
    """
    candidates = []
    scale = user_size / 32.0
    for product in levis_products:
        fit_id = (product.get("fit_id") or "").strip()
        if not fit_id or fit_id not in candidate_fits:
            continue
        if (product.get("gender") or "").strip().lower() != gender:
            continue
        m = levis_measurements.get(fit_id)
        if not m:
            continue
        measurements = {
            "waist": float(user_size),
            "front_rise": (m.get("front_rise") or 0) * scale,
            "knee": (m.get("knee") or 0) * scale,
            "leg_opening": (m.get("leg_opening") or 0) * scale,
        }
        price = (product.get("price") or "").strip() or None
        candidates.append(CandidateProduct(
            brand="levis",
            product_id=product.get("product_id", ""),
            product_name=product.get("product_name", ""),
            fit_id=fit_id,
            product_url=product.get("product_url", ""),
            tag_size=user_size,
            measurements=measurements,
            price=price,
        ))
    return candidates


def find_matching_sizes(
    candidate_fits: List[str],
    target_waist: float,
    gender: str,
    nf_products: Dict,
    nf_size_charts: Dict,
) -> List[CandidateProduct]:
    """
    Legacy: Find N&F tag sizes with waist >= target_waist (same as find_matching_sizes_nf).
    """
    return find_matching_sizes_nf(
        candidate_fits, target_waist, gender, nf_products, nf_size_charts
    )
