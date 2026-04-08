#!/usr/bin/env python3
"""
Test the improved status extraction method
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.tate_yoko_scraper import TateYokoScraper

def test_improved_status():
    """Test the improved status extraction"""
    scraper = TateYokoScraper()
    
    # Test different types of products
    test_urls = [
        "https://tateandyoko.com/collections/jeans/products/weird-guy-deep-sea-selvedge",  # On sale
        "https://tateandyoko.com/collections/jeans/products/true-guy-indigo-selvedge",     # Regular price
    ]
    
    for url in test_urls:
        print(f"\n=== Testing: {url} ===")
        soup = scraper.get_page(url)
        
        if not soup:
            print("Failed to load page")
            continue
            
        # Get product name
        title = soup.find('h1')
        print(f"Product: {title.get_text() if title else 'No title'}")
        
        # Test the improved status extraction
        status = scraper._extract_status(soup)
        print(f"Extracted status: '{status}'")
        
        # Show the price structure for verification
        sale_price = soup.find('span', class_='product-meta__price--new')
        old_price = soup.find('span', class_='product-meta__price--old')
        regular_price = soup.find('span', class_='product-meta__price')
        
        if sale_price and old_price:
            print(f"  Sale price: {sale_price.get_text().strip()}")
            print(f"  Old price: {old_price.get_text().strip()}")
            print("  -> Correctly identified as 'limited' (on sale)")
        elif regular_price:
            print(f"  Regular price: {regular_price.get_text().strip()}")
            print("  -> Correctly identified as 'active' (regular price)")
        else:
            print("  -> No clear price structure found")

if __name__ == "__main__":
    test_improved_status()
