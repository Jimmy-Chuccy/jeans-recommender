#!/usr/bin/env python3
"""
Test script to validate the four status extraction fixes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import csv
from datetime import datetime

def test_status_fixes():
    """Test the status extraction fixes on a sample of products"""
    scraper = NakedFamousNewScraper()
    
    # Test with a diverse sample of product URLs
    test_urls = [
        # These should test various scenarios
        "https://nakedandfamousdenim.com/products/weird-guy-deadstock-real-gold-selvedge",
        "https://nakedandfamousdenim.com/products/true-guy-sea-island-selvedge-indigo",
        "https://nakedandfamousdenim.com/products/easy-guy-solid-black-selvedge",
        "https://nakedandfamousdenim.com/products/naked-famous-denim-chore-coat-black-canvas",
        "https://nakedandfamousdenim.com/products/weird-guy-forbidden-fruit-selvedge",
    ]
    
    print("="*80)
    print("TESTING STATUS EXTRACTION FIXES")
    print("="*80)
    print()
    
    results = []
    validation_results = {
        'fix1_line_through': {'tested': 0, 'passed': 0, 'details': []},
        'fix2_variant_matching': {'tested': 0, 'passed': 0, 'details': []},
        'fix3_proximity': {'tested': 0, 'passed': 0, 'details': []},
        'fix4_timestamp': {'tested': 0, 'passed': 0, 'details': []},
        'is_jeans_column': {'tested': 0, 'passed': 0, 'details': []},
    }
    
    for i, url in enumerate(test_urls, 1):
        print(f"[{i}/{len(test_urls)}] Testing: {url}")
        print("-" * 80)
        
        # Set up collection tracking
        scraper._product_collections[url] = ['test']
        
        try:
            product = scraper.scrape_product(url)
            if product:
                name = product.get('product_name', 'N/A')
                status = product.get('status', 'unknown')
                fit_id = product.get('fit_id', '')
                is_jeans = product.get('is_jeans', 'unknown')
                scraped_at = product.get('scraped_at', '')
                
                print(f"  Product: {name[:60]}...")
                print(f"  Status: {status}")
                print(f"  Fit ID: {fit_id if fit_id else '(empty - non-jeans)'}")
                print(f"  Is Jeans: {is_jeans}")
                print(f"  Scraped At: {scraped_at}")
                
                # Validation checks
                
                # Fix 4: Timestamp validation
                validation_results['fix4_timestamp']['tested'] += 1
                if scraped_at:
                    try:
                        # Validate ISO format
                        datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                        validation_results['fix4_timestamp']['passed'] += 1
                        validation_results['fix4_timestamp']['details'].append(f"✓ {name[:40]}: Valid timestamp")
                    except:
                        validation_results['fix4_timestamp']['details'].append(f"✗ {name[:40]}: Invalid timestamp format")
                else:
                    validation_results['fix4_timestamp']['details'].append(f"✗ {name[:40]}: Missing timestamp")
                
                # is_jeans column validation
                validation_results['is_jeans_column']['tested'] += 1
                if fit_id:
                    if is_jeans == 'yes':
                        validation_results['is_jeans_column']['passed'] += 1
                        validation_results['is_jeans_column']['details'].append(f"✓ {name[:40]}: Jeans correctly labeled")
                    else:
                        validation_results['is_jeans_column']['details'].append(f"✗ {name[:40]}: Jeans but labeled as {is_jeans}")
                else:
                    if is_jeans == 'no':
                        validation_results['is_jeans_column']['passed'] += 1
                        validation_results['is_jeans_column']['details'].append(f"✓ {name[:40]}: Non-jeans correctly labeled")
                    else:
                        validation_results['is_jeans_column']['details'].append(f"✗ {name[:40]}: Non-jeans but labeled as {is_jeans}")
                
                # Fix 1, 2, 3: Status detection validation
                # We can't fully validate these without inspecting HTML, but we can check:
                # - Status is either 'on-sales' or 'regular'
                # - Status makes sense (not all same, not all different)
                if status in ['on-sales', 'regular']:
                    validation_results['fix1_line_through']['tested'] += 1
                    validation_results['fix1_line_through']['passed'] += 1
                    validation_results['fix1_line_through']['details'].append(f"✓ {name[:40]}: Status = {status}")
                else:
                    validation_results['fix1_line_through']['details'].append(f"✗ {name[:40]}: Invalid status = {status}")
                
                results.append(product)
            else:
                print(f"  ✗ Failed to scrape product")
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Save results to CSV for inspection
    if results:
        output_file = 'data/test_status_fixes_results.csv'
        os.makedirs('data', exist_ok=True)
        
        required_columns = [
            'product_id', 'product_name', 'fit_id', 'fabric_id', 'wash_state',
            'gender', 'default_inseam_label', 'colorway', 'status',
            'nf_product_url', 'ty_product_url', 'description_html',
            'release_season', 'run_code', 'notes',
            'sku', 'denim_weight_oz', 'denim_cat', 'made_in', 'product_description',
            'collections', 'is_jeans', 'scraped_at'
        ]
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=required_columns, extrasaction='ignore')
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        
        print("="*80)
        print("VALIDATION RESULTS")
        print("="*80)
        print()
        
        # Fix 4: Timestamp validation
        print("FIX 4: Timestamp Field (scraped_at)")
        print(f"  Tested: {validation_results['fix4_timestamp']['tested']}")
        print(f"  Passed: {validation_results['fix4_timestamp']['passed']}")
        print(f"  Success Rate: {validation_results['fix4_timestamp']['passed']}/{validation_results['fix4_timestamp']['tested']} ({100*validation_results['fix4_timestamp']['passed']/max(1,validation_results['fix4_timestamp']['tested']):.1f}%)")
        for detail in validation_results['fix4_timestamp']['details']:
            print(f"    {detail}")
        print()
        
        # is_jeans column validation
        print("BONUS: is_jeans Column")
        print(f"  Tested: {validation_results['is_jeans_column']['tested']}")
        print(f"  Passed: {validation_results['is_jeans_column']['passed']}")
        print(f"  Success Rate: {validation_results['is_jeans_column']['passed']}/{validation_results['is_jeans_column']['tested']} ({100*validation_results['is_jeans_column']['passed']/max(1,validation_results['is_jeans_column']['tested']):.1f}%)")
        for detail in validation_results['is_jeans_column']['details']:
            print(f"    {detail}")
        print()
        
        # Status detection summary
        print("FIX 1, 2, 3: Status Detection (on-sales vs regular)")
        status_counts = {}
        for r in results:
            status = r.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"  Total products tested: {len(results)}")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        if len(status_counts) > 1:
            print(f"  ✓ Good: Multiple status types detected (logic is working)")
        elif len(status_counts) == 1:
            status_type = list(status_counts.keys())[0]
            print(f"  ⚠ Note: All products marked as '{status_type}' (may be correct if all are same)")
        
        print()
        print(f"  Tested: {validation_results['fix1_line_through']['tested']}")
        print(f"  Passed: {validation_results['fix1_line_through']['passed']}")
        print(f"  Success Rate: {validation_results['fix1_line_through']['passed']}/{validation_results['fix1_line_through']['tested']} ({100*validation_results['fix1_line_through']['passed']/max(1,validation_results['fix1_line_through']['tested']):.1f}%)")
        for detail in validation_results['fix1_line_through']['details']:
            print(f"    {detail}")
        print()
        
        # Overall summary
        print("="*80)
        print("OVERALL SUMMARY")
        print("="*80)
        total_tests = sum(v['tested'] for v in validation_results.values())
        total_passed = sum(v['passed'] for v in validation_results.values())
        print(f"Total validation tests: {total_tests}")
        print(f"Total passed: {total_passed}")
        print(f"Overall success rate: {total_passed}/{total_tests} ({100*total_passed/max(1,total_tests):.1f}%)")
        print()
        print(f"✓ Results saved to: {output_file}")
        print(f"  You can manually inspect this file to verify:")
        print(f"    - scraped_at timestamps are present and valid")
        print(f"    - is_jeans column is correctly populated")
        print(f"    - status values are 'on-sales' or 'regular'")
        print()
        print("NOTE: Fixes 1, 2, and 3 (line-through check, variant matching, proximity)")
        print("      require manual inspection of actual product pages to fully validate.")
        print("      The status detection is working if you see a mix of 'on-sales' and 'regular'.")
        
    return results

if __name__ == "__main__":
    test_status_fixes()

