#!/usr/bin/env python3

import logging
from src.scrapers.tate_yoko_scraper import TateYokoScraper

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    scraper = TateYokoScraper()
    
    try:
        print("Starting size chart scraping for all products...")
        size_data = scraper.scrape_size_charts()
        
        print(f"\nSize chart scraping completed successfully!")
        print(f"Total size entries scraped: {len(size_data)}")
        
        # Save to CSV
        scraper.save_size_charts_to_csv(size_data, "tate_yoko_size_charts.csv")
        print(f"Data saved to: data/processed/tate_yoko_size_charts.csv")
        
        # Also save to JSON for backup
        scraper.save_to_json(size_data, "tate_yoko_size_charts.json")
        print(f"Backup saved to: data/raw/tate_yoko_size_charts.json")
        
        return 0
        
    except Exception as e:
        logging.error(f"Size chart scraper failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
