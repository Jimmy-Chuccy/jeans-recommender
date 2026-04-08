"""
Scraper for the new Naked & Famous website (nakedandfamousdenim.com)
Handles multiple collections and deduplicates products while preserving collection labels
"""

from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import re
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime
import time
import csv
import json


class NakedFamousNewScraper(BaseScraper):
    """Scraper for the new Naked & Famous website"""
    
    # Collection URLs to scrape with display names (men's collections only)
    COLLECTION_URLS = {
        "All Mens": "https://nakedandfamousdenim.com/collections/men-jeans",
        "Latest Arrivals": "https://nakedandfamousdenim.com/collections/mens-latest-arrivals",
        "Coming Soon": "https://nakedandfamousdenim.com/collections/men-s-coming-soon",
        "Spring/Summer 26": "https://nakedandfamousdenim.com/collections/mens-naked-famous-denim-spring-summer-2026",
        "Fall/Winter 2025": "https://nakedandfamousdenim.com/collections/g-fall-winter-2025/Mens",
        "Core Essentials": "https://nakedandfamousdenim.com/collections/core-menu",
        "Made in Japan": "https://nakedandfamousdenim.com/collections/made-in-japan-menu",
    }
    
    def __init__(self):
        super().__init__("Naked & Famous New", "https://nakedandfamousdenim.com")
        # Track products and their collections: {product_url: [collection_names]}
        self._product_collections: Dict[str, List[str]] = {}
    
    def get_product_urls_from_collection(self, collection_url: str, collection_name: str) -> List[str]:
        """
        Get all product URLs from a collection page with pagination
        
        Args:
            collection_url: URL of the collection
            collection_name: Name of the collection for tracking
        
        Returns:
            List of product URLs
        """
        urls = []
        page = 1
        max_pages = 50  # Safety limit
        
        self.logger.info(f"Scraping collection '{collection_name}': {collection_url}")
        
        while page <= max_pages:
            if page == 1:
                url = collection_url
            else:
                # Handle pagination - Shopify typically uses ?page=X
                url = f"{collection_url}?page={page}"
            
            self.logger.info(f"  Page {page}: {url}")
            soup = self.get_page(url, use_selenium=True)
            
            if not soup:
                self.logger.warning(f"Failed to load page {page}")
                break
            
            # Find product links - Shopify sites often use /products/ in href
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
            page_urls = []
            
            for link in product_links:
                href = link.get('href')
                if href:
                    # Handle relative URLs
                    if href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                    else:
                        full_url = href
                    
                    # Only include actual product pages (not collections or other pages)
                    if '/products/' in full_url and full_url not in urls:
                        urls.append(full_url)
                        page_urls.append(full_url)
                        
                        # Track which collection this product belongs to
                        if full_url not in self._product_collections:
                            self._product_collections[full_url] = []
                        if collection_name not in self._product_collections[full_url]:
                            self._product_collections[full_url].append(collection_name)
            
            self.logger.info(f"  Found {len(page_urls)} new products on page {page}")
            
            # Check if there are more pages
            # Look for pagination indicators
            next_page_link = soup.find('a', href=re.compile(r'page=' + str(page + 1)))
            pagination_info = soup.find(string=re.compile(r'Page \d+ of \d+', re.I))
            
            if not next_page_link and not pagination_info:
                # Check if we found any products on this page
                if not page_urls:
                    self.logger.info(f"  No products found on page {page}, stopping")
                    break
            
            # If no new products found, we've likely reached the end
            if not page_urls and page > 1:
                self.logger.info(f"  No new products found on page {page}, stopping pagination")
                break
            
            page += 1
            time.sleep(2)  # Be respectful with requests
        
        self.logger.info(f"Collection '{collection_name}': Found {len(urls)} total product URLs")
        return urls
    
    def get_all_product_urls(self) -> Dict[str, List[str]]:
        """
        Get all product URLs from all collections
        
        Returns:
            Dictionary mapping collection names to product URLs
        """
        all_urls = {}
        
        for collection_name, collection_url in self.COLLECTION_URLS.items():
            urls = self.get_product_urls_from_collection(collection_url, collection_name)
            all_urls[collection_name] = urls
            time.sleep(1)  # Be respectful between collections
        
        return all_urls
    
    def scrape_product(self, url: str) -> Optional[Dict]:
        """
        Scrape individual product page
        
        Args:
            url: Product URL
        
        Returns:
            Product data dictionary or None
        """
        soup = self.get_page(url, use_selenium=True)
        if not soup:
            return None
        
        try:
            product_data = {}
            
            # Extract product name - try multiple selectors (Shopify patterns)
            # Try JSON-LD structured data first (most reliable)
            product_name = None
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'name' in data:
                        product_name = data['name']
                        break
                    # Handle list of structured data
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'name' in item:
                                product_name = item['name']
                                break
                        if product_name:
                            break
                except:
                    pass
            
            # Fallback to HTML selectors
            if not product_name:
                # Try meta tags first (often more reliable)
                meta_og = soup.find('meta', property='og:title')
                if meta_og and meta_og.get('content'):
                    product_name = meta_og.get('content')
                
                if not product_name:
                    meta_product = soup.find('meta', property='product:title')
                    if meta_product and meta_product.get('content'):
                        product_name = meta_product.get('content')
                
                # Try various h1/h2 selectors
                if not product_name:
                    title_elem = (
                        soup.find('h1', class_=re.compile(r'product|title', re.I)) or
                        soup.find('h1') or
                        soup.find('h2', class_=re.compile(r'product|title', re.I))
                    )
                    if title_elem:
                        product_name = self.extract_text(title_elem)
                
                # Last resort: try page title
                if not product_name or product_name.lower() in ['site map', '404', 'not found']:
                    page_title = soup.find('title')
                    if page_title:
                        title_text = self.extract_text(page_title)
                        # Remove common suffixes
                        title_text = re.sub(r'\s*[-|]\s*Naked.*?$', '', title_text, flags=re.I)
                        if title_text and title_text.lower() not in ['site map', '404', 'not found']:
                            product_name = title_text.strip()
            
            if not product_name:
                self.logger.warning(f"No product name found for {url}")
                return None
            
            # Generate product_id
            product_data['product_id'] = self._generate_product_id(product_name, url)
            product_data['product_name'] = product_name
            
            # Extract SKU early (needs to be next to product_id)
            product_data['sku'] = self._extract_sku_from_table(soup)
            
            # Extract fit information (may be empty for non-jeans products)
            fit_info = self._extract_fit_info(product_name, soup)
            product_data['fit_id'] = fit_info.get('fit_id', '')
            product_data['fabric_id'] = fit_info.get('fabric_id', '')
            product_data['wash_state'] = fit_info.get('wash_state', '')
            
            # Extract gender
            product_data['gender'] = self._extract_gender(url, product_name, soup)
            
            # Extract colorway
            product_data['colorway'] = self._extract_colorway(product_name, soup)
            
            # Extract status and prices (fallback: use _extract_status_and_prices_regular_safe(soup) for regular-only behavior)
            status_result = self._extract_status_and_prices(soup)
            product_data['status'] = status_result['status']
            product_data['regular_price'] = status_result.get('regular_price', '')
            product_data['sales_price'] = status_result.get('sales_price', '')
            
            # Add timestamp for when this product was scraped
            product_data['scraped_at'] = datetime.now().isoformat()
            
            # URLs
            product_data['nf_product_url'] = url
            
            # Extract description HTML - only if meaningful content found
            # Leave blank if we can't extract meaningful data
            desc_elem = (
                soup.find('div', class_=re.compile(r'product.*description', re.I)) or
                soup.find('div', class_=re.compile(r'description', re.I)) or
                soup.find('div', {'id': re.compile(r'product.*description', re.I)}) or
                soup.find('div', class_='rte') or
                soup.find('div', {'data-product-description': True})
            )
            # Only set if we find meaningful content (not just empty divs)
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if desc_text and len(desc_text) > 20:  # Meaningful content threshold
                    product_data['description_html'] = str(desc_elem)
                else:
                    product_data['description_html'] = ''
            else:
                product_data['description_html'] = ''
            
            # Extract release season - only meaningful formats like SS2025, FW2025
            product_data['release_season'] = self._extract_release_season(soup, product_name)
            
            # Extract run code
            product_data['run_code'] = self._extract_run_code(product_name, soup)
            
            # Extract notes
            product_data['notes'] = self._extract_notes(soup)
            
            # Extract default inseam label
            product_data['default_inseam_label'] = self._extract_inseam_label(soup)
            
            # Extract additional product details from labelcard table
            table_data = self._extract_labelcard_table(soup)
            # Use fabric_id from labelcard if not already extracted (for non-jeans products)
            if not product_data.get('fabric_id') and table_data.get('fabric_id'):
                product_data['fabric_id'] = table_data.get('fabric_id', '')
            product_data['denim_weight_oz'] = table_data.get('denim_weight_oz', '')
            product_data['denim_cat'] = table_data.get('denim_cat', '')
            product_data['made_in'] = table_data.get('made_in', '')
            product_data['material'] = table_data.get('material', '')
            product_data['product_description'] = self._extract_product_description(soup)
            
            # Add collection labels
            collections = self._product_collections.get(url, [])
            product_data['collections'] = '; '.join(collections) if collections else ''
            
            # Add is_jeans flag (Option 3: label to indicate jeans vs non-jeans)
            product_data['is_jeans'] = 'yes' if product_data.get('fit_id') else 'no'
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {url}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _generate_product_id(self, product_name: str, url: str) -> str:
        """Generate product_id following schema pattern"""
        # Extract fit
        fit_match = re.search(
            r'(Super Guy|Weird Guy|Easy Guy|True Guy|Strong Guy|Groovy Guy|Stacked Guy|Skinny Guy|Super Girl|True Girl|Bestie|Maudie)',
            product_name
        )
        fit_id = fit_match.group(1).lower().replace(' ', '_') if fit_match else None
        
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
        
        # Create base product_id - only include fit_id if it exists (jeans products)
        if fit_id:
            base_product_id = f"{fit_id}_{fabric_id}_{wash_state}"
        else:
            # For non-jeans products, don't use 'unknown_fit' prefix
            base_product_id = f"{fabric_id}_{wash_state}" if fabric_id else wash_state
        
        # Use base_product_id as-is (fit + fabric + wash should be unique enough)
        # The combination of fit, fabric, and wash state should uniquely identify a product
        # If duplicates occur, they can be handled by adding additional distinguishing factors
        # but for now, we'll keep it simple as the user requested
        return base_product_id
    
    def _extract_fabric_from_name(self, product_name: str) -> str:
        """Extract fabric_id from text after '-' in product name"""
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
        """
        Extract fit, fabric, and wash state information
        Returns empty strings for non-jeans products
        """
        # Extract fit
        fit_match = re.search(
            r'(Super Guy|Weird Guy|Easy Guy|True Guy|Strong Guy|Groovy Guy|Stacked Guy|Skinny Guy|Super Girl|True Girl|Bestie|Maudie)',
            product_name
        )
        fit_id = fit_match.group(1).lower().replace(' ', '_') if fit_match else ''
        
        # Extract fabric from product name (only if we have a fit)
        if fit_id:
            fabric_id = self._extract_fabric_from_name(product_name)
        else:
            fabric_id = ''
        
        # Extract wash state (only for jeans)
        wash_state = ''
        if fit_id:  # Only extract wash state if it's a jeans product
            wash_state = 'raw'  # Default for jeans
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
        if '/women' in url.lower() or 'girl' in product_name.lower() or 'bestie' in product_name.lower() or 'maudie' in product_name.lower():
            return 'womens'
        elif '/men' in url.lower() or 'guy' in product_name.lower():
            return 'mens'
        else:
            return 'mens'  # Default
    
    def _extract_colorway(self, product_name: str, soup: BeautifulSoup) -> str:
        """Extract colorway information"""
        colors = []
        name_lower = product_name.lower()
        if 'black' in name_lower:
            colors.append('black')
        if 'indigo' in name_lower:
            colors.append('indigo')
        if 'blue' in name_lower and 'indigo' not in name_lower:
            colors.append('blue')
        if 'white' in name_lower:
            colors.append('white')
        if 'brown' in name_lower:
            colors.append('brown')
        if 'tan' in name_lower:
            colors.append('tan')
        if 'green' in name_lower:
            colors.append('green')
        if 'red' in name_lower:
            colors.append('red')
        if 'navy' in name_lower:
            colors.append('navy')
        
        if colors:
            return '/'.join(colors)
        return ''  # Leave blank if no color detected (for non-jeans products)
    
    def _extract_status(self, soup: BeautifulSoup) -> str:
        """
        Extract product status - look for crossed-out prices and sale prices
        Based on user feedback: products on sale have original price crossed out 
        and sale price shown. Must find BOTH in the same product price area.
        Returns 'on-sales' or 'regular'.
        """
        # Strategy: Find the main product price area and check if it has both
        # compare-at-price (crossed out) AND sale-price elements
        
        # First, try to find the main product price container
        # Look for common price container patterns
        price_container_selectors = [
            'div.product-price',
            'div.price',
            'span.price',
            'div[class*="price"]',
            'div[class*="product"][class*="price"]'
        ]
        
        main_price_container = None
        for selector in price_container_selectors:
            containers = soup.select(selector)
            # Prefer containers that are near the product title/name
            for container in containers:
                # Check if container is in the product area (not in related products)
                product_area = container.find_parent(['main', 'article', 'div'], class_=re.compile(r'product', re.I))
                if product_area:
                    main_price_container = container
                    break
            if main_price_container:
                break
        
        # If we found a main price container, check it specifically
        if main_price_container:
            compare_elem = main_price_container.find(class_=re.compile(r'compare-at-price|old-price|original-price', re.I))
            sale_elem = main_price_container.find(class_=re.compile(r'sale-price|current-price', re.I))
            
            if compare_elem and sale_elem:
                # Both found in main container - verify they're actual prices
                compare_text = compare_elem.get_text()
                sale_text = sale_elem.get_text()
                if re.search(r'\$\d+', compare_text) and re.search(r'\$\d+', sale_text):
                    # Extract and compare prices
                    compare_match = re.search(r'\$(\d+(?:\.\d+)?)', compare_text)
                    sale_match = re.search(r'\$(\d+(?:\.\d+)?)', sale_text)
                    if compare_match and sale_match:
                        compare_price = float(compare_match.group(1))
                        sale_price = float(sale_match.group(1))
                        # Sale price should be lower than compare price
                        if sale_price < compare_price:
                            return 'on-sales'
        
        # Fallback: Look for price elements - check for custom tags (compare-at-price, sale-price)
        # These are web components, so they're tag names, not classes
        all_compare_elems = []
        # Find <compare-at-price> custom tags
        all_compare_elems.extend(soup.find_all('compare-at-price'))
        # Also find elements with compare-at-price class (fallback)
        all_compare_elems.extend(soup.find_all(class_=re.compile(r'compare-at-price|old-price|original-price', re.I)))
        
        all_sale_elems = []
        # Find <sale-price> custom tags
        all_sale_elems.extend(soup.find_all('sale-price'))
        # Also find elements with sale-price class (fallback)
        all_sale_elems.extend(soup.find_all(class_=re.compile(r'sale-price|current-price', re.I)))
        
        # Check if any compare-at-price and sale-price are in the same container or are siblings
        for compare_elem in all_compare_elems:
            # Check if this element is in the main product area (not related products)
            product_area = compare_elem.find_parent(['main', 'article', 'div'], class_=re.compile(r'product', re.I))
            if not product_area:
                continue  # Skip if not in main product area
            
            # Get compare price text and value
            compare_text = compare_elem.get_text()
            if not re.search(r'\$\d+', compare_text):
                continue
            compare_match = re.search(r'\$(\d+(?:\.\d+)?)', compare_text)
            if not compare_match:
                continue
            compare_price = float(compare_match.group(1))
            
            # Check if compare element has line-through (crossed out)
            # FIX 1: Require actual line-through styling, not just tag name
            compare_classes = ' '.join(compare_elem.get('class', []))
            compare_style = compare_elem.get('style', '')
            # Check children for line-through (the price text is usually in a child)
            children_with_line_through = compare_elem.find_all(class_=re.compile(r'line-through', re.I))
            # Check if any child has line-through styling in style attribute
            children_with_style_line_through = compare_elem.find_all(style=re.compile(r'text-decoration.*line-through|text-decoration.*strikethrough', re.I))
            
            # Only consider crossed out if we have actual line-through styling
            # For <compare-at-price> tags, we still need to check children for styling
            is_crossed_out = (
                'line-through' in compare_classes.lower() or
                'line-through' in compare_style.lower() or
                'strikethrough' in compare_style.lower() or
                compare_elem.name in ['s', 'strike', 'del'] or  # Removed 'compare-at-price' - require actual styling
                len(children_with_line_through) > 0 or
                len(children_with_style_line_through) > 0
            )
            
            if not is_crossed_out:
                continue  # Skip if not actually crossed out
            
            # FIX 2 & 3: Look for sale-price with stricter proximity and variant matching
            # First, try to find variant/size context for this compare price
            variant_context = None
            check_parent = compare_elem.parent
            # Look for variant selectors (size, color, etc.) in nearby elements
            for _ in range(3):  # Check up to 3 levels for variant context
                if check_parent:
                    # Check for variant indicators
                    variant_selectors = check_parent.find_all(['select', 'input'], {'name': re.compile(r'variant|size|option', re.I)})
                    if variant_selectors:
                        variant_context = check_parent
                        break
                    check_parent = check_parent.parent if check_parent else None
            
            # Helper function to check if element is in same variant context
            def is_in_same_variant_context(elem):
                """Check if element is in the same variant context as compare_elem"""
                if not variant_context:
                    return True  # No variant context means all prices are in same context
                # Check if element is a descendant of the variant context
                elem_parent = elem.parent
                depth = 0
                while elem_parent and depth < 5:
                    if elem_parent == variant_context:
                        return True
                    elem_parent = elem_parent.parent if elem_parent else None
                    depth += 1
                return False
            
            # FIX 3: Stricter proximity - prioritize direct siblings and same immediate container
            # Check direct siblings first (most reliable)
            if compare_elem.parent:
                direct_siblings = compare_elem.parent.find_all('sale-price') + compare_elem.parent.find_all(class_=re.compile(r'sale-price|current-price', re.I))
                for sibling in direct_siblings:
                    # FIX 2: If we found variant context, ensure sibling is in same context
                    if not is_in_same_variant_context(sibling):
                        continue
                    
                    sibling_text = sibling.get_text()
                    if re.search(r'\$\d+', sibling_text):
                        sibling_match = re.search(r'\$(\d+(?:\.\d+)?)', sibling_text)
                        if sibling_match:
                            sibling_price = float(sibling_match.group(1))
                            if sibling_price < compare_price:
                                return 'on-sales'
            
            # Check same immediate parent container (depth 1)
            parent = compare_elem.parent
            if parent:
                sale_in_container = parent.find('sale-price') or parent.find(class_=re.compile(r'sale-price|current-price', re.I))
                if sale_in_container:
                    # FIX 2: Ensure same variant context if applicable
                    if not is_in_same_variant_context(sale_in_container):
                        sale_in_container = None
                    
                    if sale_in_container:
                        sale_text = sale_in_container.get_text()
                        if re.search(r'\$\d+', sale_text):
                            sale_match = re.search(r'\$(\d+(?:\.\d+)?)', sale_text)
                            if sale_match:
                                sale_price = float(sale_match.group(1))
                                if sale_price < compare_price:
                                    return 'on-sales'
            
            # FIX 3: Check parent's parent (depth 2) - reduced from 5 levels
            parent = compare_elem.parent
            depth = 0
            while parent and depth < 2:  # Reduced from 5 to 2 levels
                # Check if this container also has a sale-price element (tag or class)
                sale_in_container = parent.find('sale-price') or parent.find(class_=re.compile(r'sale-price|current-price', re.I))
                if sale_in_container:
                    # FIX 2: Ensure same variant context if applicable
                    if not is_in_same_variant_context(sale_in_container):
                        sale_in_container = None
                    
                    if sale_in_container:
                        sale_text = sale_in_container.get_text()
                        if re.search(r'\$\d+', sale_text):
                            sale_match = re.search(r'\$(\d+(?:\.\d+)?)', sale_text)
                            if sale_match:
                                sale_price = float(sale_match.group(1))
                                if sale_price < compare_price:
                                    return 'on-sales'
                
                # Check siblings at this level (but only if same variant context)
                if parent.parent:
                    siblings = parent.parent.find_all('sale-price') + parent.parent.find_all(class_=re.compile(r'sale-price|current-price', re.I))
                    for sibling in siblings:
                        # FIX 2: Ensure same variant context
                        if not is_in_same_variant_context(sibling):
                            continue
                        
                        sibling_text = sibling.get_text()
                        if re.search(r'\$\d+', sibling_text):
                            sibling_match = re.search(r'\$(\d+(?:\.\d+)?)', sibling_text)
                            if sibling_match:
                                sibling_price = float(sibling_match.group(1))
                                if sibling_price < compare_price:
                                    return 'on-sales'
                
                parent = parent.parent if parent else None
                depth += 1
        
        # If we only find sale-price elements without compare-at-price, it's regular price
        # If we only find compare-at-price without sale-price, it might be a display issue, treat as regular
        return 'regular'  # Default - no sale indicators found
    
    def _extract_release_season(self, soup: BeautifulSoup, product_name: str = '') -> str:
        """
        Extract release season - only meaningful formats like SS2025, FW2025
        Leave blank if can't extract actual meaningful data
        """
        # Look for season indicators in format SS2025, FW2025 (4-digit year)
        season_patterns = [
            r'(SS|FW)\s*20\d{2}',  # SS 2025, FW 2025
            r'(SS|FW)20\d{2}',     # SS2025, FW2025
        ]
        
        # Search in page text
        page_text = soup.get_text()
        for pattern in season_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                season = match.group(0).upper().replace(' ', '')
                return season
        
        # Also check product name
        if product_name:
            for pattern in season_patterns:
                match = re.search(pattern, product_name, re.IGNORECASE)
                if match:
                    season = match.group(0).upper().replace(' ', '')
                    return season
        
        # Don't return partial matches like "SS23" - only return if we find 4-digit year format
        return ''
    
    def _extract_run_code(self, product_name: str, soup: BeautifulSoup) -> str:
        """Extract run code if available"""
        run_match = re.search(r'(run|batch|lot)\s*([A-Z0-9]+)', product_name.lower())
        if run_match:
            return run_match.group(2)
        return ''
    
    def _extract_notes(self, soup: BeautifulSoup) -> str:
        """
        Extract notable product information
        Look for specific indicators in product metadata, not in description text
        """
        notes = []
        
        # Look for notes in specific areas, not in full page text (to avoid false positives)
        # Check meta tags first
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = meta.get('content', '').lower()
            if 'limited edition' in content:
                notes.append('limited edition')
            if 'exclusive' in content and 'exclusive' not in notes:
                # Only add if it's a product attribute, not in description
                notes.append('exclusive')
            if 'collaboration' in content:
                notes.append('collaboration')
        
        # Check product title/name area for specific indicators
        title_area = soup.find('h1') or soup.find('div', class_=re.compile(r'product.*title', re.I))
        if title_area:
            title_text = title_area.get_text().lower()
            if 'limited edition' in title_text and 'limited edition' not in notes:
                notes.append('limited edition')
            if 'collaboration' in title_text and 'collaboration' not in notes:
                notes.append('collaboration')
        
        # Don't search in description text to avoid false positives like "tried to keep it exclusive"
        # Only return notes if found in metadata/title areas
        
        return '; '.join(notes) if notes else ''
    
    def _extract_inseam_label(self, soup: BeautifulSoup) -> str:
        """Extract default inseam label"""
        inseam_elem = soup.find(string=re.compile(r'inseam.*?(\d+)', re.I))
        if inseam_elem:
            inseam_match = re.search(r'(\d+)', inseam_elem)
            if inseam_match:
                return inseam_match.group(1)
        return ''
    
    def _extract_sku_from_table(self, soup: BeautifulSoup) -> str:
        """Extract SKU from labelcard table (preferred method)"""
        labelcard = soup.find('ul', class_=re.compile(r'labelcard', re.I))
        if labelcard:
            rows = labelcard.find_all('li', class_=re.compile(r'lc-row', re.I))
            for row in rows:
                lines = row.find_all('span', class_=re.compile(r'lc-line', re.I))
                for line in lines:
                    key = line.find('span', class_=re.compile(r'lc-k', re.I))
                    value = line.find('span', class_=re.compile(r'lc-v', re.I))
                    if key and value:
                        key_text = key.get_text(strip=True)
                        if 'SKU' in key_text.upper():
                            return value.get_text(strip=True)
        
        # Fallback to old method
        sku_patterns = [
            r'SKU:\s*([A-Z0-9]+)',
            r'SKU\s*([A-Z0-9]+)',
            r'Product Code:\s*([A-Z0-9]+)',
            r'Item #:\s*([A-Z0-9]+)'
        ]
        
        page_text = soup.get_text()
        for pattern in sku_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_labelcard_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract data from labelcard table on product page
        Returns: dict with fabric_id, denim_weight_oz, denim_cat, made_in, material
        """
        result = {
            'fabric_id': '',
            'denim_weight_oz': '',
            'denim_cat': '',
            'made_in': '',
            'material': ''
        }
        
        labelcard = soup.find('ul', class_=re.compile(r'labelcard', re.I))
        if not labelcard:
            return result
        
        # Extract labelcard title (e.g., "Black Canvas", "Sea Island Selvedge - Indigo")
        # This is typically in a lc-head or lc-title element
        title_elem = labelcard.find('li', class_=re.compile(r'lc-head', re.I))
        if title_elem:
            title_div = title_elem.find('div', class_=re.compile(r'lc-title', re.I))
            if title_div:
                title_text = title_div.get_text(strip=True)
                if title_text:
                    # Convert to snake_case for fabric_id
                    fabric_id = title_text.lower().replace(' ', '_').replace('&', 'and').replace('-', '_')
                    fabric_id = re.sub(r'_+', '_', fabric_id).strip('_')
                    result['fabric_id'] = fabric_id
        
        rows = labelcard.find_all('li', class_=re.compile(r'lc-row', re.I))
        for row in rows:
            lines = row.find_all('span', class_=re.compile(r'lc-line', re.I))
            for line in lines:
                line_text = line.get_text(strip=True)
                
                # Extract weight and category - now matches ANY "oz" pattern (not just denim/selvedge)
                # This handles "10oz Japanese Canvas", "12oz Japanese Selvedge Denim", etc.
                if 'oz' in line_text.lower():
                    if not result['denim_cat']:
                        result['denim_cat'] = line_text
                    # Extract weight (numeric only)
                    weight_match = re.search(r'(\d+(?:\.\d+)?)', line_text)
                    if weight_match:
                        result['denim_weight_oz'] = weight_match.group(1)
                
                # Extract Made in (e.g., "Made in Canada")
                if 'made in' in line_text.lower():
                    result['made_in'] = line_text
                
                # Extract material (e.g., "99.6% Cotton / 0.4% Gold" or "100% Cotton")
                if '%' in line_text and ('cotton' in line_text.lower() or 'poly' in line_text.lower() or 
                                         'elastane' in line_text.lower() or 'stretch' in line_text.lower() or
                                         'gold' in line_text.lower() or 'cashmere' in line_text.lower() or
                                         'kevlar' in line_text.lower()):
                    if not result['material']:
                        result['material'] = line_text
        
        return result
    
    def _extract_status_and_prices(self, soup: BeautifulSoup, skip_onsale_second_pass: bool = False) -> Dict[str, str]:
        """
        Extract status and prices together.
        When skip_onsale_second_pass=True (regular_safe fallback), a single price
        is always treated as regular; no second-pass search for compare-at-price.
        """
        result = {
            'status': 'regular',
            'regular_price': '',
            'sales_price': ''
        }
        
        # Strategy: Find the main product price area (not variant selectors)
        # Look for price container in the main product info area
        main_price_container = None
        
        # Try to find main product price container
        price_container_selectors = [
            'div.product-price',
            'div.price',
            'span.price',
            'div[class*="product"][class*="price"]',
            'div[class*="price-container"]'
        ]
        
        for selector in price_container_selectors:
            containers = soup.select(selector)
            for container in containers:
                # Check if container is in the main product area (not in variant selectors or related products)
                # Avoid variant selectors
                if container.find_parent(['select', 'option']):
                    continue
                # Check if it's in the main product area
                product_area = container.find_parent(['main', 'article', 'div'], class_=re.compile(r'product', re.I))
                if product_area:
                    # Make sure it's not in a variant selector
                    variant_parent = container.find_parent(['select', 'div'], {'data-variant': True})
                    if not variant_parent:
                        main_price_container = container
                        break
            if main_price_container:
                break
        
        # Extract prices from main container if found
        regular_price = None
        sale_price = None
        sale_block_root = None  # Restrict second-pass to this block to avoid unrelated prices
        
        if main_price_container:
            # Look for compare-at-price and sale-price in this container
            compare_elem = main_price_container.find('compare-at-price') or main_price_container.find(class_=re.compile(r'compare-at-price|old-price|original-price', re.I))
            sale_elem = main_price_container.find('sale-price') or main_price_container.find(class_=re.compile(r'sale-price|current-price', re.I))
            
            # Only use compare-at-price if it's actually crossed out (on sale)
            if compare_elem:
                # Verify it's crossed out
                compare_classes = ' '.join(compare_elem.get('class', []))
                compare_style = compare_elem.get('style', '')
                children_with_line_through = compare_elem.find_all(class_=re.compile(r'line-through', re.I))
                is_crossed_out = (
                    'line-through' in compare_classes.lower() or
                    'line-through' in compare_style.lower() or
                    len(children_with_line_through) > 0
                )
                if is_crossed_out:
                    text = compare_elem.get_text()
                    price_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
                    if price_match:
                        regular_price = price_match.group(1)
            
            if sale_elem:
                text = sale_elem.get_text()
                price_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
                if price_match:
                    sale_price = price_match.group(1)
                    # Same-block root: container or its parent (compare-at may be sibling of container)
                    sale_block_root = main_price_container.parent if main_price_container.parent else main_price_container
        else:
            # Fallback: Find prices in product area, but be very careful about matching
            # The issue: We might find compare-at-price from related products or hidden elements
            product_area = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'product', re.I))
            if product_area:
                # Find all price tags, but filter carefully
                compare_tags = product_area.find_all('compare-at-price')
                sale_tags = product_area.find_all('sale-price')
                
                # Helper function to check if element is visible (not hidden)
                def is_visible(elem):
                    """Check if element is likely visible (not hidden by CSS)"""
                    style = elem.get('style', '')
                    classes = ' '.join(elem.get('class', []))
                    # Check for common hiding patterns
                    if 'display: none' in style or 'display:none' in style:
                        return False
                    if 'visibility: hidden' in style or 'visibility:hidden' in style:
                        return False
                    if 'hidden' in classes.lower():
                        return False
                    # Check parent visibility
                    parent = elem.parent
                    depth = 0
                    while parent and depth < 3:
                        parent_style = parent.get('style', '')
                        parent_classes = ' '.join(parent.get('class', []))
                        if 'display: none' in parent_style or 'display:none' in parent_style:
                            return False
                        if 'hidden' in parent_classes.lower():
                            return False
                        parent = parent.parent
                        depth += 1
                    return True
                
                # Helper function to check if element is in main product price area (not related products)
                def is_in_main_price_area(elem):
                    """Check if element is in the main product price display, not related products"""
                    # Exclude variant selectors
                    if elem.find_parent(['select', 'option']):
                        return False
                    # Exclude related products sections
                    parent = elem.parent
                    depth = 0
                    while parent and depth < 5:
                        parent_classes = ' '.join(parent.get('class', []))
                        parent_id = parent.get('id', '')
                        # Check for related products indicators
                        if any(keyword in parent_classes.lower() or keyword in parent_id.lower() 
                               for keyword in ['related', 'recommended', 'you-may-also', 'similar', 'upsell']):
                            return False
                        # Check if we're in a product card/list (likely related products)
                        if parent.name in ['li', 'article'] and 'product' in parent_classes.lower():
                            # Make sure it's the main product, not a product card
                            if 'card' in parent_classes.lower() or 'item' in parent_classes.lower():
                                return False
                        parent = parent.parent
                        depth += 1
                    return True
                
                # Strategy: Find sale-price first (this is the actual displayed price)
                # Then look for compare-at-price ONLY if it's:
                # 1. Visible (not hidden)
                # 2. In main price area (not related products)
                # 3. Actually crossed out
                # 4. In the same immediate container as the sale-price
                found_pair = False
                
                # First, find the main sale-price (the actual product price)
                main_sale_price = None
                main_sale_elem = None
                for sale_tag in sale_tags:
                    if (is_in_main_price_area(sale_tag) and is_visible(sale_tag) and 
                        not sale_tag.find_parent(['select', 'option'])):
                        text = sale_tag.get_text()
                        price_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
                        if price_match:
                            main_sale_price = price_match.group(1)
                            main_sale_elem = sale_tag
                            break
                
                # If we found a sale-price, look for compare-at-price (tag or class) ONLY in the same immediate container
                if main_sale_elem:
                    # Check direct siblings first (tag or class-based compare-at)
                    if main_sale_elem.parent:
                        compare_sibling = (
                            main_sale_elem.find_previous_sibling('compare-at-price')
                            or main_sale_elem.find_previous_sibling(class_=re.compile(r'compare-at-price|old-price|original-price', re.I))
                        )
                        if not compare_sibling:
                            compare_sibling = (
                                main_sale_elem.find_next_sibling('compare-at-price')
                                or main_sale_elem.find_next_sibling(class_=re.compile(r'compare-at-price|old-price|original-price', re.I))
                            )
                        if compare_sibling and is_visible(compare_sibling) and is_in_main_price_area(compare_sibling):
                            # Verify it's crossed out
                            compare_classes = ' '.join(compare_sibling.get('class', []))
                            compare_style = compare_sibling.get('style', '')
                            children_with_line_through = compare_sibling.find_all(class_=re.compile(r'line-through', re.I))
                            is_crossed_out = (
                                'line-through' in compare_classes.lower() or
                                'line-through' in compare_style.lower() or
                                len(children_with_line_through) > 0
                            )
                            if is_crossed_out:
                                compare_text = compare_sibling.get_text()
                                compare_match = re.search(r'\$(\d+(?:\.\d+)?)', compare_text)
                                if compare_match:
                                    regular_price = compare_match.group(1)
                                    sale_price = main_sale_price
                                    found_pair = True
                    
                    # If not siblings, check same immediate parent container (tag or class-based compare-at)
                    if not found_pair and main_sale_elem.parent:
                        parent = main_sale_elem.parent
                        compare_in_parent = parent.find('compare-at-price') or parent.find(class_=re.compile(r'compare-at-price|old-price|original-price', re.I))
                        if (compare_in_parent and is_visible(compare_in_parent) and 
                            is_in_main_price_area(compare_in_parent)):
                            # Verify it's crossed out
                            compare_classes = ' '.join(compare_in_parent.get('class', []))
                            compare_style = compare_in_parent.get('style', '')
                            children_with_line_through = compare_in_parent.find_all(class_=re.compile(r'line-through', re.I))
                            is_crossed_out = (
                                'line-through' in compare_classes.lower() or
                                'line-through' in compare_style.lower() or
                                len(children_with_line_through) > 0
                            )
                            if is_crossed_out:
                                compare_text = compare_in_parent.get_text()
                                compare_match = re.search(r'\$(\d+(?:\.\d+)?)', compare_text)
                                if compare_match:
                                    regular_price = compare_match.group(1)
                                    sale_price = main_sale_price
                                    found_pair = True
                
                # If no pair found, use sale-price as regular price (single price = regular)
                if not found_pair and main_sale_price:
                    sale_price = main_sale_price
                    # Same-block root: ancestor of sale element (so second pass only sees this product's price block)
                    if main_sale_elem:
                        node = main_sale_elem
                        for _ in range(6):
                            if node and node.parent:
                                node = node.parent
                            else:
                                break
                        sale_block_root = node
        
        # Apply result: both prices found in same container = definitive
        if regular_price and sale_price:
            try:
                if float(sale_price) < float(regular_price):
                    result['status'] = 'on-sales'
                    result['regular_price'] = regular_price
                    result['sales_price'] = sale_price
                else:
                    result['status'] = 'regular'
                    result['regular_price'] = str(min(float(regular_price), float(sale_price)))
                    result['sales_price'] = ''
            except ValueError:
                result['status'] = 'regular'
                result['regular_price'] = sale_price if sale_price else regular_price
                result['sales_price'] = ''
            return result
        
        # Only sale_price found: may be regular OR on-sale (compare-at-price not in same container)
        # Second pass (unless skip_onsale_second_pass): search only in same price block for compare-at-price
        if sale_price:
            if skip_onsale_second_pass:
                result['status'] = 'regular'
                result['regular_price'] = sale_price
                result['sales_price'] = ''
                return result
            # Restrict to same block as displayed price to avoid picking up unrelated (e.g. related-product) prices
            search_root = sale_block_root if sale_block_root else (soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'product', re.I)))
            if search_root:
                def _not_in_related(elem):
                    p = elem.parent
                    depth = 0
                    while p and depth < 6:
                        c = ' '.join(p.get('class', [])).lower()
                        i = (p.get('id') or '').lower()
                        if any(k in c or k in i for k in ['related', 'recommended', 'you-may-also', 'similar', 'upsell', 'cart']):
                            return False
                        if p.name in ['li', 'article'] and 'product' in c and ('card' in c or 'item' in c):
                            return False
                        p = p.parent
                        depth += 1
                    return True
                try:
                    sale_val = float(sale_price)
                    # Include both tag and class-based compare-at (e.g. <compare-at-price> or span.compare-at-price)
                    compare_elems = list(search_root.find_all('compare-at-price'))
                    compare_elems.extend(search_root.find_all(class_=re.compile(r'compare-at-price|old-price|original-price', re.I)))
                    seen_ids = set()
                    for compare_elem in compare_elems:
                        if id(compare_elem) in seen_ids:
                            continue
                        seen_ids.add(id(compare_elem))
                        if compare_elem.find_parent(['select', 'option']):
                            continue
                        if not _not_in_related(compare_elem):
                            continue
                        txt = compare_elem.get_text()
                        m = re.search(r'\$(\d+(?:\.\d+)?)', txt)
                        if m:
                            compare_val = float(m.group(1))
                            if compare_val > sale_val:
                                result['status'] = 'on-sales'
                                result['regular_price'] = m.group(1)
                                result['sales_price'] = sale_price
                                return result
                except ValueError:
                    pass
                # Numeric fallback: site may not use compare-at tag/class (e.g. two spans in one block).
                # Scan price-related elements in the same block for any dollar amount > sale price.
                try:
                    sale_val = float(sale_price)
                    price_elems = search_root.find_all(class_=re.compile(r'price', re.I))
                    if not price_elems:
                        price_elems = [search_root]
                    higher_amounts = []
                    for elem in price_elems:
                        if not _not_in_related(elem):
                            continue
                        txt = elem.get_text()
                        for m in re.finditer(r'\$(\d+(?:\.\d+)?)', txt):
                            try:
                                val = float(m.group(1))
                                # Must be higher than sale and plausibly a product price (not shipping e.g. 5, 10, 25)
                                if val > sale_val and val >= 50:
                                    higher_amounts.append((val, m.group(1)))
                            except ValueError:
                                pass
                    if higher_amounts:
                        # Use smallest value higher than sale (likely the compare-at; avoids unrelated higher prices)
                        best = min(higher_amounts, key=lambda x: x[0])
                        result['status'] = 'on-sales'
                        result['regular_price'] = best[1]
                        result['sales_price'] = sale_price
                        return result
                except (ValueError, TypeError):
                    pass
            # No compare-at found with higher price -> treat as regular (preserve current behavior)
            result['status'] = 'regular'
            result['regular_price'] = sale_price
            result['sales_price'] = ''
            return result
        
        if regular_price:
            result['status'] = 'regular'
            result['regular_price'] = regular_price
            result['sales_price'] = ''
            return result
        
        result['status'] = self._extract_status(soup)
        return result
    
    def _extract_status_and_prices_regular_safe(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        FALLBACK: Single price is always treated as regular (no second-pass on-sale detection).
        Use when we want to preserve the previous behavior: only mark on-sales when both
        prices were found in the same container.
        """
        return self._extract_status_and_prices(soup, skip_onsale_second_pass=True)
    
    def _extract_denim_weight_oz(self, soup: BeautifulSoup) -> str:
        """
        Extract denim weight - only numeric value (e.g., '13.5' not '13.5oz')
        Leave blank for non-jeans products
        """
        weight_patterns = [
            r'(\d+(?:\.\d+)?)oz\s+Japanese\s+Selvedge\s+Denim',
            r'(\d+(?:\.\d+)?)oz\s+selvedge\s+denim',
            r'(\d+(?:\.\d+)?)oz\s+denim',
            r'(\d+(?:\.\d+)?)oz'
        ]
        
        page_text = soup.get_text()
        for pattern in weight_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                # Return only the numeric value
                return match.group(1)
        
        return ''
    
    def _extract_denim_category(self, soup: BeautifulSoup) -> str:
        """Extract denim category"""
        list_items = soup.find_all('li')
        for li in list_items:
            text = li.get_text(strip=True)
            if 'oz' in text and ('selvedge' in text.lower() or 'denim' in text.lower()):
                return text
        
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
        """Extract the main product description text, excluding labelcard table"""
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
                # Exclude labelcard table from description
                # Remove any labelcard elements before extracting text
                labelcard = elem.find('ul', class_=re.compile(r'labelcard', re.I))
                if labelcard:
                    labelcard.decompose()  # Remove labelcard from the element
                
                desc_text = elem.get_text(strip=True)
                if desc_text and len(desc_text) > 50:
                    # Additional cleanup: remove any remaining labelcard-like patterns
                    # Remove lines that look like labelcard entries (e.g., "STYLE / FIT—Easy Guy")
                    lines = desc_text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        # Skip lines that look like labelcard entries
                        if re.match(r'^[A-Z\s/]+—', line):  # Pattern like "STYLE / FIT—"
                            continue
                        if re.match(r'^\d+\.?\d*oz', line, re.I):  # Pattern like "13.75oz"
                            continue
                        if re.match(r'^\d+%', line):  # Pattern like "100% Cotton"
                            continue
                        if 'Made in' in line and len(line) < 30:  # Short "Made in" lines
                            continue
                        if re.match(r'^SKU', line, re.I):  # Pattern like "SKU—101132706"
                            continue
                        if line:
                            cleaned_lines.append(line)
                    
                    cleaned_text = ' '.join(cleaned_lines)
                    # Remove any trailing labelcard-like text
                    cleaned_text = re.sub(r'\s*[A-Z\s/]+—[A-Za-z\s]+$', '', cleaned_text)
                    cleaned_text = re.sub(r'\s*\d+\.?\d*oz\s+[A-Za-z\s]+$', '', cleaned_text, flags=re.I)
                    cleaned_text = re.sub(r'\s*\d+%\s+[A-Za-z\s]+$', '', cleaned_text)
                    cleaned_text = re.sub(r'\s*Made in\s+[A-Za-z]+$', '', cleaned_text, flags=re.I)
                    cleaned_text = re.sub(r'\s*SKU[—\-]\s*[A-Z0-9]+$', '', cleaned_text, flags=re.I)
                    
                    if cleaned_text and len(cleaned_text) > 50:
                        return cleaned_text
        
        return ''
    
    def _extract_made_in(self, soup: BeautifulSoup) -> str:
        """Extract 'Made in' information"""
        list_items = soup.find_all('li')
        for li in list_items:
            li_text = li.get_text().strip()
            if 'Made in' in li_text:
                match = re.search(r'Made in\s+([A-Za-z\s]+)', li_text, re.IGNORECASE)
                if match:
                    country = match.group(1).strip()
                    country = re.sub(r'\s+', ' ', country)
                    return f"Made in {country}"
        
        # Fallback: search in all text
        page_text = soup.get_text()
        match = re.search(r'Made in\s+([A-Za-z\s]+)', page_text, re.IGNORECASE)
        if match:
            country = match.group(1).strip()
            country = re.sub(r'\s+', ' ', country)
            country = country.split('\n')[0]
            if len(country) < 50:
                return f"Made in {country}"
        
        return ''
    
    def _open_size_chart_and_return_soup(self, driver):
        """
        Click 'SIZE CHART' on product page, wait for modal, return page soup for parsing.
        Used with with_selenium_driver(url, self._open_size_chart_and_return_soup).
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        wait = WebDriverWait(driver, 15)
        clicked = False
        # Try link text first (user said "clickable text SIZE CHART")
        for selector in [
            (By.LINK_TEXT, "SIZE CHART"),
            (By.PARTIAL_LINK_TEXT, "SIZE CHART"),
            (By.XPATH, "//a[contains(normalize-space(), 'SIZE CHART')]"),
            (By.XPATH, "//*[contains(text(), 'SIZE CHART') and (self::a or self::button)]"),
        ]:
            try:
                elem = wait.until(EC.element_to_be_clickable(selector))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", elem)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            self.logger.warning("Could not find or click 'SIZE CHART' link")
            return BeautifulSoup(driver.page_source, "html.parser")
        time.sleep(2)
        # Wait for modal table (e.g. row with WAIST or FRONT RISE)
        try:
            wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//*[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'WAIST') or contains(text(), 'Front Rise') or contains(text(), 'FRONT RISE')]"
            )))
        except Exception:
            pass
        time.sleep(1)
        return BeautifulSoup(driver.page_source, "html.parser")
    
    def _parse_nf_size_chart_table(
        self, soup: BeautifulSoup, nf_product_url: str, product_id: str
    ) -> List[Dict]:
        """
        Parse N+F size chart table from modal. Table has measurement names in first column,
        tag sizes as column headers (or first row). Returns list of dicts: one per tag size.
        """
        # Find table - may be in modal/dialog/overlay
        table = (
            soup.select_one("table") or
            soup.find("table", class_=re.compile(r"size|chart", re.I))
        )
        if not table:
            self.logger.warning("No size chart table found in page")
            return []
        rows = table.find_all("tr")
        if len(rows) < 2:
            return []
        # Assume first row is header: first cell "TAG SIZE", rest are sizes (28, 29, ...)
        header_cells = rows[0].find_all(["th", "td"])
        tag_sizes = []
        for c in header_cells[1:]:
            t = c.get_text(strip=True)
            if t and re.match(r"^\d+$", t):
                tag_sizes.append(t)
        if not tag_sizes:
            # Maybe first column is empty and headers are in first row
            for c in header_cells:
                t = c.get_text(strip=True)
                if re.match(r"^\d+$", t):
                    tag_sizes.append(t)
        if not tag_sizes:
            self.logger.warning("Could not find tag size headers in size chart table")
            return []
        # Map measurement name (row) -> list of values per column
        measurement_map = {}  # e.g. "waist" -> [v0, v1, ...] by column index
        measurement_row_names = [
            "waist", "front_rise", "back_rise", "upper_thigh", "knee", "leg_opening", "inseam"
        ]
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            if not cells:
                continue
            name_cell = (cells[0].get_text(strip=True) or "").lower().replace(" ", "_").replace("-", "_")
            # Normalize to our schema names
            if "waist" in name_cell and name_cell.strip() in ("waist", "waists"):
                key = "waist"
            elif "front_rise" in name_cell or "frontrise" in name_cell:
                key = "front_rise"
            elif "back_rise" in name_cell or "backrise" in name_cell:
                key = "back_rise"
            elif "upper_thigh" in name_cell or "thigh" in name_cell:
                key = "upper_thigh"
            elif "knee" in name_cell:
                key = "knee"
            elif "leg_opening" in name_cell or "leg_opening" in name_cell:
                key = "leg_opening"
            elif "inseam" in name_cell:
                key = "inseam"
            else:
                continue
            values = []
            for cell in cells[1:]:
                val = self.extract_number(cell.get_text(strip=True))
                values.append(val)
            measurement_map[key] = values
        # Build one record per tag size
        def _val(key: str, i: int):
            vals = measurement_map.get(key) or []
            return vals[i] if i < len(vals) else None

        result = []
        for i, tag in enumerate(tag_sizes):
            entry = {
                "product_id": product_id,
                "nf_product_url": nf_product_url,
                "tag_size": tag,
                "waist": _val("waist", i),
                "front_rise": _val("front_rise", i),
                "back_rise": _val("back_rise", i),
                "upper_thigh": _val("upper_thigh", i),
                "knee": _val("knee", i),
                "leg_opening": _val("leg_opening", i),
                "inseam": _val("inseam", i),
            }
            result.append(entry)
        return result
    
    def scrape_size_chart_for_product(self, url: str, product_id: str) -> List[Dict]:
        """
        Load product page, click SIZE CHART, parse modal table. Returns list of measurement
        rows (one per tag size) with keys: product_id, nf_product_url, tag_size, waist,
        front_rise, back_rise, upper_thigh, knee, leg_opening, inseam. Caller adds
        measurement_source and scraped_at.
        """
        def _callback(driver):
            soup = self._open_size_chart_and_return_soup(driver)
            return self._parse_nf_size_chart_table(soup, url, product_id)
        rows = self.with_selenium_driver(url, _callback)
        if not rows:
            return []
        return rows if isinstance(rows, list) else []
    
    def save_to_csv(self, data: List[Dict], filename: str = "naked_famous_products.csv"):
        """Save scraped data to CSV following the schema"""
        os.makedirs('data/processed', exist_ok=True)
        filepath = f'data/processed/{filename}'
        
        # Define required columns with new field order
        required_columns = [
            'product_id', 'sku',  # SKU moved next to product_id
            'product_name', 'fit_id', 'fabric_id', 'wash_state',
            'gender', 'default_inseam_label', 'colorway', 
            'status', 'regular_price', 'sales_price',  # Prices next to status
            'nf_product_url', 'description_html',
            'release_season', 'run_code', 'notes',
            'denim_weight_oz', 'denim_cat', 'material', 'made_in',  # Material next to denim_cat
            'product_description',
            'collections',  # Collection labels
            'is_jeans',  # Label indicating jeans vs non-jeans
            'scraped_at'  # Timestamp when product was scraped
        ]
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(required_columns)  # Write header
            
            for item in data:
                row = []
                for col in required_columns:
                    value = item.get(col, '')
                    if isinstance(value, str):
                        # Clean the value
                        value = re.sub(r'<script.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
                        value = value.strip()
                    else:
                        value = str(value) if value is not None else ''
                    row.append(value)
                writer.writerow(row)
        
        self.logger.info(f"Saved {len(data)} products to {filepath}")
        return filepath
    
    def scrape_all(self) -> List[Dict]:
        """
        Main method to scrape all products from all collections
        Deduplicates products while preserving collection labels
        """
        self.logger.info(f"Starting to scrape {self.brand_name}")
        
        # Get all product URLs from all collections
        collection_urls = self.get_all_product_urls()
        
        # Collect all unique product URLs
        all_product_urls = set()
        for urls in collection_urls.values():
            all_product_urls.update(urls)
        
        self.logger.info(f"Found {len(all_product_urls)} unique product URLs across all collections")
        
        # Scrape each product
        products = []
        for i, url in enumerate(all_product_urls, 1):
            self.logger.info(f"Scraping product {i}/{len(all_product_urls)}: {url}")
            product_data = self.scrape_product(url)
            if product_data:
                products.append(product_data)
            time.sleep(2)  # Be respectful
        
        # Save to CSV with timestamp to preserve old data
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.save_to_csv(products, f"naked_famous_products_{timestamp}.csv")
        
        # Also save to JSON for backup
        self.save_to_json(products, f"naked_famous_products_{timestamp}.json")
        
        # Also save as latest version (best-effort; timestamped files above are authoritative)
        try:
            self.save_to_csv(products, "naked_famous_products_latest.csv")
            self.save_to_json(products, "naked_famous_products_latest.json")
        except OSError as e:
            self.logger.warning(f"Could not save latest files (timestamped saves succeeded): {e}")
        
        self.logger.info(f"Scraping completed. Found {len(products)} products.")
        return products

