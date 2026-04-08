"""
Fit mapping utilities for preferences and cross-brand fit options
"""

from typing import List, Optional, Dict, Any


# N&F: preference -> fit_ids
PREFERENCE_TO_NF_FITS = {
    "relaxed": ["strong_guy", "easy_guy"],
    "slim": ["super_guy", "true_guy", "weird_guy"],
    "tapered": ["weird_guy", "easy_guy", "super_guy"],
    "straight": ["true_guy", "strong_guy"],
    "bootcut": ["groovy_guy"],
    "skinny": ["super_guy", "stacked_guy"],
}

# Nudie: preference -> fit_ids (by leg_profile / thigh_room)
PREFERENCE_TO_NUDIE_FITS = {
    "relaxed": ["tuff_tony", "loud_larry", "steady_eddie_ii", "rad_rufus"],
    "slim": ["grim_tim", "lean_dean", "slim_jim", "solid_ollie", "gritty_jackson", "tight_terry"],
    "tapered": ["lean_dean", "solid_ollie", "steady_eddie_ii", "tight_terry"],
    "straight": ["grim_tim", "slim_jim", "gritty_jackson", "rad_rufus", "tuff_tony"],
    "bootcut": ["slim_jim", "flare_glenn"],
    "skinny": ["tight_terry", "lean_dean"],
}

# Levi's: preference -> model numbers
PREFERENCE_TO_LEVIS_FITS = {
    "relaxed": ["550", "501", "505"],
    "slim": ["511", "514"],
    "tapered": ["541", "512"],
    "straight": ["501", "514", "505"],
    "bootcut": ["517"],
    "skinny": ["511"],
}

# Infer style preference when user skipped fit question but named a reference model
NF_MODEL_TO_PREFERENCE: Dict[str, str] = {
    "super_guy": "skinny",
    "stacked_guy": "skinny",
    "weird_guy": "tapered",
    "easy_guy": "relaxed",
    "true_guy": "straight",
    "strong_guy": "relaxed",
    "groovy_guy": "bootcut",
    "true_girl": "straight",
    "super_girl": "skinny",
    "bestie": "tapered",
    "maudie": "relaxed",
    "wide_leg_trouser": "relaxed",
    "wide_wild_west": "relaxed",
}

NUDIE_MODEL_TO_PREFERENCE: Dict[str, str] = {
    "tight_terry": "skinny",
    "lean_dean": "tapered",
    "solid_ollie": "tapered",
    "steady_eddie_ii": "tapered",
    "grim_tim": "slim",
    "slim_jim": "slim",
    "gritty_jackson": "straight",
    "rad_rufus": "straight",
    "tuff_tony": "relaxed",
    "loud_larry": "relaxed",
    "flare_glenn": "bootcut",
}

LEVIS_MODEL_TO_PREFERENCE: Dict[str, str] = {
    "501": "straight",
    "505": "straight",
    "514": "straight",
    "511": "slim",
    "512": "tapered",
    "517": "bootcut",
    "541": "tapered",
    "550": "relaxed",
}


def infer_fit_preference_from_reference(brand: str, model_id: str) -> Optional[str]:
    """
    When user skipped fit style but picked a reference model, map that model to
    a preference (relaxed, slim, tapered, straight, bootcut, skinny).
    """
    if not model_id:
        return None
    mid = model_id.strip().lower()
    if brand == "nf":
        return NF_MODEL_TO_PREFERENCE.get(mid)
    if brand == "nudie":
        return NUDIE_MODEL_TO_PREFERENCE.get(mid)
    if brand == "levis":
        return LEVIS_MODEL_TO_PREFERENCE.get(mid)
    return None


# Levi's fit options for "what jeans do you wear" (id -> display name)
LEVIS_FIT_OPTIONS = [
    {"id": "501", "name": "501 Original Fit"},
    {"id": "511", "name": "511 Slim Fit"},
    {"id": "505", "name": "505 Regular Fit"},
    {"id": "514", "name": "514 Straight Fit"},
    {"id": "517", "name": "517 Bootcut"},
    {"id": "541", "name": "541 Athletic Taper"},
    {"id": "550", "name": "550 Relaxed Fit"},
]

