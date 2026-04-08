#!/usr/bin/env python3
"""
Test script to verify price extraction fixes on problematic products
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper
import csv
from datetime import datetime

def test_price_fixes():
    """Test price extraction fixes on specific problematic products"""
    scraper = NakedFamousNewScraper()
    
    # Test the specific problematic products mentioned by the user
    test_products = [
        {
            'url': 'https://nakedandfamousdenim.com/products/weird-guy-cashmere-stretch-blend-denim',
            'expected_status': 'regular',
            'expected_regular_price': '306.00',
            'expected_sales_price': '',
            'name': 'Weird Guy - Cashmere Stretch Blend Denim'
        },
        {
            'url': 'https://nakedandfamousdenim.com/products/easy-guy-max-brush-selvedge-indigo',
            'expected_status': 'regular',
            'expected_regular_price': None,  # We'll check it's not $345
            'expected_sales_price': '',
            'name': 'Easy Guy - Max Brush Selvedge - Indigo'
        }
    ]
    
    print("="*80)
    print("TESTING PRICE EXTRACTION FIXES")
    print("="*80)
    print()
    
    results = []
    
    for i, test_case in enumerate(test_products, 1):
        url = test_case['url']
        print(f"[{i}/{len(test_products)}] Testing: {test_case['name']}")
        print(f"  URL: {url}")
        print(f"  Expected: status={test_case['expected_status']}, "
              f"regular_price={test_case['expected_regular_price']}, "
              f"sales_price={test_case['expected_sales_price']}")
        
        try:
            # Try with requests first (faster, no Selenium needed for price extraction)
            # The price extraction should work with static HTML
            product = scraper.scrape_product(url)
            if product:
                status = product.get('status', 'unknown')
                regular_price = product.get('regular_price', '')
                sales_price = product.get('sales_price', '')
                product_id = product.get('product_id', '')
                product_name = product.get('product_name', '')
                
                print(f"  Actual:   status={status}, regular_price={regular_price}, sales_price={sales_price}")
                print(f"  Product ID: {product_id}")
                print(f"  Product Name: {product_name}")
                
                # Validate results
                passed = True
                issues = []
                
                if status != test_case['expected_status']:
                    passed = False
                    issues.append(f"Status mismatch: expected '{test_case['expected_status']}', got '{status}'")
                
                if test_case['expected_regular_price']:
                    if regular_price != test_case['expected_regular_price']:
                        passed = False
                        issues.append(f"Regular price mismatch: expected '{test_case['expected_regular_price']}', got '{regular_price}'")
                
                if test_case['expected_regular_price'] == '306.00':
                    # Special check: should NOT be $345
                    if regular_price == '345.00':
                        passed = False
                        issues.append(f"ERROR: Found incorrect regular_price of $345 (should be $306)")
                
                if sales_price != test_case['expected_sales_price']:
                    passed = False
                    issues.append(f"Sales price mismatch: expected '{test_case['expected_sales_price']}', got '{sales_price}'")
                
                # Check product_id doesn't have hash suffix
                if len(product_id.split('_')) > 4:  # fit_fabric_wash should be max 3-4 parts
                    # Check if last part looks like a hash (8 hex chars)
                    last_part = product_id.split('_')[-1]
                    if len(last_part) == 8 and all(c in '0123456789abcdef' for c in last_part.lower()):
                        passed = False
                        issues.append(f"Product ID has hash suffix: {product_id}")
                
                if passed:
                    print(f"  ✅ PASSED")
                else:
                    print(f"  ❌ FAILED")
                    for issue in issues:
                        print(f"    - {issue}")
                
                results.append({
                    'url': url,
                    'name': product_name,
                    'product_id': product_id,
                    'status': status,
                    'regular_price': regular_price,
                    'sales_price': sales_price,
                    'passed': passed,
                    'issues': '; '.join(issues) if issues else ''
                })
            else:
                print(f"  ❌ FAILED: Could not scrape product")
                results.append({
                    'url': url,
                    'name': test_case['name'],
                    'product_id': '',
                    'status': 'ERROR',
                    'regular_price': '',
                    'sales_price': '',
                    'passed': False,
                    'issues': 'Failed to scrape product'
                })
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            results.append({
                'url': url,
                'name': test_case['name'],
                'product_id': '',
                'status': 'ERROR',
                'regular_price': '',
                'sales_price': '',
                'passed': False,
                'issues': f'Exception: {str(e)}'
            })
        
        print()
    
    # Save results to CSV
    if results:
        output_file = 'data/test_price_fixes_results.csv'
        os.makedirs('data', exist_ok=True)
        
        fieldnames = ['url', 'name', 'product_id', 'status', 'regular_price', 'sales_price', 'passed', 'issues']
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        
        print("="*80)
        print("TEST SUMMARY")
        print("="*80)
        passed_count = sum(1 for r in results if r['passed'])
        print(f"Passed: {passed_count}/{len(results)}")
        print(f"Results saved to: {output_file}")
        print()
        
        if passed_count == len(results):
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. See details above.")
            for r in results:
                if not r['passed']:
                    print(f"\n  Failed: {r['name']}")
                    print(f"    Issues: {r['issues']}")

if __name__ == "__main__":
    test_price_fixes()
