#!/usr/bin/env python3
"""
Test the new extraction methods for SKU, denim_weight, denim_cat, and made_in
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.tate_yoko_scraper import TateYokoScraper

def test_new_fields():
    """Test the new field extraction methods"""
    scraper = TateYokoScraper()
    
    # Test URL from the example
    test_url = "https://tateandyoko.com/collections/jeans/products/strong-guy-solid-black-selvedge"
    print(f"=== Testing: {test_url} ===")
    
    soup = scraper.get_page(test_url)
    if not soup:
        print("Failed to load page")
        return
        
    # Test each new extraction method
    print("\n--- Testing New Field Extractions ---")
    
    sku = scraper._extract_sku(soup)
    print(f"SKU: '{sku}'")
    
    denim_weight = scraper._extract_denim_weight(soup)
    print(f"Denim Weight: '{denim_weight}'")
    
    denim_cat = scraper._extract_denim_category(soup)
    print(f"Denim Category: '{denim_cat}'")
    
    made_in = scraper._extract_made_in(soup)
    print(f"Made In: '{made_in}'")
    
    # Test a few more products to see variety
    test_urls = [
        "https://tateandyoko.com/collections/jeans/products/weird-guy-deep-sea-selvedge",
        "https://tateandyoko.com/collections/jeans/products/true-guy-indigo-selvedge"
    ]
    
    for url in test_urls:
        print(f"\n=== Testing: {url} ===")
        soup = scraper.get_page(url)
        if soup:
            sku = scraper._extract_sku(soup)
            denim_weight = scraper._extract_denim_weight(soup)
            denim_cat = scraper._extract_denim_category(soup)
            made_in = scraper._extract_made_in(soup)
            
            print(f"SKU: '{sku}'")
            print(f"Denim Weight: '{denim_weight}'")
            print(f"Denim Category: '{denim_cat}'")
            print(f"Made In: '{made_in}'")

if __name__ == "__main__":
    test_new_fields()
