#!/usr/bin/env python3
"""
Run the Nudie Jeans scraper. Pass sample size as first arg for a small test batch (e.g. 3).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from scrapers.nudie_jeans_scraper import NudieJeansScraper

if __name__ == "__main__":
    sample = int(sys.argv[1]) if len(sys.argv) > 1 else None
    scraper = NudieJeansScraper()
    products = scraper.scrape_all(sample_size=sample)
    print(f"Done. Scraped {len(products)} products.")
    if products:
        out = scraper.save_to_csv(products, "nudie_jeans_products_latest.csv")
        print(f"Latest CSV: {out}")
