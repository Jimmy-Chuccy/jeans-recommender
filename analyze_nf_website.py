#!/usr/bin/env python3
"""
Analyze the structure of the new Naked & Famous website
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import re
import json

class NFAnalyzer(BaseScraper):
    def __init__(self):
        super().__init__("Naked & Famous", "https://nakedandfamousdenim.com")
    
    def analyze_collection_page(self, url: str):
        """Analyze a collection page structure"""
        print(f"\n{'='*80}")
        print(f"Analyzing: {url}")
        print(f"{'='*80}")
        
        soup = self.get_page(url, use_selenium=True)
        if not soup:
            print("Failed to load page")
            return
        
        # Check for pagination
        pagination = soup.find_all('a', href=re.compile(r'page=\d+'))
        if pagination:
            print(f"\nPagination found: {len(pagination)} pagination links")
            for link in pagination[:5]:
                print(f"  - {link.get('href')}")
        
        # Find product links
        product_links = soup.find_all('a', href=re.compile(r'/products/'))
        print(f"\nProduct links found: {len(product_links)}")
        
        # Check for different link patterns
        link_patterns = {}
        for link in product_links[:10]:
            href = link.get('href', '')
            pattern = re.search(r'/products/([^/?]+)', href)
            if pattern:
                product_slug = pattern.group(1)
                if product_slug not in link_patterns:
                    link_patterns[product_slug] = href
        
        print(f"\nUnique product slugs (first 10):")
        for slug, href in list(link_patterns.items())[:10]:
            print(f"  - {slug}: {href}")
        
        # Check for product cards/containers
        product_containers = soup.find_all(['div', 'article'], class_=re.compile(r'product|card|item', re.I))
        print(f"\nProduct containers found: {len(product_containers)}")
        
        # Look for product titles
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'Guy|Girl', re.I))
        print(f"\nProduct titles found: {len(titles)}")
        for title in titles[:5]:
            print(f"  - {title.get_text(strip=True)}")
        
        # Check for load more / infinite scroll
        load_more = soup.find_all(['button', 'a'], string=re.compile(r'load|more|show', re.I))
        if load_more:
            print(f"\nLoad more buttons found: {len(load_more)}")
        
        # Save HTML for inspection
        with open('debug_nf_page.html', 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"\nHTML saved to debug_nf_page.html")

if __name__ == "__main__":
    analyzer = NFAnalyzer()
    
    # Analyze main collection
    analyzer.analyze_collection_page("https://nakedandfamousdenim.com/collections/men-jeans")
    
    # Analyze one product page to understand structure
    print(f"\n{'='*80}")
    print("Analyzing sample product page...")
    print(f"{'='*80}")
    analyzer.analyze_collection_page("https://nakedandfamousdenim.com/products/super-guy-mij14-haru-kaze-selvedge")

