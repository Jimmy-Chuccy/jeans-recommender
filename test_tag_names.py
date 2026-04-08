#!/usr/bin/env python3
"""
Check if compare-at-price is a tag name
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
from bs4 import BeautifulSoup
import re

def check_tags(url: str):
    """Check for compare-at-price and sale-price tags"""
    scraper = NakedFamousNewScraper()
    soup = scraper.get_page(url, use_selenium=True)
    
    if not soup:
        print(f"Failed to load {url}")
        return
    
    print(f"\n{'='*80}")
    print(f"Checking tag names: {url}")
    print(f"{'='*80}\n")
    
    # Check if compare-at-price is a tag name
    compare_tags = soup.find_all('compare-at-price')
    print(f"Found {len(compare_tags)} <compare-at-price> tags")
    for i, tag in enumerate(compare_tags[:3], 1):
        print(f"  {i}. {tag.get_text(strip=True)[:60]}")
        print(f"     Classes: {' '.join(tag.get('class', []))}")
        print()
    
    # Check if sale-price is a tag name
    sale_tags = soup.find_all('sale-price')
    print(f"Found {len(sale_tags)} <sale-price> tags")
    for i, tag in enumerate(sale_tags[:3], 1):
        print(f"  {i}. {tag.get_text(strip=True)[:60]}")
        print(f"     Classes: {' '.join(tag.get('class', []))}")
        print()
    
    # Check for elements with compare-at-price class
    compare_class = soup.find_all(class_=re.compile(r'compare-at-price', re.I))
    print(f"Found {len(compare_class)} elements with compare-at-price class")
    
    # Check for elements with sale-price class
    sale_class = soup.find_all(class_=re.compile(r'sale-price', re.I))
    print(f"Found {len(sale_class)} elements with sale-price class")
    
    # If we found compare-at-price tags, check their children
    if compare_tags:
        for tag in compare_tags[:2]:
            children = tag.find_all(['span', 'div', 'p'])
            print(f"\nChildren of <compare-at-price>:")
            for child in children[:3]:
                text = child.get_text(strip=True)
                if re.search(r'\$\d+', text):
                    print(f"  Price: {text}")
                    print(f"    Classes: {' '.join(child.get('class', []))}")
                    print(f"    Has line-through: {'line-through' in ' '.join(child.get('class', [])).lower()}")

if __name__ == "__main__":
    test_url = "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge"
    check_tags(test_url)

