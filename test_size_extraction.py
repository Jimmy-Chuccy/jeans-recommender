#!/usr/bin/env python3

import logging
from src.scrapers.tate_yoko_scraper import TateYokoScraper

def test_size_extraction():
    """Test size chart extraction on a sample product"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    scraper = TateYokoScraper()
    
    # Test on a single product
    test_url = "https://tateandyoko.com/collections/jeans/products/strong-guy-solid-black-selvedge"
    
    print(f"Testing size chart extraction on: {test_url}")
    
    # Use Selenium to get the fully rendered page
    soup = scraper.get_page(test_url, use_selenium=True)
    if not soup:
        print("Failed to load page")
        return
    
    # Extract size chart data
    size_data = scraper._extract_size_chart(soup, test_url)
    
    print(f"\nExtracted {len(size_data)} size entries:")
    for entry in size_data[:5]:  # Show first 5 entries
        print(f"  Size {entry['tag_size']}: waist={entry['waist']}, front_rise={entry['front_rise']}, back_rise={entry['back_rise']}")
    
    if len(size_data) > 5:
        print(f"  ... and {len(size_data) - 5} more entries")
    
    # Test CSV saving
    scraper.save_size_charts_to_csv(size_data, "test_size_charts.csv")
    print(f"\nSaved test data to data/processed/test_size_charts.csv")

if __name__ == "__main__":
    test_size_extraction()
