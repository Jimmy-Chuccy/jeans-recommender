"""
Data loading utilities for CSV files.

Referenced datasets:
- N&F: naked_famous_products_latest.csv, naked_famous_size_charts_latest.csv, fits_new.csv
- Nudie: nudie_jeans_products_latest.csv, Nudie_Jeans_measurements_manual.csv, Nudie_Jeans_fits.csv
- Levi's: levis_product_manual_new_20260317.csv, levis_measurements_manual.csv
"""

import csv
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict


# Default filenames (use _latest for most recent scraped data)
NF_PRODUCTS_FILE = "naked_famous_products_latest.csv"
NF_SIZE_CHARTS_FILE = "naked_famous_size_charts_latest.csv"
NF_FITS_FILE = "fits_new.csv"
NUDIE_PRODUCTS_FILE = "nudie_jeans_products_latest.csv"
NUDIE_MEASUREMENTS_FILE = "Nudie_Jeans_measurements_manual.csv"
NUDIE_FITS_FILE = "Nudie_Jeans_fits.csv"
LEVIS_PRODUCTS_FILE = "levis_product_manual_new_20260317.csv"
LEVIS_MEASUREMENTS_FILE = "levis_measurements_manual.csv"


def get_data_path(filename: str) -> str:
    """Get absolute path to data file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "processed", filename)


def _read_float(row: Dict[str, str], key: str) -> Optional[float]:
    val = row.get(key, "").strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Levi's
# ---------------------------------------------------------------------------


def load_levis_measurements() -> Dict[str, Dict[str, float]]:
    """
    Load Levi's measurements from levis_measurements_manual.csv
    Returns: {fit_id: {measurement_type: value}}
    Example: {"501": {"waist": 32, "front_rise": 11.25, "knee": 17.5, "leg_opening": 16}}
    """
    measurements = {}
    filepath = get_data_path(LEVIS_MEASUREMENTS_FILE)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Levi's measurements file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fit_id = row.get("fit_id", "").strip()
            if not fit_id:
                continue
            measurements[fit_id] = {
                "waist": _read_float(row, "waist"),
                "front_rise": _read_float(row, "front_rise"),
                "upper_thigh": _read_float(row, "upper_thigh"),
                "knee": _read_float(row, "knee"),
                "leg_opening": _read_float(row, "leg_opening"),
            }
    return measurements


def load_levis_products() -> List[Dict[str, Any]]:
    """
    Load Levi's product catalog from levis_product_manual_new_20260317.csv
    Returns: list of dicts with product_id, product_name, fit_id, gender, product_url, price, etc.
    """
    filepath = get_data_path(LEVIS_PRODUCTS_FILE)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Levi's products file not found: {filepath}")
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


# ---------------------------------------------------------------------------
# Naked & Famous
# ---------------------------------------------------------------------------


def load_nf_products() -> Dict[str, List[Dict]]:
    """
    Load N&F products from naked_famous_products_latest.csv, grouped by fit_id.
    Returns: {fit_id: [{product_id, product_name, product_url (nf_product_url), fit_id, gender, status}, ...]}
    """
    products_by_fit = defaultdict(list)
    filepath = get_data_path(NF_PRODUCTS_FILE)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"N&F products file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fit_id = (row.get("fit_id") or "").strip()
            if not fit_id:
                continue
            product_url = (row.get("nf_product_url") or "").strip()
            price = (row.get("sales_price") or row.get("regular_price") or "").strip() or None
            products_by_fit[fit_id].append({
                "product_id": row.get("product_id", ""),
                "product_name": row.get("product_name", ""),
                "product_url": product_url,
                "fit_id": fit_id,
                "gender": (row.get("gender") or "").strip() or "mens",
                "status": (row.get("status") or "").strip() or "regular",
                "price": price,
            })
    return dict(products_by_fit)


def load_nf_size_charts() -> Dict[str, Dict[int, Dict[str, float]]]:
    """
    Load N&F size charts from naked_famous_size_charts_latest.csv.
    Returns: {product_url (nf_product_url): {tag_size: {waist, front_rise, upper_thigh, knee, leg_opening}}}
    """
    size_charts = defaultdict(dict)
    filepath = get_data_path(NF_SIZE_CHARTS_FILE)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"N&F size charts file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_url = (row.get("nf_product_url") or "").strip()
            if not product_url:
                continue
            try:
                tag_size = int(row.get("tag_size", "").strip())
            except (ValueError, TypeError):
                continue
            measurements = {}
            for field in ["waist", "front_rise", "upper_thigh", "knee", "leg_opening"]:
                measurements[field] = _read_float(row, field)
            size_charts[product_url][tag_size] = measurements
    return dict(size_charts)


def load_nf_fits() -> List[Dict[str, Any]]:
    """
    Load N&F fit metadata from fits_new.csv.
    Returns: list of dicts with fit_id, fit_name, gender, rise_class, thigh_room, leg_profile, etc.
    """
    filepath = get_data_path(NF_FITS_FILE)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"N&F fits file not found: {filepath}")
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("fit_id") or "").strip():
                rows.append(dict(row))
    return rows


# ---------------------------------------------------------------------------
# Nudie Jeans
# ---------------------------------------------------------------------------


def load_nudie_products() -> Dict[str, List[Dict]]:
    """
    Load Nudie Jeans products from nudie_jeans_products_latest.csv, grouped by fit_id.
    Returns: {fit_id: [{product_id, product_name, product_url (nudie_product_url), fit_id, gender, status}, ...]}
    """
    products_by_fit = defaultdict(list)
    filepath = get_data_path(NUDIE_PRODUCTS_FILE)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Nudie products file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fit_id = (row.get("fit_id") or "").strip()
            if not fit_id:
                continue
            product_url = (row.get("nudie_product_url") or "").strip()
            price = (row.get("sales_price") or row.get("regular_price") or "").strip() or None
            products_by_fit[fit_id].append({
                "product_id": row.get("product_id", ""),
                "product_name": row.get("product_name", ""),
                "product_url": product_url,
                "fit_id": fit_id,
                "gender": (row.get("gender") or "").strip() or "mens",
                "status": (row.get("status") or "").strip() or "regular",
                "price": price,
            })
    return dict(products_by_fit)


def load_nudie_measurements() -> Dict[str, Dict[int, Dict[str, float]]]:
    """
    Load Nudie measurements from Nudie_Jeans_measurements_manual.csv.
    Nudie measurements are per fit_id (not per product). Returns same measurement shape as N&F for compatibility.
    Returns: {fit_id: {tag_size: {waist, front_rise, upper_thigh, knee, leg_opening}}}
    """
    by_fit: Dict[str, Dict[int, Dict[str, float]]] = defaultdict(dict)
    filepath = get_data_path(NUDIE_MEASUREMENTS_FILE)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Nudie measurements file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fit_id = (row.get("fit_id") or "").strip()
            if not fit_id:
                continue
            try:
                tag_size = int(row.get("tag_size", "").strip())
            except (ValueError, TypeError):
                continue
            measurements = {
                "waist": _read_float(row, "waist"),
                "front_rise": _read_float(row, "front_rise"),
                "upper_thigh": _read_float(row, "upper_thigh"),
                "knee": _read_float(row, "knee"),
                "leg_opening": _read_float(row, "leg_opening"),
            }
            by_fit[fit_id][tag_size] = measurements
    return dict(by_fit)


def load_nudie_fits() -> List[Dict[str, Any]]:
    """
    Load Nudie fit metadata from Nudie_Jeans_fits.csv.
    Returns: list of dicts with fit_id, fit_name, gender, rise_class, thigh_room, leg_profile, etc.
    """
    filepath = get_data_path(NUDIE_FITS_FILE)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Nudie fits file not found: {filepath}")
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("fit_id") or "").strip():
                rows.append(dict(row))
    return rows
