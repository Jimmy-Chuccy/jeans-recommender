#!/usr/bin/env python3
"""
Run N+F size chart pipeline: match T+Y to N+F, backfill imported rows, then scrape
only products that don't have measurements. Output: naked_famous_size_charts_<timestamp>.csv
and naked_famous_size_charts_latest.csv.

Uses:
- data/processed/naked_famous_products_20260302_091952.csv (jeans only)
- data/processed/tate_yoko_size_charts.csv
"""

import sys
import os
import re
import csv
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Paths
PRODUCTS_CSV = "data/processed/naked_famous_products_20260302_091952.csv"
TY_SIZE_CHARTS_CSV = "data/processed/tate_yoko_size_charts.csv"
OUTPUT_DIR = "data/processed"
SIZE_CHART_FIELDS = [
    "product_id", "nf_product_url", "tag_size",
    "waist", "front_rise", "back_rise", "upper_thigh", "knee", "leg_opening", "inseam",
    "measurement_source", "scraped_at",
]


def normalize_ty_slug(ty_product_url: str) -> str:
    """Extract slug from T+Y product URL: path after /products/"""
    if "/products/" not in ty_product_url:
        return ""
    slug = ty_product_url.split("/products/")[-1].strip("/").split("?")[0]
    return slug.lower().strip()


