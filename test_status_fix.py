#!/usr/bin/env python3
"""
Test script to verify status extraction fix on a small sample of products
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import csv

def test_status_extraction():
    """Test status extraction on a sample of products"""
    scraper = NakedFamousNewScraper()
    
    # Sample product URLs from the latest scraped data
    # These were all marked as "on-sales" in the old data - let's verify which are actually on sale
    test_urls = [
        "https://nakedandfamousdenim.com/products/true-guy-sea-island-selvedge-indigo",
        "https://nakedandfamousdenim.com/products/true-guy-max-brush-selvedge-indigo",
        "https://nakedandfamousdenim.com/products/weird-guy-forbidden-fruit-selvedge",
        "https://nakedandfamousdenim.com/products/easy-guy-indigo-sashiko",
        "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge",  # This one from the image should be on sale
        "https://nakedandfamousdenim.com/products/naked-famous-denim-chore-coat-black-canvas",
        "https://nakedandfamousdenim.com/products/crewneck-black-terry",
        "https://nakedandfamousdenim.com/products/easy-guy-max-brush-selvedge-indigo",
    ]
    
    print("="*80)
    print("Testing Status Extraction on Sample Products")
    print("="*80)
    print()
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"[{i}/{len(test_urls)}] Testing: {url}")
        print("-" * 80)
        
        # Set up collection tracking for this test
        scraper._product_collections[url] = ['test']
        
        try:
            product = scraper.scrape_product(url)
            if product:
                status = product.get('status', 'unknown')
                name = product.get('product_name', 'N/A')
                print(f"  Product: {name[:60]}...")
                print(f"  Status: {status}")
                print()
                
                results.append({
                    'url': url,
                    'product_name': name,
                    'status': status
                })
            else:
                print(f"  ERROR: Failed to scrape product")
                print()
                results.append({
                    'url': url,
                    'product_name': 'FAILED',
                    'status': 'ERROR'
                })
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            print()
            results.append({
                'url': url,
                'product_name': 'ERROR',
                'status': f'EXCEPTION: {str(e)}'
            })
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tested: {len(results)}")
    
    status_counts = {}
    for r in results:
        status = r['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nStatus distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    print("\nDetailed results:")
    for r in results:
        print(f"  {r['status']:12} - {r['product_name'][:50]}")
    
    # Check if we have a mix of statuses (good sign)
    unique_statuses = set(r['status'] for r in results if not r['status'].startswith('ERROR'))
    if len(unique_statuses) > 1:
        print("\n✓ Good: Found multiple status types (fix appears to be working)")
    elif len(unique_statuses) == 1 and 'regular' in unique_statuses:
        print("\n✓ All products are 'regular' (this is expected if none are on sale)")
    elif len(unique_statuses) == 1 and 'on-sales' in unique_statuses:
        print("\n⚠ Warning: All products marked as 'on-sales' (may need further investigation)")
    
    return results

if __name__ == "__main__":
    test_status_extraction()

