#!/usr/bin/env python3
"""
More detailed check including line-through elements
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
    
    # Find all price-like elements (containing $)
    all_price_texts = soup.find_all(string=re.compile(r'\$\d+'))
    
    print(f"Found {len(all_price_texts)} price strings\n")
    
    # Show all price elements with their context
    print("All price elements found:")
    for i, price_text in enumerate(all_price_texts[:10], 1):
        if hasattr(price_text, 'parent') and price_text.parent:
            parent = price_text.parent
            text = price_text.strip()
            classes = ' '.join(parent.get('class', []))
            style = parent.get('style', '')
            
            # Check for line-through
            has_line_through = (
                'line-through' in classes.lower() or
                'line-through' in style.lower() or
                parent.name in ['s', 'strike', 'del']
            )
            
            print(f"  {i}. Price: {text}")
            print(f"     Parent: {parent.name}")
            print(f"     Classes: {classes if classes else 'None'}")
            print(f"     Has line-through: {has_line_through}")
            print()
    
    # Look for line-through elements specifically
    line_through_elems = soup.find_all(class_=re.compile(r'line-through', re.I))
    print(f"\nFound {len(line_through_elems)} elements with line-through class:")
    for i, elem in enumerate(line_through_elems[:5], 1):
        text = elem.get_text(strip=True)
        classes = ' '.join(elem.get('class', []))
        print(f"  {i}. {text[:80]}")
        print(f"     Classes: {classes}")
        print()
    
    # Get final status
    status = scraper._extract_status(soup)
    print(f"\nFinal Status: {status}")
    print("="*80)

if __name__ == "__main__":
    # Test with the Deadstock Real Gold product
    test_url = "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge"
    detailed_status_check(test_url)

