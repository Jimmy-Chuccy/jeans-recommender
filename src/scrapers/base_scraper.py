import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

class BaseScraper:
    def __init__(self, brand_name: str, base_url: str):
        self.brand_name = brand_name
        self.base_url = base_url
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_session()
        self.setup_logging()
        
    def setup_session(self):
        """Setup requests session with headers"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def setup_logging(self):
        """Setup logging for the scraper"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - {self.brand_name} - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.brand_name)
        
    def get_page(self, url: str, use_selenium: bool = False) -> Optional[BeautifulSoup]:
        """Get page content using requests or selenium"""
        try:
            if use_selenium:
                return self.get_page_selenium(url)
            else:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    def get_page_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content using selenium for JS-heavy sites"""
        import os
        import platform
        import subprocess
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--user-agent={self.ua.random}')
            
            # Get chromedriver path (may return dir, zip, or executable path)
            driver_path = ChromeDriverManager().install()
            if not driver_path:
                raise RuntimeError("ChromeDriverManager().install() returned None")
            
            # Resolve to the actual chromedriver executable (webdriver_manager can return dir, .zip, or executable)
            if driver_path.endswith('.zip'):
                base_dir = os.path.dirname(driver_path)
                candidates = [
                    os.path.join(base_dir, 'chromedriver-mac-arm64', 'chromedriver'),
                    os.path.join(base_dir, 'chromedriver'),
                ]
                # If zip wasn't extracted, extract it so we can use the binary
                found = None
                for path in candidates:
                    if os.path.isfile(path):
                        found = path
                        break
                if not found and os.path.isfile(driver_path):
                    try:
                        import zipfile
                        with zipfile.ZipFile(driver_path, 'r') as z:
                            z.extractall(base_dir)
                        for path in candidates:
                            if os.path.isfile(path):
                                found = path
                                break
                    except Exception:
                        pass
                if found:
                    driver_path = found
                else:
                    driver_path = os.path.join(base_dir, 'chromedriver')  # will fail below if missing
            elif os.path.isdir(driver_path):
                base_dir = driver_path
                candidates = [
                    os.path.join(base_dir, 'chromedriver'),
                    os.path.join(base_dir, 'chromedriver-mac-arm64', 'chromedriver'),
                ]
                # Also search one level down (e.g. mac64/144.x.x/chromedriver)
                try:
                    for name in os.listdir(base_dir):
                        sub = os.path.join(base_dir, name)
                        if os.path.isdir(sub):
                            candidates.append(os.path.join(sub, 'chromedriver'))
                except OSError:
                    pass
            else:
                base_dir = os.path.dirname(driver_path)
                # If install() returned a file that isn't the binary (e.g. LICENSE), use same dir
                if os.path.basename(driver_path) != 'chromedriver':
                    candidates = [os.path.join(base_dir, 'chromedriver')]
                else:
                    candidates = [driver_path]
            
            driver_path = None
            for path in candidates:
                if os.path.isfile(path):
                    driver_path = path
                    break
            if not driver_path:
                raise RuntimeError("Could not find chromedriver executable in cache (tried %s)" % candidates[:5])
            
            # On macOS: remove quarantine and ensure executable (fixes [Errno 1] Operation not permitted)
            if platform.system() == 'Darwin':
                try:
                    for target in [driver_path, os.path.dirname(driver_path), os.path.dirname(os.path.dirname(driver_path))]:
                        if target and os.path.exists(target):
                            subprocess.run(['xattr', '-d', 'com.apple.quarantine', target], capture_output=True, check=False)
                    if os.path.isfile(driver_path):
                        os.chmod(driver_path, 0o755)
                except Exception:
                    pass
            
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get(url)
            # Wait longer for JS-heavy sites
            time.sleep(5)  # Wait for JS to load
            
            # Try to wait for specific elements if possible
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                # Wait for page to be ready
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass  # Continue even if wait fails
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            
            return soup
        except Exception as e:
            self.logger.error(f"Selenium error for {url}: {str(e)}")
            return None

    def with_selenium_driver(self, url: str, callback):
        """
        Create a Selenium driver, load url, run callback(driver), then quit.
        Returns whatever callback(driver) returns. Use for multi-step flows (e.g. click, wait, then parse).
        """
        import os
        import platform
        import subprocess
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--user-agent={self.ua.random}')
            driver_path = ChromeDriverManager().install()
            if not driver_path:
                raise RuntimeError("ChromeDriverManager().install() returned None")
            if driver_path.endswith('.zip'):
                base_dir = os.path.dirname(driver_path)
                candidates = [
                    os.path.join(base_dir, 'chromedriver-mac-arm64', 'chromedriver'),
                    os.path.join(base_dir, 'chromedriver'),
                ]
                found = None
                for path in candidates:
                    if os.path.isfile(path):
                        found = path
                        break
                if not found and os.path.isfile(driver_path):
                    try:
                        import zipfile
                        with zipfile.ZipFile(driver_path, 'r') as z:
                            z.extractall(base_dir)
                        for path in candidates:
                            if os.path.isfile(path):
                                found = path
                                break
                    except Exception:
                        pass
                driver_path = found or os.path.join(base_dir, 'chromedriver')
            elif os.path.isdir(driver_path):
                base_dir = driver_path
                candidates = [
                    os.path.join(base_dir, 'chromedriver'),
                    os.path.join(base_dir, 'chromedriver-mac-arm64', 'chromedriver'),
                ]
                try:
                    for name in os.listdir(base_dir):
                        sub = os.path.join(base_dir, name)
                        if os.path.isdir(sub):
                            candidates.append(os.path.join(sub, 'chromedriver'))
                except OSError:
                    pass
                driver_path = None
                for path in candidates:
                    if os.path.isfile(path):
                        driver_path = path
                        break
                driver_path = driver_path or os.path.join(base_dir, 'chromedriver')
            else:
                base_dir = os.path.dirname(driver_path)
                driver_path = driver_path if (os.path.basename(driver_path) == 'chromedriver' and os.path.isfile(driver_path)) else os.path.join(base_dir, 'chromedriver')
            if not os.path.isfile(driver_path):
                raise RuntimeError("Could not find chromedriver executable")
            if platform.system() == 'Darwin':
                try:
                    for target in [driver_path, os.path.dirname(driver_path)]:
                        if target and os.path.exists(target):
                            subprocess.run(['xattr', '-d', 'com.apple.quarantine', target], capture_output=True, check=False)
                    if os.path.isfile(driver_path):
                        os.chmod(driver_path, 0o755)
                except Exception:
                    pass
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(url)
            time.sleep(5)
            try:
                return callback(driver)
            finally:
                driver.quit()
        except Exception as e:
            self.logger.error(f"Selenium session error for {url}: {str(e)}")
            return None

    def extract_text(self, element, default: str = "") -> str:
        """Safely extract text from BeautifulSoup element"""
        if element:
            return element.get_text(strip=True)
        return default
        
    def extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        import re
        if not text:
            return None
        numbers = re.findall(r'[\d.]+', text)
        return float(numbers[0]) if numbers else None
        
    def normalize_size(self, size: str) -> str:
        """Normalize size format"""
        if not size:
            return ""
        return size.strip().upper()
        
    def save_to_json(self, data: List[Dict], filename: str):
        """Save scraped data to JSON file"""
        import os
        os.makedirs('data/raw', exist_ok=True)
        filepath = f'data/raw/{filename}'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Saved {len(data)} items to {filepath}")
        
    def get_product_urls(self) -> List[str]:
        """Override in subclasses to get product URLs"""
        raise NotImplementedError
        
    def scrape_product(self, url: str) -> Optional[Dict]:
        """Override in subclasses to scrape individual product"""
        raise NotImplementedError
        
    def scrape_all(self) -> List[Dict]:
        """Main method to scrape all products"""
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
            
        self.save_to_json(products, f"{self.brand_name.lower().replace(' ', '_')}_products.json")
        return products