# Backwards compatibility
PREFERENCE_TO_FITS = PREFERENCE_TO_NF_FITS


def get_candidate_fits(preference: Optional[str], levis_model: Optional[str] = None) -> List[str]:
    """Get candidate N&F fit_ids (kept for backwards compatibility)."""
    if preference and preference.lower() in PREFERENCE_TO_NF_FITS:
        return PREFERENCE_TO_NF_FITS[preference.lower()]
    if levis_model:
        return map_levis_to_nf_fit(levis_model)
    return []


def get_candidate_fits_for_brand(brand: str, preference: Optional[str]) -> List[str]:
    """
    Get candidate fit_ids for a brand based on user's fit preference.
    brand: "nf" | "nudie" | "levis"
    """
    if not preference:
        return []
    pref = preference.lower()
    if brand == "nf" and pref in PREFERENCE_TO_NF_FITS:
        return PREFERENCE_TO_NF_FITS[pref]
    if brand == "nudie" and pref in PREFERENCE_TO_NUDIE_FITS:
        return PREFERENCE_TO_NUDIE_FITS[pref]
    if brand == "levis" and pref in PREFERENCE_TO_LEVIS_FITS:
        return PREFERENCE_TO_LEVIS_FITS[pref]
    return []


def map_levis_to_nf_fit(levis_model: str) -> List[str]:
    """Map Levi's model number to N&F fit_ids."""
    levis_to_nf = {
        "501": ["strong_guy", "weird_guy"],
        "511": ["super_guy", "weird_guy"],
        "512": ["weird_guy", "easy_guy"],
        "505": ["strong_guy", "true_guy"],
        "514": ["true_guy", "strong_guy"],
        "517": ["groovy_guy"],
        "541": ["easy_guy", "weird_guy"],
        "550": ["strong_guy", "easy_guy"],
    }
    return levis_to_nf.get(str(levis_model).strip(), [])


def get_fit_options_for_brand(brand: str, gender: str = "mens") -> List[Dict[str, str]]:
    """
    Get list of fit options {id, name} for the chatbot "What jeans do you wear from X?".
    For Levi's returns static list. For N&F and Nudie loads from data_loader (avoids circular import by lazy load).
    """
    if brand == "levis":
        return LEVIS_FIT_OPTIONS.copy()

    # Lazy load to avoid circular import
    from .data_loader import load_nf_fits, load_nudie_fits

    if brand == "nf":
        fits = load_nf_fits()
        # Filter by gender: "men" / "women" in CSV vs "mens"
        out = []
        for row in fits:
            g = (row.get("gender") or "").strip().lower()
            if gender == "mens" and g == "men":
                out.append({"id": (row.get("fit_id") or "").strip(), "name": (row.get("fit_name") or "").strip()})
            elif gender == "womens" and g == "women":
                out.append({"id": (row.get("fit_id") or "").strip(), "name": (row.get("fit_name") or "").strip()})
            elif not g:
                out.append({"id": (row.get("fit_id") or "").strip(), "name": (row.get("fit_name") or "").strip()})
        return out if out else [{"id": r.get("fit_id", "").strip(), "name": r.get("fit_name", "").strip()} for r in fits]

    if brand == "nudie":
        fits = load_nudie_fits()
        out = []
        for row in fits:
            g = (row.get("gender") or "").strip().lower()
            if gender == "mens" and g == "men":
                out.append({"id": (row.get("fit_id") or "").strip(), "name": (row.get("fit_name") or "").strip()})
            elif gender == "womens" and g == "women":
                out.append({"id": (row.get("fit_id") or "").strip(), "name": (row.get("fit_name") or "").strip()})
            elif not g:
                out.append({"id": (row.get("fit_id") or "").strip(), "name": (row.get("fit_name") or "").strip()})
        return out if out else [{"id": r.get("fit_id", "").strip(), "name": r.get("fit_name", "").strip()} for r in fits]

    return []
