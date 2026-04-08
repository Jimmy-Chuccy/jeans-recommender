#!/usr/bin/env python3
"""
Explore Nudie Jeans website structure to understand how to scrape it
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import re
import json

class NudieJeansExplorer(BaseScraper):
    def __init__(self):
        super().__init__("Nudie Jeans", "https://www.nudiejeans.com")
    
    def explore_homepage(self):
        """Explore the homepage structure"""
        print("\n" + "="*80)
        print("EXPLORING NUDIE JEANS HOMEPAGE")
        print("="*80)
        
        url = "https://www.nudiejeans.com/en-CA"
        print(f"\nFetching: {url}")
        soup = self.get_page(url, use_selenium=True)
        
        if not soup:
            print("Failed to load page")
            return
        
        # Check what platform it's using
        print("\n=== PLATFORM DETECTION ===")
        scripts = soup.find_all('script', src=True)
        shopify_indicators = [s for s in scripts if 'shopify' in s.get('src', '').lower()]
        if shopify_indicators:
            print("✓ Detected: Shopify platform")
        else:
            print("? Platform: Unknown (may need further investigation)")
        
        # Look for navigation/menu structure
        print("\n=== NAVIGATION STRUCTURE ===")
        nav_links = soup.find_all('a', href=True)
        
        # Find collection/category links
        collection_patterns = [
            r'/collections/',
            r'/category/',
            r'/shop/',
            r'/products/',
            r'/men',
            r'/women',
            r'/jeans'
        ]
        
        collection_links = {}
        for link in nav_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            for pattern in collection_patterns:
                if re.search(pattern, href, re.I):
                    if pattern not in collection_links:
                        collection_links[pattern] = []
                    collection_links[pattern].append({
                        'text': text,
                        'href': href
                    })
                    break
        
        for pattern, links in collection_links.items():
            print(f"\n{pattern} links ({len(links)} found):")
            for link in links[:10]:  # Show first 10
                print(f"  - {link['text']}: {link['href']}")
        
        # Look for product links on homepage
        print("\n=== PRODUCT LINKS ON HOMEPAGE ===")
        product_links = soup.find_all('a', href=re.compile(r'/products/'))
        print(f"Found {len(product_links)} product links")
        if product_links:
            unique_products = set()
            for link in product_links[:10]:
                href = link.get('href', '')
                if href:
                    # Normalize URL
                    if href.startswith('/'):
                        full_url = f"https://www.nudiejeans.com{href}"
                    else:
                        full_url = href
                    unique_products.add(full_url)
            print("Sample product URLs:")
            for url in list(unique_products)[:5]:
                print(f"  - {url}")
        
        # Check for data attributes or JSON data
        print("\n=== DATA STRUCTURE ===")
        json_scripts = soup.find_all('script', type='application/json')
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        print(f"JSON-LD scripts: {len(json_ld_scripts)}")
        print(f"JSON scripts: {len(json_scripts)}")
        
        if json_ld_scripts:
            print("\nSample JSON-LD data:")
            try:
                data = json.loads(json_ld_scripts[0].string)
                print(json.dumps(data, indent=2)[:500])
            except:
                pass
        
        # Look for common e-commerce patterns
        print("\n=== E-COMMERCE PATTERNS ===")
        product_containers = soup.find_all(['div', 'article', 'section'], 
                                          class_=re.compile(r'product|item|card', re.I))
        print(f"Product containers found: {len(product_containers)}")
        
        # Check for pagination patterns
        pagination = soup.find_all(['a', 'button'], 
                                 class_=re.compile(r'pagination|page|next|prev', re.I))
        print(f"Pagination elements: {len(pagination)}")
    
    def explore_collection_page(self, collection_url):
        """Explore a collection page structure"""
        print("\n" + "="*80)
        print(f"EXPLORING COLLECTION PAGE: {collection_url}")
        print("="*80)
        
        soup = self.get_page(collection_url, use_selenium=True)
        if not soup:
            print("Failed to load page")
            return
        
        # Find product links
        product_links = soup.find_all('a', href=re.compile(r'/products/'))
        print(f"\nProduct links found: {len(product_links)}")
        
        # Extract unique product URLs
        unique_products = set()
        for link in product_links:
            href = link.get('href', '')
            if href:
                if href.startswith('/'):
                    full_url = f"https://www.nudiejeans.com{href}"
                else:
                    full_url = href
                # Remove query params and fragments
                full_url = full_url.split('?')[0].split('#')[0]
                unique_products.add(full_url)
        
        print(f"Unique product URLs: {len(unique_products)}")
        print("\nSample product URLs:")
        for url in list(unique_products)[:10]:
            print(f"  - {url}")
        
        # Check pagination
        print("\n=== PAGINATION ===")
        pagination_links = soup.find_all('a', href=re.compile(r'page=|p=\d+', re.I))
        if pagination_links:
            print(f"Pagination links found: {len(pagination_links)}")
            for link in pagination_links[:5]:
                print(f"  - {link.get('href')}")
        else:
            # Check for "load more" or infinite scroll
            load_more = soup.find_all(['button', 'a'], 
                                     string=re.compile(r'load more|show more|next', re.I))
            if load_more:
                print("Found 'Load More' button (infinite scroll pattern)")
            else:
                print("No pagination found - may be single page or infinite scroll")
        
        # Check for product grid structure
        print("\n=== PRODUCT GRID STRUCTURE ===")
        grid_containers = soup.find_all(['div', 'ul', 'section'], 
                                       class_=re.compile(r'grid|products|collection', re.I))
        print(f"Grid containers: {len(grid_containers)}")
        if grid_containers:
            print("Sample classes:")
            for container in grid_containers[:3]:
                classes = container.get('class', [])
                if classes:
                    print(f"  - {classes}")
    
    def explore_product_page(self, product_url):
        """Explore a product page structure"""
        print("\n" + "="*80)
        print(f"EXPLORING PRODUCT PAGE: {product_url}")
        print("="*80)
        
        soup = self.get_page(product_url, use_selenium=True)
        if not soup:
            print("Failed to load page")
            return
        
        # Extract product name
        print("\n=== PRODUCT NAME ===")
        name_selectors = [
            ('h1', {}),
            ('h1', {'class': re.compile(r'product|title', re.I)}),
            ('meta', {'property': 'og:title'}),
            ('title', {})
        ]
        
        for tag, attrs in name_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                if tag == 'meta':
                    name = elem.get('content', '')
                else:
                    name = elem.get_text(strip=True)
                if name:
                    print(f"Found via {tag}: {name[:100]}")
                    break
        
        # Extract price
        print("\n=== PRICE STRUCTURE ===")
        price_patterns = [
            r'\$\d+',
            r'\d+\s*CAD',
            r'\d+\s*USD',
            r'price',
            r'cost'
        ]
        
        price_elements = soup.find_all(string=re.compile('|'.join(price_patterns), re.I))
        if price_elements:
            print(f"Price-related text found: {len(price_elements)}")
            for elem in price_elements[:5]:
                text = str(elem).strip()[:100]
                if text:
                    print(f"  - {text}")
        
        # Check for structured data
        print("\n=== STRUCTURED DATA ===")
        json_ld = soup.find_all('script', type='application/ld+json')
        if json_ld:
            print(f"JSON-LD scripts: {len(json_ld)}")
            try:
                for script in json_ld[:2]:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        print(f"  Type: {data.get('@type', 'Unknown')}")
                        if 'name' in data:
                            print(f"  Name: {data.get('name', '')[:100]}")
                        if 'offers' in data:
                            offers = data.get('offers', {})
                            if isinstance(offers, dict):
                                print(f"  Price: {offers.get('price', 'N/A')}")
                    elif isinstance(data, list):
                        print(f"  Found list with {len(data)} items")
            except Exception as e:
                print(f"  Error parsing JSON-LD: {e}")
        
        # Check for product details/specifications
        print("\n=== PRODUCT DETAILS ===")
        detail_containers = soup.find_all(['div', 'dl', 'ul'], 
                                         class_=re.compile(r'detail|spec|info|description', re.I))
        print(f"Detail containers: {len(detail_containers)}")
        
        # Look for fit information
        print("\n=== FIT INFORMATION ===")
        fit_keywords = ['fit', 'cut', 'rise', 'leg', 'waist', 'inseam']
        fit_elements = soup.find_all(string=re.compile('|'.join(fit_keywords), re.I))
        if fit_elements:
            print(f"Fit-related text found: {len(fit_elements)}")
            for elem in fit_elements[:5]:
                text = str(elem).strip()[:100]
                if text and len(text) > 10:
                    print(f"  - {text}")
        
        # Check for wash/fabric information
        print("\n=== FABRIC/WASH INFORMATION ===")
        fabric_keywords = ['wash', 'fabric', 'denim', 'oz', 'selvedge', 'selvage', 'cotton']
        fabric_elements = soup.find_all(string=re.compile('|'.join(fabric_keywords), re.I))
        if fabric_elements:
            print(f"Fabric-related text found: {len(fabric_elements)}")
            for elem in fabric_elements[:5]:
                text = str(elem).strip()[:100]
                if text and len(text) > 10:
                    print(f"  - {text}")

def main():
    explorer = NudieJeansExplorer()
    
    # Explore homepage
    explorer.explore_homepage()
    
    # Try to explore a collection page (men's jeans)
    print("\n\n" + "="*80)
    print("ATTEMPTING TO EXPLORE COLLECTION PAGES")
    print("="*80)
    
    # Common collection URL patterns to try
    collection_urls_to_try = [
        "https://www.nudiejeans.com/en-CA/collections/men-jeans",
        "https://www.nudiejeans.com/en-CA/collections/mens-jeans",
        "https://www.nudiejeans.com/en-CA/collections/jeans-men",
        "https://www.nudiejeans.com/en-CA/men/jeans",
        "https://www.nudiejeans.com/en-CA/products",  # If they have a products listing
    ]
    
    for url in collection_urls_to_try:
        print(f"\nTrying: {url}")
        soup = explorer.get_page(url, use_selenium=True)
        if soup:
            # Check if page loaded successfully (not 404)
            title = soup.find('title')
            if title and '404' not in title.get_text().lower():
                product_links = soup.find_all('a', href=re.compile(r'/products/'))
                if product_links:
                    print(f"✓ Found {len(product_links)} product links!")
                    explorer.explore_collection_page(url)
                    # Try to explore one product page
                    if product_links:
                        first_product = product_links[0].get('href', '')
                        if first_product:
                            if first_product.startswith('/'):
                                full_url = f"https://www.nudiejeans.com{first_product}"
                            else:
                                full_url = first_product
                            full_url = full_url.split('?')[0].split('#')[0]
                            print(f"\nExploring first product: {full_url}")
                            explorer.explore_product_page(full_url)
                    break
            else:
                print("  ✗ Page not found or error")
        else:
            print("  ✗ Failed to load")
    
    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

