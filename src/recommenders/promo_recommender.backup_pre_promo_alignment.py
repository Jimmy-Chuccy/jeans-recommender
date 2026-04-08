"""
Discount / on-sales recommendations when user has no fit preference and no reference.
Benchmark: straight fit (Nudie Rad Rufus at closest tag size). Up to 10 products; N&F-heavy.
"""

from typing import List, Dict, Optional, Any

from .models import CandidateProduct
from .data_loader import (
    load_nf_products,
    load_nf_size_charts,
    load_levis_products,
    load_levis_measurements,
    load_nudie_measurements,
)

_CACHE = {}
_MAX_TOTAL = 10
_MAX_NF = 7
_MAX_LEVIS = 5
_ON_SALES = "on-sales"
_BASELINE = 32
_BENCHMARK_FIT_ID = "rad_rufus"


def _load():
    global _CACHE
    if not _CACHE:
        _CACHE["nf_products"] = load_nf_products()
        _CACHE["nf_charts"] = load_nf_size_charts()
        _CACHE["levis_products"] = load_levis_products()
        _CACHE["levis_meas"] = load_levis_measurements()
        _CACHE["nudie_meas"] = load_nudie_measurements()
    return _CACHE


def _benchmark_rad_rufus(user_size: int, nudie_meas: dict) -> Dict[str, float]:
    fit_sizes = nudie_meas.get(_BENCHMARK_FIT_ID) or {}
    if not fit_sizes:
        return {"front_rise": 11.0, "knee": 17.0, "leg_opening": 16.0}

    best_tag = min(fit_sizes.keys(), key=lambda t: abs(int(t) - int(user_size)))
    m = fit_sizes.get(best_tag) or {}
    return {
        "front_rise": m.get("front_rise") or 11.0,
        "knee": m.get("knee") or 17.0,
        "leg_opening": m.get("leg_opening") or 16.0,
    }


def _score_vs_benchmark(
    meas: Dict[str, float],
    bench: Dict[str, float],
    rise_pref: Optional[str],
    thigh_pref: Optional[str],
    leg_pref: Optional[str],
) -> float:
    cr = meas.get("front_rise") or 0
    ck = meas.get("knee") or 0
    cl = meas.get("leg_opening") or 0
    br, bk, bl = bench["front_rise"], bench["knee"], bench["leg_opening"]
    score = 0.0

    def band_similar(c, b, width=1.5):
        return max(0.0, 100.0 - abs(c - b) / max(width, 0.01) * 30)

    if rise_pref == "higher":
        score += min(100.0, max(0.0, (cr - br) / max(br, 0.01) * 80 + 40))
    elif rise_pref == "lower":
        score += min(100.0, max(0.0, (br - cr) / max(br, 0.01) * 80 + 40))
    else:
        score += band_similar(cr, br, 1.2)

    if thigh_pref == "more":
        score += min(100.0, max(0.0, (ck - bk) / max(bk, 0.01) * 80 + 40))
    elif thigh_pref == "less":
        score += min(100.0, max(0.0, (bk - ck) / max(bk, 0.01) * 80 + 40))
    else:
        score += band_similar(ck, bk, 1.5)

    if leg_pref == "wider":
        score += min(100.0, max(0.0, (cl - bl) / max(bl, 0.01) * 80 + 40))
    elif leg_pref == "narrower":
        score += min(100.0, max(0.0, (bl - cl) / max(bl, 0.01) * 80 + 40))
    else:
        score += band_similar(cl, bl, 1.2)

    return score


