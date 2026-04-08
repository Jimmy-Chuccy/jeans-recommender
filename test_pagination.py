#!/usr/bin/env python3
"""
Test script to check pagination on Tate+Yoko website
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.tate_yoko_scraper import TateYokoScraper
import logging

def test_pagination():
    """Test pagination specifically"""
    logging.basicConfig(level=logging.INFO)
    
    scraper = TateYokoScraper()
    
    # Test first few pages manually
    base_url = "https://tateandyoko.com/collections/jeans"
    
    for page in range(1, 6):  # Test first 5 pages
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?page={page}"
            
        print(f"\n=== Testing Page {page}: {url} ===")
        soup = scraper.get_page(url)
        
        if not soup:
            print(f"Failed to load page {page}")
            break
            
        # Find product links
        product_links = soup.find_all('a', href=re.compile(r'/products/'))
        print(f"Found {len(product_links)} product links on page {page}")
        
        # Check for pagination elements
        next_page_link = soup.find('a', string=re.compile(r'Next'))
        page_info = soup.find(string=re.compile(r'Page \d+ of \d+'))
        
        print(f"Next page link found: {next_page_link is not None}")
        if page_info:
            print(f"Page info: {page_info.strip()}")
        
        # Look for other pagination indicators
        pagination_divs = soup.find_all('div', class_=re.compile(r'pagination'))
        print(f"Pagination divs found: {len(pagination_divs)}")
        
        if not product_links:
            print(f"No products found on page {page}, stopping")
            break

if __name__ == "__main__":
    test_pagination()
