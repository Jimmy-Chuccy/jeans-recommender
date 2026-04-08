#!/usr/bin/env python3
"""
Detailed test to see what price elements are being found
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
from bs4 import BeautifulSoup
import re

def detailed_status_check(url: str):
    """Check status extraction in detail"""
    scraper = NakedFamousNewScraper()
    soup = scraper.get_page(url, use_selenium=True)
    
    if not soup:
        print(f"Failed to load {url}")
        return
    
    print(f"\n{'='*80}")
    print(f"Detailed Status Check: {url}")
    print(f"{'='*80}\n")
    
    # Find all price-related elements
    compare_elems = soup.find_all(class_=re.compile(r'compare-at-price|old-price|original-price', re.I))
    sale_elems = soup.find_all(class_=re.compile(r'sale-price|current-price', re.I))
    
    print(f"Found {len(compare_elems)} compare-at-price elements")
    print(f"Found {len(sale_elems)} sale-price elements\n")
    
    # Show compare-at-price elements
    if compare_elems:
        print("Compare-at-price elements:")
        for i, elem in enumerate(compare_elems[:3], 1):
            text = elem.get_text(strip=True)
            classes = ' '.join(elem.get('class', []))
            parent = elem.parent
            parent_classes = ' '.join(parent.get('class', [])) if parent else 'None'
            print(f"  {i}. Text: {text[:60]}")
            print(f"     Classes: {classes}")
            print(f"     Parent classes: {parent_classes}")
            print()
    
    # Show sale-price elements
    if sale_elems:
        print("Sale-price elements:")
        for i, elem in enumerate(sale_elems[:3], 1):
            text = elem.get_text(strip=True)
            classes = ' '.join(elem.get('class', []))
            parent = elem.parent
            parent_classes = ' '.join(parent.get('class', [])) if parent else 'None'
            print(f"  {i}. Text: {text[:60]}")
            print(f"     Classes: {classes}")
            print(f"     Parent classes: {parent_classes}")
            print()
    
    # Check if they're in same container
    if compare_elems and sale_elems:
        print("Checking if compare and sale prices are in same container:")
        for compare_elem in compare_elems[:2]:
            parent = compare_elem.parent
            depth = 0
            while parent and depth < 4:
                sale_in_container = parent.find(class_=re.compile(r'sale-price|current-price', re.I))
                if sale_in_container:
                    print(f"  ✓ Found both in same container at depth {depth}")
                    compare_text = compare_elem.get_text()
                    sale_text = sale_in_container.get_text()
                    compare_match = re.search(r'\$(\d+(?:\.\d+)?)', compare_text)
                    sale_match = re.search(r'\$(\d+(?:\.\d+)?)', sale_text)
                    if compare_match and sale_match:
                        compare_price = float(compare_match.group(1))
                        sale_price = float(sale_match.group(1))
                        print(f"    Compare price: ${compare_price}")
                        print(f"    Sale price: ${sale_price}")
                        print(f"    Sale < Compare: {sale_price < compare_price}")
                parent = parent.parent if parent else None
                depth += 1
    
    # Get final status
    status = scraper._extract_status(soup)
    print(f"\nFinal Status: {status}")
    print("="*80)

if __name__ == "__main__":
    # Test with the Deadstock Real Gold product (should be on sale per user's image)
    test_url = "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge"
    detailed_status_check(test_url)
    
    # Test with another product
    print("\n\n")
    test_url2 = "https://nakedandfamousdenim.com/products/true-guy-sea-island-selvedge-indigo"
    detailed_status_check(test_url2)