def _nf_on_sales_candidates(
    target_waist: float,
    user_size: int,
    gender: str,
    nf_products: dict,
    nf_charts: dict,
) -> List[CandidateProduct]:
    out = []
    for fit_id, products in nf_products.items():
        for p in products:
            if (p.get("status") or "").strip().lower() != _ON_SALES:
                continue
            if p.get("gender") != gender:
                continue
            ij = (p.get("is_jeans") or "").strip().lower()
            if ij in ("no", "false", "0"):
                continue
            url = (p.get("product_url") or "").strip()
            if not url or url not in nf_charts:
                continue
            best = None
            best_sc = float("inf")
            est = int(round(target_waist))
            for tag, m in nf_charts[url].items():
                w = m.get("waist")
                if w is not None and w >= target_waist:
                    sc = abs(tag - est) * 10 + (w - target_waist)
                    if sc < best_sc:
                        best_sc = sc
                        best = (tag, m)
            if not best:
                md = float("inf")
                for tag, m in nf_charts[url].items():
                    w = m.get("waist")
                    if w is not None and abs(w - target_waist) < md:
                        md = abs(w - target_waist)
                        best = (tag, m)
            if not best:
                continue
            tag, m = best
            price = (p.get("price") or "").strip() or None
            out.append(
                CandidateProduct(
                    brand="nf",
                    product_id=p.get("product_id", ""),
                    product_name=p.get("product_name", ""),
                    fit_id=fit_id,
                    product_url=url,
                    tag_size=tag,
                    measurements={
                        "waist": m.get("waist") or 0,
                        "front_rise": m.get("front_rise") or 0,
                        "knee": m.get("knee") or 0,
                        "leg_opening": m.get("leg_opening") or 0,
                    },
                    price=price,
                )
            )
    return out


def _levis_on_sales_candidates(
    user_size: int,
    gender: str,
    levis_products: List[dict],
    levis_meas: dict,
) -> List[CandidateProduct]:
    out = []
    sc = user_size / float(_BASELINE)
    for p in levis_products:
        if (p.get("status") or "").strip().lower() != _ON_SALES:
            continue
        if (p.get("gender") or "").strip().lower() != gender:
            continue
        fid = (p.get("fit_id") or "").strip()
        m = levis_meas.get(fid)
        if not m:
            continue
        meas = {
            "waist": float(user_size),
            "front_rise": (m.get("front_rise") or 0) * sc,
            "knee": (m.get("knee") or 0) * sc,
            "leg_opening": (m.get("leg_opening") or 0) * sc,
        }
        price = (p.get("price") or "").strip() or None
        out.append(
            CandidateProduct(
                brand="levis",
                product_id=p.get("product_id", ""),
                product_name=p.get("product_name", ""),
                fit_id=fid,
                product_url=p.get("product_url", ""),
                tag_size=user_size,
                measurements=meas,
                price=price,
            )
        )
    return out


def recommend_promotional(
    user_size: int,
    rise_preference: Optional[str],
    thigh_preference: Optional[str],
    leg_opening_preference: Optional[str],
    gender: str = "mens",
) -> List[Dict[str, str]]:
    """
    On-sales products only. Nudie skipped (no on-sales in current data).
    Up to 10 items, favor N&F (max 7) then Levi's (max 5), fill to 10.
    """
    data = _load()
    target_waist = float(user_size)
    bench = _benchmark_rad_rufus(user_size, data["nudie_meas"])

    nf_list = _nf_on_sales_candidates(
        target_waist, user_size, gender, data["nf_products"], data["nf_charts"]
    )
    lv_list = _levis_on_sales_candidates(
        user_size, gender, data["levis_products"], data["levis_meas"]
    )

    for c in nf_list:
        c.score = _score_vs_benchmark(
            c.measurements, bench, rise_preference, thigh_preference, leg_opening_preference
        )
    for c in lv_list:
        c.score = _score_vs_benchmark(
            c.measurements, bench, rise_preference, thigh_preference, leg_opening_preference
        )

    nf_list.sort(key=lambda x: -x.score)
    lv_list.sort(key=lambda x: -x.score)

    # N&F-heavy: up to 7 N&F + Levi's to 10 total
    picked = list(nf_list[:_MAX_NF])
    for c in lv_list:
        if len(picked) >= _MAX_TOTAL:
            break
        picked.append(c)
    if len(picked) < _MAX_TOTAL:
        seen = {c.product_url for c in picked}
        for c in nf_list[_MAX_NF:] + lv_list[_MAX_LEVIS:]:
            if len(picked) >= _MAX_TOTAL:
                break
            if c.product_url in seen:
                continue
            picked.append(c)
            seen.add(c.product_url)

    return [
        {
            "brand": c.brand,
            "product_name": c.product_name,
            "tag_size": c.tag_size,
            "price": c.price or "",
            "product_url": c.product_url,
        }
        for c in picked[:_MAX_TOTAL]
    ]