def normalize_nf_slug_from_url(nf_product_url: str) -> str:
    """Extract and normalize slug from N+F product URL for matching."""
    if "/products/" not in nf_product_url:
        return ""
    slug = nf_product_url.split("/products/")[-1].strip("/").split("?")[0]
    slug = slug.lower()
    # Strip known N+F prefixes (site restructuring)
    for prefix in ("naked-famous-denim-", "naked-famous-"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
            break
    # Strip variant suffix like -1, -2 for matching
    slug = re.sub(r"-\d+$", "", slug)
    return slug


def slug_from_product_name(product_name: str) -> str:
    """Derive canonical slug from product name for fallback matching."""
    if not product_name:
        return ""
    s = product_name.lower().strip()
    s = s.replace(" - ", "-").replace(" ", "-").replace("&", "and")
    s = re.sub(r"[^\w\-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def load_nf_jeans_products(path: str) -> List[Dict]:
    """Load N+F product CSV and return rows where is_jeans is 'yes'."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("is_jeans") or "").strip().lower() == "yes":
                rows.append(row)
    return rows


def load_ty_size_charts(path: str) -> List[Dict]:
    """Load T+Y size chart CSV."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_ty_to_nf_mapping(
    nf_products: List[Dict], ty_rows: List[Dict]
) -> Dict[str, Tuple[str, str]]:
    """
    Build mapping: ty_product_url -> (product_id, nf_product_url).
    Uses normalized URL slug first, then product_name slug fallback.
    """
    # Index N+F by normalized URL slug and by product_name slug
    by_url_slug = {}
    by_name_slug = {}
    for p in nf_products:
        pid = (p.get("product_id") or "").strip()
        url = (p.get("nf_product_url") or "").strip()
        name = (p.get("product_name") or "").strip()
        if not pid or not url:
            continue
        u_slug = normalize_nf_slug_from_url(url)
        if u_slug:
            by_url_slug[u_slug] = (pid, url)
        n_slug = slug_from_product_name(name)
        if n_slug and n_slug not in by_name_slug:
            by_name_slug[n_slug] = (pid, url)
    # Unique T+Y product URLs
    ty_urls = list({r["product_url"] for r in ty_rows})
    mapping = {}
    for ty_url in ty_urls:
        ty_slug = normalize_ty_slug(ty_url)
        if not ty_slug:
            continue
        if ty_slug in by_url_slug:
            mapping[ty_url] = by_url_slug[ty_slug]
            continue
        if ty_slug in by_name_slug:
            mapping[ty_url] = by_name_slug[ty_slug]
            continue
        # Try without variant suffix on ty_slug (e.g. ty has -1)
        ty_base = re.sub(r"-\d+$", "", ty_slug)
        if ty_base in by_url_slug:
            mapping[ty_url] = by_url_slug[ty_base]
        elif ty_base in by_name_slug:
            mapping[ty_url] = by_name_slug[ty_base]
    return mapping


def backfill_from_ty(
    ty_rows: List[Dict],
    ty_to_nf: Dict[str, Tuple[str, str]],
    scraped_at: str,
) -> List[Dict]:
    """Convert T+Y size chart rows to N+F schema with measurement_source='imported'."""
    out = []
    for row in ty_rows:
        ty_url = (row.get("product_url") or "").strip()
        if ty_url not in ty_to_nf:
            continue
        product_id, nf_product_url = ty_to_nf[ty_url]
        out.append({
            "product_id": product_id,
            "nf_product_url": nf_product_url,
            "tag_size": (row.get("tag_size") or "").strip(),
            "waist": row.get("waist"),
            "front_rise": row.get("front_rise"),
            "back_rise": row.get("back_rise"),
            "upper_thigh": row.get("upper_thigh"),
            "knee": row.get("knee"),
            "leg_opening": row.get("leg_opening"),
            "inseam": row.get("inseam"),
            "measurement_source": "imported",
            "scraped_at": scraped_at,
        })
    return out


def main():
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("nf_size_charts")

    no_scrape = "--no-scrape" in sys.argv
    if no_scrape:
        logger.info("Running with --no-scrape: match and backfill only, no Selenium scraping")

    scraped_at = datetime.now().isoformat()

    # 1) Load N+F jeans and T+Y size charts
    if not os.path.isfile(PRODUCTS_CSV):
        logger.error(f"Product CSV not found: {PRODUCTS_CSV}")
        return 1
    if not os.path.isfile(TY_SIZE_CHARTS_CSV):
        logger.error(f"T+Y size chart CSV not found: {TY_SIZE_CHARTS_CSV}")
        return 1

    nf_products = load_nf_jeans_products(PRODUCTS_CSV)
    ty_rows = load_ty_size_charts(TY_SIZE_CHARTS_CSV)
    logger.info(f"Loaded {len(nf_products)} N+F jeans products and {len(ty_rows)} T+Y size chart rows")

    # 2) Match T+Y -> N+F and backfill
    ty_to_nf = build_ty_to_nf_mapping(nf_products, ty_rows)
    logger.info(f"Matched {len(ty_to_nf)} T+Y products to N+F")
    imported_rows = backfill_from_ty(ty_rows, ty_to_nf, scraped_at)
    logger.info(f"Backfilled {len(imported_rows)} measurement rows from T+Y")

    # 3) Gap: N+F jeans that have no measurement row yet
    product_ids_with_measurements = {r["product_id"] for r in imported_rows}
    nf_by_id = {p["product_id"]: p for p in nf_products}
    gap_products = [
        p for p in nf_products
        if p["product_id"] not in product_ids_with_measurements
    ]
    logger.info(f"Products to scrape (gap): {len(gap_products)}")

    # 4) Scrape size charts for gap products (skip if --no-scrape)
    scraped_rows = []
    if not no_scrape:
        from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
        scraper = NakedFamousNewScraper()
        for i, p in enumerate(gap_products, 1):
            url = (p.get("nf_product_url") or "").strip()
            pid = (p.get("product_id") or "").strip()
            if not url or not pid:
                continue
            logger.info(f"Scraping size chart {i}/{len(gap_products)}: {pid}")
            try:
                rows = scraper.scrape_size_chart_for_product(url, pid)
                for r in rows:
                    r["measurement_source"] = "scraped"
                    r["scraped_at"] = scraped_at
                    scraped_rows.append(r)
            except Exception as e:
                logger.warning(f"Failed to scrape size chart for {url}: {e}")
            time.sleep(2)
    else:
        logger.info("Skipping scrape (--no-scrape). Output will contain imported rows only.")

    # 5) Combine and save
    all_rows = imported_rows + scraped_rows
    logger.info(f"Total measurement rows: {len(all_rows)} (imported: {len(imported_rows)}, scraped: {len(scraped_rows)})")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for filename in (f"naked_famous_size_charts_{timestamp}.csv", "naked_famous_size_charts_latest.csv"):
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SIZE_CHART_FIELDS, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for r in all_rows:
                writer.writerow({k: r.get(k, "") for k in SIZE_CHART_FIELDS})
        logger.info(f"Saved {len(all_rows)} rows to {filepath}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
