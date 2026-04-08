#!/usr/bin/env python3
"""
Test script to verify all scraper fixes on a sample of ~50 products
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import csv
from datetime import datetime

def test_scraper_fixes():
    """Test scraper fixes on a sample of products"""
    scraper = NakedFamousNewScraper()
    
    print("="*80)
    print("TESTING SCRAPER FIXES - Sample of ~50 Products")
    print("="*80)
    print()
    
    # Get a diverse sample of product URLs
    sample_urls = []
    
    try:
        # Try to load from latest data to get real product URLs
        with open('data/processed/naked_famous_products_latest.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            total = len(rows)
            print(f"Found {total} products in latest data")
            
            # Sample strategy: Get diverse mix
            # - First 10 products
            # - Every Nth product from middle section (to get variety)
            # - Last 10 products
            # - Total target: ~50 products
            
            sample_indices = []
            
            # First 10
            sample_indices.extend(range(0, min(10, total)))
            
            # Middle section - sample every ~(total/40) products
            if total > 20:
                step = max(1, total // 40)
                mid_start = total // 4
                mid_end = 3 * total // 4
                sample_indices.extend(range(mid_start, mid_end, step))
            
            # Last 10
            if total > 10:
                sample_indices.extend(range(max(0, total - 10), total))
            
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
            "https://nakedandfamousdenim.com/products/easy-guy-solid-black-selvedge",
            "https://nakedandfamousdenim.com/products/naked-famous-denim-chore-coat-black-canvas",
            "https://nakedandfamousdenim.com/products/weird-guy-forbidden-fruit-selvedge",
        ]
    
    # Limit to ~50 products
    if len(sample_urls) > 50:
        sample_urls = sample_urls[:50]
        print(f"Limited to 50 products for testing")
    
    print(f"\nWill test {len(sample_urls)} products")
    print("This may take 30-60 minutes depending on page load times...")
    print()
    
    results = []
    errors = []
    validation_stats = {
        'has_sku': 0,
        'has_collections': 0,
        'has_made_in': 0,
        'has_denim_cat': 0,
        'has_material': 0,
        'has_denim_weight': 0,
        'has_regular_price': 0,
        'has_sales_price': 0,
        'jeans_count': 0,
        'non_jeans_count': 0,
        'on_sales_count': 0,
        'regular_count': 0,
    }
    
    for i, url in enumerate(sample_urls, 1):
        print(f"[{i}/{len(sample_urls)}] Scraping: {url}")
        
        # Note: Collections will be empty in test mode since we're not going through
        # the full collection scraping process. In real scraping, collections are
        # populated by get_product_urls_from_collection() which tracks which collection
        # each product URL was found in. For testing, we leave it empty to show
        # the actual behavior - collections will be populated during full scrape.
        
        try:
            product = scraper.scrape_product(url)
            if product:
                name = product.get('product_name', 'N/A')
                status = product.get('status', 'unknown')
                
                # Validation counts
                if product.get('sku'):
                    validation_stats['has_sku'] += 1
                if product.get('collections'):
                    validation_stats['has_collections'] += 1
                if product.get('made_in'):
                    validation_stats['has_made_in'] += 1
                if product.get('denim_cat'):
                    validation_stats['has_denim_cat'] += 1
                if product.get('material'):
                    validation_stats['has_material'] += 1
                if product.get('denim_weight_oz'):
                    validation_stats['has_denim_weight'] += 1
                if product.get('regular_price'):
                    validation_stats['has_regular_price'] += 1
                if product.get('sales_price'):
                    validation_stats['has_sales_price'] += 1
                
                if product.get('is_jeans') == 'yes':
                    validation_stats['jeans_count'] += 1
                else:
                    validation_stats['non_jeans_count'] += 1
                
                if status == 'on-sales':
                    validation_stats['on_sales_count'] += 1
                else:
                    validation_stats['regular_count'] += 1
                
                print(f"  ✓ {name[:55]}... | Status: {status}")
                if product.get('regular_price'):
                    print(f"    Regular: ${product.get('regular_price')}, Sale: ${product.get('sales_price') or 'N/A'}")
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
        output_file = 'data/test_scraper_fixes_results.csv'
        os.makedirs('data', exist_ok=True)
        
        # Define column order matching the scraper
        required_columns = [
            'product_id', 'sku',
            'product_name', 'fit_id', 'fabric_id', 'wash_state',
            'gender', 'default_inseam_label', 'colorway', 
            'status', 'regular_price', 'sales_price',
            'nf_product_url', 'description_html',
            'release_season', 'run_code', 'notes',
            'denim_weight_oz', 'denim_cat', 'material', 'made_in',
            'product_description',
            'collections',
            'is_jeans',
            'scraped_at'
        ]
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=required_columns, extrasaction='ignore')
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        
        print("="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"Total products tested: {len(sample_urls)}")
        print(f"Successfully scraped: {len(results)}")
        print(f"Errors: {len(errors)}")
        print()
        
        print("Field Extraction Success Rates:")
        print(f"  SKU: {validation_stats['has_sku']}/{len(results)} ({100*validation_stats['has_sku']/max(1,len(results)):.1f}%)")
        print(f"  Collections: {validation_stats['has_collections']}/{len(results)} ({100*validation_stats['has_collections']/max(1,len(results)):.1f}%)")
        print(f"  Made In: {validation_stats['has_made_in']}/{len(results)} ({100*validation_stats['has_made_in']/max(1,len(results)):.1f}%)")
        print(f"  Denim Category: {validation_stats['has_denim_cat']}/{len(results)} ({100*validation_stats['has_denim_cat']/max(1,len(results)):.1f}%)")
        print(f"  Material: {validation_stats['has_material']}/{len(results)} ({100*validation_stats['has_material']/max(1,len(results)):.1f}%)")
        print(f"  Denim Weight: {validation_stats['has_denim_weight']}/{len(results)} ({100*validation_stats['has_denim_weight']/max(1,len(results)):.1f}%)")
        print(f"  Regular Price: {validation_stats['has_regular_price']}/{len(results)} ({100*validation_stats['has_regular_price']/max(1,len(results)):.1f}%)")
        print(f"  Sales Price: {validation_stats['has_sales_price']}/{len(results)} ({100*validation_stats['has_sales_price']/max(1,len(results)):.1f}%)")
        print()
        
        print("Product Distribution:")
        print(f"  Jeans products: {validation_stats['jeans_count']}")
        print(f"  Non-jeans products: {validation_stats['non_jeans_count']}")
        print(f"  On-sales: {validation_stats['on_sales_count']}")
        print(f"  Regular price: {validation_stats['regular_count']}")
        print()
        
        # Sample of results for quick inspection
        print("Sample Results (first 5 products):")
        for i, r in enumerate(results[:5], 1):
            print(f"\n  {i}. {r.get('product_name', 'N/A')[:50]}")
            print(f"     SKU: {r.get('sku', 'N/A')}")
            print(f"     Status: {r.get('status', 'N/A')}")
            print(f"     Regular Price: ${r.get('regular_price', 'N/A')}")
            print(f"     Sales Price: ${r.get('sales_price', 'N/A') if r.get('sales_price') else 'N/A'}")
            print(f"     Made In: {r.get('made_in', 'N/A')}")
            print(f"     Denim Cat: {r.get('denim_cat', 'N/A')[:50]}")
            print(f"     Material: {r.get('material', 'N/A')[:50]}")
            print(f"     Collections: {r.get('collections', 'N/A')}")
        
        print()
        print(f"✓ Results saved to: {output_file}")
        print(f"  You can now manually inspect this file to verify all fixes")
        print()
        print("Key things to check:")
        print("  1. SKU is populated and next to product_id")
        print("  2. Collections show actual collection names (not 'test')")
        print("  3. Made In shows 'Made in Canada' or 'Made in Japan' (simple format)")
        print("  4. Denim Cat shows full text like '12.5oz Japanese Selvedge Denim'")
        print("  5. Material shows composition like '99.6% Cotton / 0.4% Gold'")
        print("  6. Denim Weight shows numeric value only (e.g., '12.5')")
        print("  7. Regular Price and Sales Price are populated correctly")
        print("  8. ty_product_url field is removed")
        print("  9. Field order matches the new schema")
        
        if errors:
            print(f"\nErrors encountered ({len(errors)}):")
            for err in errors[:5]:
                print(f"  - {err['url'][:60]}... : {err['error']}")
    else:
        print("No results to save!")
    
    return results

if __name__ == "__main__":
    test_scraper_fixes()

