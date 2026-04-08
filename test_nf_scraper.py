#!/usr/bin/env python3
"""
Test the new Naked & Famous scraper with a small sample
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import time

if __name__ == "__main__":
    scraper = NakedFamousNewScraper()
    
    # Test getting URLs from one collection first
    print("Testing collection URL extraction...")
    test_urls = scraper.get_product_urls_from_collection(
        "https://nakedandfamousdenim.com/collections/men-jeans",
        "all_mens"
    )
    
    print(f"\nFound {len(test_urls)} product URLs")
    if test_urls:
        print(f"\nFirst 5 URLs:")
        for url in test_urls[:5]:
            print(f"  - {url}")
        
        # Test scraping one product
        print(f"\n\nTesting product scraping...")
        test_product = scraper.scrape_product(test_urls[0])
        if test_product:
            print(f"\n✅ Successfully scraped product:")
            print(f"  Name: {test_product.get('product_name')}")
            print(f"  Fit: {test_product.get('fit_id')}")
            print(f"  Collections: {test_product.get('collections')}")
            print(f"  URL: {test_product.get('nf_product_url')}")
        else:
            print("❌ Failed to scrape product")
    else:
        print("❌ No URLs found")

