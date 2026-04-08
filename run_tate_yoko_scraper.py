#!/usr/bin/env python3
"""
Main script to run the Tate+Yoko scraper
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.tate_yoko_scraper import TateYokoScraper
import logging

def main():
    """Main function to run the scraper"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create scraper instance
    scraper = TateYokoScraper()
    
    try:
        # Run the scraper
        products = scraper.scrape_all()
        
        print(f"\nScraping completed successfully!")
        print(f"Total products scraped: {len(products)}")
        print(f"Data saved to: data/processed/tate_yoko_products.csv")
        print(f"Backup saved to: data/raw/tate_yoko_products.json")
        
    except Exception as e:
        print(f"Error running scraper: {str(e)}")
        logging.error(f"Scraper failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
