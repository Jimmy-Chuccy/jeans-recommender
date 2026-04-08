#!/usr/bin/env python3
"""
Test scraper on a sample of products and save results to CSV for manual inspection
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import csv
from datetime import datetime

def test_sample_scrape():
    """Test scraper on a sample of products"""
    scraper = NakedFamousNewScraper()
    
    # Get a sample of product URLs from the latest data
    print("Loading sample product URLs from latest data...")
    sample_urls = []
    
    try:
        with open('data/processed/naked_famous_products_latest.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Get a diverse sample - mix of different products
            # Take first 10, middle 10, and last 10 for variety
            total = len(rows)
            sample_indices = list(range(0, min(10, total)))  # First 10
            if total > 20:
                mid_start = total // 2 - 5
                sample_indices.extend(range(mid_start, mid_start + 10))  # Middle 10
            if total > 10:
                sample_indices.extend(range(max(0, total - 10), total))  # Last 10
            
            # Remove duplicates and get unique URLs
            seen = set()
            for idx in sample_indices:
                if idx < len(rows):
                    url = rows[idx].get('nf_product_url', '')
                    if url and url not in seen:
                        seen.add(url)
                        sample_urls.append(url)
            
            print(f"Selected {len(sample_urls)} unique product URLs for testing")
    except FileNotFoundError:
        print("Latest data file not found. Using hardcoded sample URLs...")
        # Fallback to some known URLs
        sample_urls = [
            "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge",
            "https://nakedandfamousdenim.com/products/true-guy-sea-island-selvedge-indigo",
            "https://nakedandfamousdenim.com/products/true-guy-max-brush-selvedge-indigo",
            "https://nakedandfamousdenim.com/products/weird-guy-forbidden-fruit-selvedge",
            "https://nakedandfamousdenim.com/products/easy-guy-indigo-sashiko",
        ]
    
    print(f"\n{'='*80}")
    print(f"Testing Scraper on {len(sample_urls)} Sample Products")
    print(f"{'='*80}\n")
    
    results = []
    errors = []
    
    for i, url in enumerate(sample_urls, 1):
        print(f"[{i}/{len(sample_urls)}] Scraping: {url}")
        
        # Set up collection tracking for this test
        scraper._product_collections[url] = ['test_sample']
        
        try:
            product = scraper.scrape_product(url)
            if product:
                status = product.get('status', 'unknown')
                name = product.get('product_name', 'N/A')
                print(f"  ✓ {name[:60]}... | Status: {status}")
                results.append(product)
            else:
                print(f"  ✗ Failed to scrape product")
                errors.append({'url': url, 'error': 'Failed to scrape'})
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            errors.append({'url': url, 'error': str(e)})
        print()
    
    # Save results to CSV
    if results:
        output_file = 'data/test_sample_results.csv'
        os.makedirs('data', exist_ok=True)
        
        # Get all unique keys from results
        all_keys = set()
        for r in results:
            all_keys.update(r.keys())
        
        # Define column order (matching the main scraper)
        required_columns = [
            'product_id', 'product_name', 'fit_id', 'fabric_id', 'wash_state',
            'gender', 'default_inseam_label', 'colorway', 'status',
            'nf_product_url', 'ty_product_url', 'description_html',
            'release_season', 'run_code', 'notes',
            'sku', 'denim_weight_oz', 'denim_cat', 'made_in', 'product_description',
            'collections'
        ]
        
        # Add any extra keys that aren't in required_columns
        extra_keys = sorted(all_keys - set(required_columns))
        fieldnames = required_columns + extra_keys
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total tested: {len(sample_urls)}")
        print(f"Successfully scraped: {len(results)}")
        print(f"Errors: {len(errors)}")
        
        # Status distribution
        status_counts = {}
        for r in results:
            status = r.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\nStatus distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        # Products with vs without fit_id (jeans vs non-jeans)
        jeans_count = sum(1 for r in results if r.get('fit_id'))
        non_jeans_count = len(results) - jeans_count
        print(f"\nProduct types:")
        print(f"  Jeans products: {jeans_count}")
        print(f"  Non-jeans products: {non_jeans_count}")
        
        print(f"\n✓ Results saved to: {output_file}")
        print(f"  You can now manually inspect this file to verify data integrity")
        
        if errors:
            print(f"\nErrors encountered:")
            for err in errors[:5]:  # Show first 5 errors
                print(f"  - {err['url'][:60]}... : {err['error']}")
    else:
        print("No results to save!")
    
    return results

if __name__ == "__main__":
    test_sample_scrape()

