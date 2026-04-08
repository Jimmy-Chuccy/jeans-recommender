#!/usr/bin/env python3
"""
Script to scrape the new Naked & Famous website
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.naked_famous_new_scraper import NakedFamousNewScraper

if __name__ == "__main__":
    scraper = NakedFamousNewScraper()
    products = scraper.scrape_all()
    print(f"\n✅ Scraping complete! Found {len(products)} products.")
    print(f"Data saved with timestamp and as latest version")

