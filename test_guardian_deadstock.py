#!/usr/bin/env python3
"""
Quick test scrape: Guardian Selvedge and Deadstock Super Guy only.
Confirms on-sale detection (regular_price vs sales_price) fixes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import csv

# Only these two products (on-sale; we expect status=on-sales, regular_price > sales_price)
TEST_URLS = [
    ("Super Guy - Guardian Selvedge", "https://nakedandfamousdenim.com/products/naked-famous-super-guy-guardian-selvedge"),
    ("Super Guy - Deadstock Real Gold Selvedge", "https://nakedandfamousdenim.com/products/super-guy-deadstock-real-gold-selvedge"),
]

REQUIRED_COLUMNS = [
    'product_id', 'sku', 'product_name', 'fit_id', 'fabric_id', 'wash_state',
    'gender', 'default_inseam_label', 'colorway',
    'status', 'regular_price', 'sales_price',
    'nf_product_url', 'description_html',
    'release_season', 'run_code', 'notes',
    'denim_weight_oz', 'denim_cat', 'material', 'made_in',
    'product_description', 'collections', 'is_jeans', 'scraped_at'
]

def main():
    scraper = NakedFamousNewScraper()
    results = []

    print("=" * 70)
    print("TEST SCRAPE: Guardian Selvedge + Deadstock Super Guy (on-sale check)")
    print("=" * 70)

    for name, url in TEST_URLS:
        scraper._product_collections[url] = ['test']
        print(f"\nScraping: {name}")
        print(f"  URL: {url}")
        try:
            product = scraper.scrape_product(url)
            if product:
                results.append(product)
                s = product.get('status', '')
                rp = product.get('regular_price', '')
                sp = product.get('sales_price', '')
                print(f"  status={s!r}  regular_price={rp!r}  sales_price={sp!r}  product_id={product.get('product_id','')!r}")
            else:
                print("  Failed: no product data")
        except Exception as e:
            print(f"  Error: {e}")

    if results:
        os.makedirs('data', exist_ok=True)
        out = 'data/test_guardian_deadstock_results.csv'
        with open(out, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS, extrasaction='ignore')
            w.writeheader()
            for r in results:
                w.writerow(r)
        print(f"\nResults saved to: {out}")

if __name__ == "__main__":
    main()
