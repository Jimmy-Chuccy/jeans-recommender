from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime
import time
import csv
import json

class TateYokoScraper(BaseScraper):
    def __init__(self):
        super().__init__("Tate+Yoko", "https://tateandyoko.com")
        
    def get_product_urls(self) -> List[str]:
        """Get all product URLs from Tate+Yoko jeans collection with pagination"""
        urls = []
        
        # Start with the main jeans collection page
        base_url = "https://tateandyoko.com/collections/jeans"
        page = 1
        max_pages = 10  # Safety limit
        
        while page <= max_pages:
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page}"
                
            self.logger.info(f"Scraping page {page}: {url}")
            soup = self.get_page(url)
            
            if not soup:
                self.logger.warning(f"Failed to load page {page}")
                break
                
            # Find product links
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
            page_urls = []
            
            for link in product_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
                        page_urls.append(full_url)
            
            self.logger.info(f"Found {len(page_urls)} new products on page {page}")
            
            # Check if there are more pages by looking for page info
            page_info = soup.find(string=re.compile(r'Page \d+ of \d+'))
            if page_info:
                # Extract total pages from "Page X of Y" text
                match = re.search(r'Page \d+ of (\d+)', page_info)
                if match:
                    total_pages = int(match.group(1))
                    self.logger.info(f"Found page info: {page_info.strip()}, total pages: {total_pages}")
                    if page >= total_pages:
                        self.logger.info(f"Reached last page ({total_pages}), stopping pagination")
                        break
            
            # If no new products found, we've likely reached the end
            if not page_urls:
                self.logger.info(f"No new products found on page {page}, stopping pagination")
                break
                
            page += 1
            time.sleep(1)  # Be respectful
            
        self.logger.info(f"Found {len(urls)} total product URLs across {page-1} pages")
        return urls
        
    def scrape_product(self, url: str) -> Optional[Dict]:
        """Scrape individual Tate+Yoko product following the schema"""
        soup = self.get_page(url)
        if not soup:
            return None
            
        try:
            product_data = {}
            
            # Extract product name
            title_elem = soup.find('h1', class_='product-title') or soup.find('h1')
            product_name = self.extract_text(title_elem)
            
            if not product_name:
                self.logger.warning(f"No product name found for {url}")
                return None
                
            # Generate product_id following the schema pattern: {fit_id}_{fabric_id}_{wash_state}
            product_data['product_id'] = self._generate_product_id(product_name, url)
            product_data['product_name'] = product_name
            
            # Extract fit information
            fit_info = self._extract_fit_info(product_name, soup)
            product_data['fit_id'] = fit_info['fit_id']
            product_data['fabric_id'] = fit_info['fabric_id']
            product_data['wash_state'] = fit_info['wash_state']
            
            # Extract gender
            product_data['gender'] = self._extract_gender(url, product_name, soup)
            
            # Extract colorway
            product_data['colorway'] = self._extract_colorway(product_name, soup)
            
            # Extract status - FIXED: Use "on-sales" or "regular"
            product_data['status'] = self._extract_status(soup)
            
            # URLs
            product_data['ty_product_url'] = url
            product_data['nf_product_url'] = self._find_nf_url(soup)
            
            # Extract description HTML
            desc_elem = soup.find('div', class_='product-description') or soup.find('div', class_='description')
            if desc_elem:
                product_data['description_html'] = str(desc_elem)
            else:
                product_data['description_html'] = ''
            
            # Extract release season
            product_data['release_season'] = self._extract_release_season(soup)
            
            # Extract run code
            product_data['run_code'] = self._extract_run_code(product_name, soup)
            
            # Extract notes
            product_data['notes'] = self._extract_notes(soup)
            
            # Extract default inseam label
            product_data['default_inseam_label'] = self._extract_inseam_label(soup)
            
            # NEW: Extract additional product detail information
            product_data['sku'] = self._extract_sku(soup)
            product_data['denim_weight'] = self._extract_denim_weight(soup)
            product_data['denim_cat'] = self._extract_denim_category(soup)
            product_data['made_in'] = self._extract_made_in(soup)
            product_data['product_description'] = self._extract_product_description(soup)
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {url}: {str(e)}")
            return None
    
    def _generate_product_id(self, product_name: str, url: str) -> str:
        """Generate UNIQUE product_id following schema pattern: {fit_id}_{fabric_id}_{wash_state}"""
        # Extract fit
        fit_match = re.search(r'(Super Guy|Weird Guy|Easy Guy|True Guy|Strong Guy|Groovy Guy|Stacked Guy|Skinny Guy)', product_name)
        fit_id = fit_match.group(1).lower().replace(' ', '_') if fit_match else 'unknown_fit'
        
        # Extract fabric info from text after "-" in product name
        fabric_id = self._extract_fabric_from_name(product_name)
        
        # Extract wash state
        wash_state = 'raw'  # Default
        if 'washed' in product_name.lower():
            wash_state = 'washed'
        elif 'rinsed' in product_name.lower():
            wash_state = 'rinsed'
        elif 'one wash' in product_name.lower():
            wash_state = 'one_wash'
            
        # Create base product_id
        base_product_id = f"{fit_id}_{fabric_id}_{wash_state}"
        
        # Extract URL slug for uniqueness
        url_slug = url.split('/')[-1]  # Get the last part of URL
        url_slug = url_slug.replace('-', '_')
        
        # Combine for uniqueness: {fit_id}_{fabric_id}_{wash_state}_{url_slug}
        unique_product_id = f"{base_product_id}_{url_slug}"
        
        return unique_product_id
    
    def _extract_fabric_from_name(self, product_name: str) -> str:
        """Extract fabric_id from text after '-' in product name"""
        # Split by '-' and take everything after the first '-'
        parts = product_name.split(' - ', 1)
        if len(parts) > 1:
            fabric_text = parts[1].strip()
            # Convert to snake_case
            fabric_id = fabric_text.lower().replace(' ', '_').replace('&', 'and').replace('-', '_')
            # Clean up any double underscores
            fabric_id = re.sub(r'_+', '_', fabric_id)
            # Remove trailing underscores
            fabric_id = fabric_id.strip('_')
            return fabric_id
        return 'standard'
    
    def _extract_fit_info(self, product_name: str, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract fit, fabric, and wash state information"""
        # Extract fit
        fit_match = re.search(r'(Super Guy|Weird Guy|Easy Guy|True Guy|Strong Guy|Groovy Guy|Stacked Guy|Skinny Guy)', product_name)
        fit_id = fit_match.group(1).lower().replace(' ', '_') if fit_match else 'unknown_fit'
        
        # Extract fabric from product name (text after '-')
        fabric_id = self._extract_fabric_from_name(product_name)
        
        # Extract wash state
        wash_state = 'raw'  # Default
        if 'washed' in product_name.lower():
            wash_state = 'washed'
        elif 'rinsed' in product_name.lower():
            wash_state = 'rinsed'
        elif 'one wash' in product_name.lower():
            wash_state = 'one_wash'
            
        return {
            'fit_id': fit_id,
            'fabric_id': fabric_id,
            'wash_state': wash_state
        }
    
    def _extract_gender(self, url: str, product_name: str, soup: BeautifulSoup) -> str:
        """Extract gender information"""
        if '/womens' in url or 'women' in product_name.lower():
            return 'womens'
        elif '/mens' in url or 'men' in product_name.lower():
            return 'mens'
        else:
            # Default to mens for most Naked & Famous products
            return 'mens'
    
    def _extract_colorway(self, product_name: str, soup: BeautifulSoup) -> str:
        """Extract colorway information"""
        colors = []
        if 'black' in product_name.lower():
            colors.append('black')
        if 'indigo' in product_name.lower():
            colors.append('indigo')
        if 'blue' in product_name.lower():
            colors.append('blue')
            
        if colors:
            return '/'.join(colors)
        return 'indigo/indigo'  # Default
    
    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extract product status - FIXED: Use 'on-sales' or 'regular'"""
        # Look for sale price indicators in the product area
        sale_price_elem = soup.find('span', class_='product-meta__price--new')
        old_price_elem = soup.find('span', class_='product-meta__price--old')
        
        # If we find both sale and old price, it's on sale
        if sale_price_elem and old_price_elem:
            return 'on-sales'
            
        # Check for sold out indicators
        sold_out_elem = soup.find('span', string=re.compile(r'Sold out', re.I))
        if sold_out_elem:
            return 'discontinued'
            
        return 'regular'  # Default for regular price items
    
    def _find_nf_url(self, soup: BeautifulSoup) -> str:
        """Find Naked & Famous product URL if available"""
        # Look for links to nakedandfamousdenim.com
        nf_links = soup.find_all('a', href=re.compile(r'nakedandfamousdenim\.com'))
        if nf_links:
            return nf_links[0].get('href')
        return ''
    
    def _extract_release_season(self, soup: BeautifulSoup) -> str:
        """Extract release season"""
        # Look for season indicators in the page
        season_elem = soup.find(string=re.compile(r'(FW|SS)\d{2}'))
        if season_elem:
            return season_elem.strip()
        return ''
    
    def _extract_run_code(self, product_name: str, soup: BeautifulSoup) -> str:
        """Extract run code if available"""
        # Look for run indicators in product name or description
        run_match = re.search(r'(run|batch|lot)\s*([A-Z0-9]+)', product_name.lower())
        if run_match:
            return run_match.group(2)
        return ''
    
    def _extract_notes(self, soup: BeautifulSoup) -> str:
        """Extract any notable information"""
        notes = []
        
        # Check for special features
        if soup.find(string=re.compile(r'limited edition', re.I)):
            notes.append('limited edition')
        if soup.find(string=re.compile(r'exclusive', re.I)):
            notes.append('exclusive')
        if soup.find(string=re.compile(r'collaboration', re.I)):
            notes.append('collaboration')
            
        return '; '.join(notes) if notes else ''
    
    def _extract_inseam_label(self, soup: BeautifulSoup) -> str:
        """Extract default inseam label"""
        # Look for inseam information
        inseam_elem = soup.find(string=re.compile(r'inseam.*?(\d+)', re.I))
        if inseam_elem:
            inseam_match = re.search(r'(\d+)', inseam_elem)
            if inseam_match:
                return inseam_match.group(1)
        return ''
    
    # NEW METHODS FOR ADDITIONAL PRODUCT DETAILS
    
    def _extract_sku(self, soup: BeautifulSoup) -> str:
        """Extract SKU from product detail page"""
        # Look for SKU in various formats
        sku_patterns = [
            r'SKU:\s*([A-Z0-9]+)',
            r'SKU\s*([A-Z0-9]+)',
            r'Product Code:\s*([A-Z0-9]+)',
            r'Item #:\s*([A-Z0-9]+)'
        ]
        
        # Search in all text content
        page_text = soup.get_text()
        for pattern in sku_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_denim_weight(self, soup: BeautifulSoup) -> str:
        """Extract denim weight (e.g., '13oz') from product detail page"""
        # Look for weight patterns like "13oz", "14.5oz", etc.
        weight_patterns = [
            r'(\d+(?:\.\d+)?)oz\s+Japanese\s+Selvedge\s+Denim',
            r'(\d+(?:\.\d+)?)oz\s+selvedge\s+denim',
            r'(\d+(?:\.\d+)?)oz\s+denim',
            r'(\d+(?:\.\d+)?)oz'
        ]
        
        # Search in all text content
        page_text = soup.get_text()
        for pattern in weight_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}oz"
        
        return ''
    
    def _extract_denim_category(self, soup: BeautifulSoup) -> str:
        """Extract denim category (e.g., '13oz Japanese Selvedge Denim')"""
        # First try to find in list items (more reliable)
        list_items = soup.find_all('li')
        for li in list_items:
            text = li.get_text(strip=True)
            if 'oz' in text and ('selvedge' in text.lower() or 'denim' in text.lower()):
                # Clean up the text and return as-is
                return text
        
        # Fallback: search in all text content with more flexible patterns
        category_patterns = [
            r'(\d+(?:\.\d+)?oz\s+Japanese\s+[Ss]elvedge\s+[Dd]enim)',
            r'(\d+(?:\.\d+)?oz\s+Japanese\s+[Dd]enim)',
            r'(\d+(?:\.\d+)?oz\s+[Ss]elvedge\s+[Dd]enim)',
            r'(\d+(?:\.\d+)?oz\s+[Dd]enim)'
        ]
        
        page_text = soup.get_text()
        for pattern in category_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_product_description(self, soup: BeautifulSoup) -> str:
        """Extract the main product description text"""
        # Try multiple selectors for the product description
        selectors = [
            'div.product_description.rte',
            'div.product-description.rte', 
            'div.rte',
            'div.product_info .product_description',
            'div[class*="description"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # Get the text content, not HTML
                desc_text = elem.get_text(strip=True)
                if desc_text and len(desc_text) > 50:  # Ensure it's substantial content
                    return desc_text
        
        return ''
    
    def _extract_size_chart(self, soup: BeautifulSoup, product_url: str) -> List[Dict]:
        """Extract size chart data from product detail page"""
        size_data = []
        
        # Find the size chart table
        table = soup.select_one('table.ks-table')
        if not table:
            self.logger.warning(f"No size chart table found for {product_url}")
            return size_data
        
        # Get table headers (sizes)
        header_row = table.find('tr')
        if not header_row:
            return size_data
        
        # Extract size headers (skip first column which is measurement type)
        size_headers = []
        header_cells = header_row.find_all(['th', 'td'])
        for cell in header_cells[1:]:  # Skip first column
            size_text = cell.get_text(strip=True)
            if size_text and size_text != 'Tag Size':
                size_headers.append(size_text)
        
        if not size_headers:
            self.logger.warning(f"No size headers found for {product_url}")
            return size_data
        
        # Extract measurement rows
        measurement_rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in measurement_rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
            
            # First cell is the measurement type
            measurement_type = cells[0].get_text(strip=True).lower().replace(' ', '_')
            
            # Extract measurements for each size
            for i, cell in enumerate(cells[1:], 0):  # Start from second cell
                if i >= len(size_headers):
                    break
                
                size = size_headers[i]
                
                # Get measurement value from data-unit-values attribute (inches = index 0)
                data_values = cell.get('data-unit-values')
                if data_values:
                    try:
                        import json
                        values = json.loads(data_values)
                        measurement_value = float(values.get('0', 0))  # Index 0 = inches
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # Fallback to text content
                        measurement_value = self.extract_number(cell.get_text(strip=True))
                else:
                    # Fallback to text content
                    measurement_value = self.extract_number(cell.get_text(strip=True))
                
                if measurement_value is not None:
                    # Find existing size entry or create new one
                    size_entry = None
                    for entry in size_data:
                        if entry['tag_size'] == size:
                            size_entry = entry
                            break
                    
                    if not size_entry:
                        size_entry = {
                            'product_url': product_url,
                            'tag_size': size,
                            'waist': None,
                            'front_rise': None,
                            'back_rise': None,
                            'upper_thigh': None,
                            'knee': None,
                            'leg_opening': None,
                            'inseam': None
                        }
                        size_data.append(size_entry)
                    
                    # Add measurement to the size entry
                    size_entry[measurement_type] = measurement_value
        
        return size_data
    
    def _extract_made_in(self, soup: BeautifulSoup) -> str:
        """Extract 'Made in' information - IMPROVED to prioritize list items"""
        # Look for "Made in" patterns in list items first (most reliable)
        list_items = soup.find_all('li')
        for li in list_items:
            li_text = li.get_text().strip()
            if 'Made in' in li_text:
                # Extract country from the list item
                match = re.search(r'Made in\s+([A-Za-z\s]+)', li_text, re.IGNORECASE)
                if match:
                    country = match.group(1).strip()
                    country = re.sub(r'\s+', ' ', country)  # Remove extra whitespace
                    return f"Made in {country}"
        
        # Fallback: Look in product description area
        product_desc = soup.find('div', class_='product-description')
        if product_desc:
            desc_text = product_desc.get_text()
            match = re.search(r'Made in\s+([A-Za-z\s]+)', desc_text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                country = re.sub(r'\s+', ' ', country)
                country = country.split('\n')[0]
                return f"Made in {country}"
        
        # Final fallback: search in all text but prioritize shorter matches
        page_text = soup.get_text()
        all_matches = []
        matches = re.findall(r'Made in\s+([A-Za-z\s]+)', page_text, re.IGNORECASE)
        for match in matches:
            country = match.strip()
            country = re.sub(r'\s+', ' ', country)
            country = country.split('\n')[0]
            # Only include reasonable country names
            if len(country) < 50 and not any(word in country.lower() for word in ['jeans', 'pants', 'jackets', 'shirts']):
                all_matches.append((country, len(country)))
        
        # Return the shortest match (most likely to be the correct one)
        if all_matches:
            all_matches.sort(key=lambda x: x[1])  # Sort by length
            return f"Made in {all_matches[0][0]}"
        
        return ''
    
    def save_to_csv(self, data: List[Dict], filename: str = "products.csv"):
        """Save scraped data to CSV following the schema"""
        os.makedirs('data/processed', exist_ok=True)
        filepath = f'data/processed/{filename}'
        
        # Define required columns according to schema + new fields
        required_columns = [
            'product_id', 'product_name', 'fit_id', 'fabric_id', 'wash_state',
            'gender', 'default_inseam_label', 'colorway', 'status',
            'nf_product_url', 'ty_product_url', 'description_html',
            'release_season', 'run_code', 'notes',
            'sku', 'denim_weight', 'denim_cat', 'made_in', 'product_description'  # NEW FIELDS
        ]
        
        # Write CSV file with proper escaping
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(required_columns)  # Write header
            
            for item in data:
                # Ensure all required columns are present and clean
                row = []
                for col in required_columns:
                    value = item.get(col, '')
                    # Clean the value - remove any JavaScript or unwanted content
                    if isinstance(value, str):
                        # Remove any JavaScript code that might have been scraped
                        value = re.sub(r'<script.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
                        value = re.sub(r'KiwiSizing.*?};', '', value, flags=re.DOTALL | re.IGNORECASE)
                        value = value.strip()
                    else:
                        value = str(value) if value is not None else ''
                    row.append(value)
                writer.writerow(row)
        
        self.logger.info(f"Saved {len(data)} products to {filepath}")
        return filepath
    
    def scrape_all(self) -> List[Dict]:
        """Main method to scrape all products and save to CSV"""
        self.logger.info(f"Starting to scrape {self.brand_name}")
        
        product_urls = self.get_product_urls()
        self.logger.info(f"Found {len(product_urls)} product URLs")
        
        products = []
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
            product_data = self.scrape_product(url)
            if product_data:
                products.append(product_data)
            time.sleep(1)  # Be respectful
            
        # Save to CSV following the schema
        csv_file = self.save_to_csv(products, "tate_yoko_products.csv")
        
        # Also save to JSON for backup
        self.save_to_json(products, "tate_yoko_products.json")
        
        self.logger.info(f"Scraping completed. Found {len(products)} products.")
        return products
    
    def scrape_size_charts(self) -> List[Dict]:
        """Scrape size chart data for all products"""
        self.logger.info("Starting to scrape size charts for all products")
        
        # Get all product URLs
        product_urls = self.get_product_urls()
        self.logger.info(f"Found {len(product_urls)} product URLs for size chart scraping")
        
        all_size_data = []
        
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping size chart {i}/{len(product_urls)}: {url}")
            
            # Use Selenium to get the fully rendered page
            soup = self.get_page(url, use_selenium=True)
            if not soup:
                self.logger.warning(f"Failed to load page {url}")
                continue
            
            # Extract size chart data
            size_data = self._extract_size_chart(soup, url)
            if size_data:
                all_size_data.extend(size_data)
                self.logger.info(f"Extracted {len(size_data)} size entries for {url}")
            else:
                self.logger.warning(f"No size chart data found for {url}")
            
            # Be respectful with requests
            time.sleep(1)
        
        self.logger.info(f"Size chart scraping completed. Found {len(all_size_data)} total size entries")
        return all_size_data
    
    def save_size_charts_to_csv(self, size_data: List[Dict], filename: str):
        """Save size chart data to CSV file"""
        os.makedirs('data/processed', exist_ok=True)
        filepath = f'data/processed/{filename}'
        
        if not size_data:
            self.logger.warning("No size chart data to save to CSV.")
            return
        
        # Define CSV headers for size chart data
        fieldnames = [
            'product_url', 'tag_size', 'waist', 'front_rise', 'back_rise', 
            'upper_thigh', 'knee', 'leg_opening', 'inseam'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for item in size_data:
                # Ensure all fields are present, fill missing with None
                row = {field: item.get(field) for field in fieldnames}
                writer.writerow(row)
        
        self.logger.info(f"Saved {len(size_data)} size chart entries to {filepath}")
