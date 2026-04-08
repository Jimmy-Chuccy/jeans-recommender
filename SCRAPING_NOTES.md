# Naked & Famous New Website Scraper

## Overview
This scraper targets the new Naked & Famous website at https://nakedandfamousdenim.com/

## Collections Scraped
1. **All Men's Jeans**: https://nakedandfamousdenim.com/collections/men-jeans
2. **Latest Arrivals**: https://nakedandfamousdenim.com/collections/mens-latest-arrivals
3. **Coming Soon**: https://nakedandfamousdenim.com/collections/men-s-coming-soon
4. **Fall/Winter 2025**: https://nakedandfamousdenim.com/collections/g-fall-winter-2025/Mens
5. **Core Essentials**: https://nakedandfamousdenim.com/collections/core-menu
6. **Made in Japan**: https://nakedandfamousdenim.com/collections/made-in-japan-menu

## Features
- **Deduplication**: Products appearing in multiple collections are stored only once
- **Collection Labels**: Each product tracks which collections it belongs to (semicolon-separated)
- **Filtering**: Automatically filters out non-jeans products (gift cards, accessories, jackets, etc.)
- **Schema Compatibility**: Uses the same schema as the old CSV with an added `collections` field

## Output
- CSV: `data/processed/naked_famous_products_new.csv`
- JSON: `data/raw/naked_famous_products_new.json`

## Notes
- Uses Selenium for JavaScript-heavy pages
- Includes delays to be respectful to the server
- May take 1-2 hours to complete full scrape depending on number of products

