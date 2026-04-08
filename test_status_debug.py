#!/usr/bin/env python3
"""
Debug why status extraction isn't working
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
from bs4 import BeautifulSoup
import re

def debug_status(url: str):
    """Debug status extraction"""
    scraper = NakedFamousNewScraper()
    soup = scraper.get_page(url, use_selenium=True)
    
    if not soup:
        print(f"Failed to load {url}")
        return
    
    print(f"\n{'='*80}")
    print(f"Debug Status: {url}")
    print(f"{'='*80}\n")
    
    # Find compare-at-price elements - check both element classes and parent classes
    compare_elems = soup.find_all(class_=re.compile(r'compare-at-price', re.I))
    print(f"Found {len(compare_elems)} elements with compare-at-price class")
    
    # Also find elements whose parent has compare-at-price class
    parent_compare_elems = []
    for elem in soup.find_all(['span', 'div', 'p', 's']):
        parent = elem.parent
        if parent:
            parent_classes = ' '.join(parent.get('class', []))
            if 'compare-at-price' in parent_classes.lower():
                parent_compare_elems.append(elem)
    
    print(f"Found {len(parent_compare_elems)} elements with parent having compare-at-price class")
    all_compare = list(set(compare_elems + parent_compare_elems))
    print(f"Total unique compare elements: {len(all_compare)}\n")
    
    for i, compare_elem in enumerate(all_compare[:3], 1):
        print(f"Compare element {i}:")
        compare_text = compare_elem.get_text(strip=True)
        compare_classes = ' '.join(compare_elem.get('class', []))
        print(f"  Text: {compare_text}")
        print(f"  Classes: {compare_classes}")
        
        # Check if crossed out
        is_crossed = 'line-through' in compare_classes.lower()
        print(f"  Has line-through: {is_crossed}")
        
        # Extract price
        compare_match = re.search(r'\$(\d+(?:\.\d+)?)', compare_text)
        if compare_match:
            compare_price = float(compare_match.group(1))
            print(f"  Price: ${compare_price}")
            
            # Check parent and siblings
            parent = compare_elem.parent
            print(f"  Parent: {parent.name if parent else 'None'}")
            if parent:
                print(f"  Parent classes: {' '.join(parent.get('class', []))}")
                
                # Look for sale-price in same parent
                sale_in_parent = parent.find(class_=re.compile(r'sale-price', re.I))
                if sale_in_parent:
                    sale_text = sale_in_parent.get_text(strip=True)
                    sale_match = re.search(r'\$(\d+(?:\.\d+)?)', sale_text)
                    if sale_match:
                        sale_price = float(sale_match.group(1))
                        print(f"  ✓ Found sale-price in same parent: ${sale_price}")
                        print(f"  Sale < Compare: {sale_price < compare_price}")
                        if sale_price < compare_price and is_crossed:
                            print(f"  ✓ SHOULD RETURN 'on-sales'")
                else:
                    print(f"  ✗ No sale-price in same parent")
                
                # Check siblings
                if parent.parent:
                    siblings = parent.parent.find_all(class_=re.compile(r'sale-price', re.I))
                    if siblings:
                        print(f"  Found {len(siblings)} sale-price siblings")
                        for sib in siblings[:2]:
                            sib_text = sib.get_text(strip=True)
                            sib_match = re.search(r'\$(\d+(?:\.\d+)?)', sib_text)
                            if sib_match:
                                sib_price = float(sib_match.group(1))
                                print(f"    Sibling price: ${sib_price}")
                                if sib_price < compare_price and is_crossed:
                                    print(f"    ✓ SHOULD RETURN 'on-sales'")
        print()
    
    # Test the actual method
    status = scraper._extract_status(soup)
    print(f"Final Status: {status}")
    print("="*80)

if __name__ == "__main__":
    test_url = "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge"
    debug_status(test_url)

