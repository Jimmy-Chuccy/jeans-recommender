from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin

class NakedFamousScraper(BaseScraper):
    def __init__(self):
        super().__init__("Naked & Famous", "https://www.nakedandfamousdenim.com")
        
    def get_product_urls(self) -> List[str]:
        """Get all product URLs from Naked & Famous website"""
        urls = []
        
        # Try different category pages
        category_urls = [
            "https://www.nakedandfamousdenim.com/collections/mens-jeans",
            "https://www.nakedandfamousdenim.com/collections/womens-jeans",
            "https://www.nakedandfamousdenim.com/collections/jeans"
        ]
        
        for category_url in category_urls:
            soup = self.get_page(category_url)
            if soup:
                # Look for product links
                product_links = soup.find_all('a', href=re.compile(r'/products/'))
                for link in product_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in urls:
                            urls.append(full_url)
                            
        self.logger.info(f"Found {len(urls)} product URLs")
        return urls
        
    def scrape_product(self, url: str) -> Optional[Dict]:
        """Scrape individual Naked & Famous product"""
        soup = self.get_page(url)
        if not soup:
            return None
            
        try:
            product_data = {
                'brand': 'Naked & Famous',
                'product_url': url,
                'scraped_from': 'nakedandfamousdenim.com'
            }
            
            # Product name
            title_elem = soup.find('h1', class_='product-title') or soup.find('h1')
            product_data['name'] = self.extract_text(title_elem)
            
            # Price
            price_elem = soup.find('span', class_='price') or soup.find('div', class_='price')
            if price_elem:
                price_text = self.extract_text(price_elem)
                product_data['price'] = self.extract_number(price_text.replace('$', '').replace(',', ''))
            
            # Description
            desc_elem = soup.find('div', class_='product-description') or soup.find('div', class_='description')
            product_data['description'] = self.extract_text(desc_elem)
            
            # Images
            images = []
            img_elements = soup.find_all('img', src=re.compile(r'products'))
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(urljoin(self.base_url, src))
            product_data['image_urls'] = images
            
            # Extract fit information from description
            description = product_data.get('description', '').lower()
            if 'skinny' in description:
                product_data['fit'] = 'skinny'
            elif 'slim' in description:
                product_data['fit'] = 'slim'
            elif 'relaxed' in description:
                product_data['fit'] = 'relaxed'
            elif 'straight' in description:
                product_data['fit'] = 'straight'
            elif 'tapered' in description:
                product_data['fit'] = 'tapered'
            
            # Extract fabric weight
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*oz', description)
            if weight_match:
                product_data['fabric_weight'] = weight_match.group(1) + ' oz'
            
            # Check for selvedge
            if 'selvedge' in description:
                product_data['selvedge'] = True
            
            # Check for stretch
            if 'stretch' in description:
                product_data['stretch'] = True
            
            # Determine gender from URL or description
            if '/mens' in url or 'men' in description:
                product_data['gender'] = 'mens'
            elif '/womens' in url or 'women' in description:
                product_data['gender'] = 'womens'
            else:
                product_data['gender'] = 'mens'  # Default assumption
            
            # Try to get size information
            size_elements = soup.find_all('option', value=re.compile(r'\d+'))
            sizes = []
            for size_elem in size_elements:
                size_text = self.extract_text(size_elem)
                if size_text and size_text.isdigit():
                    sizes.append(size_text)
            product_data['sizes_available'] = sizes
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {url}: {str(e)}")
            return None
