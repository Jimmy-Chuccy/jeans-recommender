"""
Scraper for Nudie Jeans (nudiejeans.com).
Men's jeans only; discovers products by fit from config; extracts details from product page + Details slide-out panel.
"""

from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import re
from urllib.parse import urljoin
import os
from datetime import datetime
import time
import csv
import yaml


def _load_scraper_config() -> Dict[str, Any]:
    """Load config from config/scrapers.yaml (project root)."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base, "config", "scrapers.yaml")
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class NudieJeansScraper(BaseScraper):
    """Scraper for Nudie Jeans; uses fit-based discovery and Details panel for specs."""

    def __init__(self):
        cfg = _load_scraper_config().get("nudie_jeans", {})
        base_url = cfg.get("base_url", "https://www.nudiejeans.com")
        locale = cfg.get("locale_path", "/en-CA")
        self.base_url_with_locale = base_url.rstrip("/") + locale
        super().__init__("Nudie Jeans", base_url)
        self._config = cfg
        self._currency = cfg.get("currency", "CAD")
        fits = cfg.get("mens_fits", [])
        self._fit_slugs = [f["slug"] for f in fits]
        self._fit_names = [f["name"] for f in fits]
        self._fit_name_to_slug = {f["name"]: f["slug"] for f in fits}

    def get_product_urls(self) -> List[str]:
        """Collect all product URLs by iterating over each men's fit selection page."""
        seen: set = set()
        for slug in self._fit_slugs:
            url = f"{self.base_url_with_locale}/selection/{slug}"
            self.logger.info(f"Fit selection: {url}")
            soup = self.get_page(url, use_selenium=True)
            if not soup:
                continue
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if "/product/" not in href:
                    continue
                full = urljoin(self.base_url_with_locale, href) if href.startswith("/") else urljoin(self.base_url, href)
                full = full.split("?")[0].split("#")[0]
                if full not in seen:
                    seen.add(full)
            time.sleep(2)
        return list(seen)

    def _open_details_and_return_soup(self, driver) -> Optional[BeautifulSoup]:
        """Click 'Details' button (or link) and wait for panel. Nudie uses a <button>, not <a>."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        wait = WebDriverWait(driver, 15)
        clicked = False
        # Strategy 1: Button with text "Details" (Nudie product page uses <button>, class ProductMainInfo_detailsButton_*)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//main//button[normalize-space()='Details']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            clicked = True
        except Exception:
            pass
        # Strategy 2: Any button with exact text "Details"
        if not clicked:
            try:
                btn = driver.find_element(By.XPATH, "//button[normalize-space()='Details']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
            except Exception:
                pass
        # Strategy 3: CSS class contains detailsButton (e.g. ProductMainInfo_detailsButton_wWqu4)
        if not clicked:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button[class*='detailsButton']")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
            except Exception:
                pass
        # Strategy 4: Link "Details" (fallback)
        if not clicked:
            try:
                link = driver.find_element(By.LINK_TEXT, "Details")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", link)
                clicked = True
            except Exception:
                pass
        if not clicked:
            self.logger.warning("Could not find or click 'Details' button/link")
        else:
            time.sleep(2)
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Made in') or contains(text(),'Organic cotton') or contains(text(),'organic cotton')]")))
            except Exception as e:
                self.logger.warning(f"Details panel may not have opened: {e}")
        return BeautifulSoup(driver.page_source, "html.parser")

    def scrape_product(self, url: str) -> Optional[Dict]:
        """Scrape one product: load page, open Details panel, then extract all schema fields."""
        soup = self.with_selenium_driver(url, self._open_details_and_return_soup)
        if not soup:
            return None
        try:
            data = {}
            data["nudie_product_url"] = url
            data["gender"] = "mens"
            data["collections"] = ""
            data["is_jeans"] = "yes"
            data["scraped_at"] = datetime.now().isoformat()
            data["sku"] = ""

            product_name = self._extract_product_name(soup)
            if not product_name:
                self.logger.warning(f"No product name for {url}")
                return None
            data["product_name"] = product_name

            fit_id, fabric_id = self._extract_fit_and_fabric(product_name)
            data["fit_id"] = fit_id
            data["fabric_id"] = fabric_id

            panel = self._get_details_panel_element(soup)
            panel_text = self._get_details_panel_text(panel)
            desc_paragraph, desc_html = self._get_description_from_panel(panel)

            wash_state = self._extract_wash_state(product_name, desc_paragraph)
            data["wash_state"] = wash_state

            data["product_id"] = self._generate_product_id(product_name)

            data["default_inseam_label"] = self._extract_inseam_lengths(soup)
            data["colorway"] = self._extract_colorway(desc_paragraph, product_name)
            data["notes"] = self._extract_notes(soup, product_name, panel_text)

            status, regular, sales = self._extract_status_and_prices(soup)
            data["status"] = status
            data["regular_price"] = regular
            data["sales_price"] = sales

            data["denim_weight_oz"] = self._extract_denim_weight_oz(panel_text)
            data["denim_cat"] = self._extract_denim_cat(panel_text)
            data["material"] = self._extract_material(panel_text)
            data["made_in"] = self._extract_made_in(panel_text)

            data["product_description"] = desc_paragraph
            data["description_html"] = desc_html

            data["release_season"] = ""
            data["run_code"] = ""

            return data
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title = soup.find("title")
        if title:
            t = title.get_text(strip=True)
            if "|" in t:
                return t.split("|")[0].strip()
            return t
        return ""

    def _extract_fit_and_fabric(self, product_name: str) -> tuple:
        """Return (fit_id snake_case, fabric_id snake_case). fabric_id = text after fit name."""
        for name in self._fit_names:
            if product_name.startswith(name):
                rest = product_name[len(name):].strip()
                fit_slug = self._fit_name_to_slug.get(name, name.lower().replace(" ", "_").replace("II", "ii"))
                fit_id = fit_slug.replace("-", "_")
                fabric_id = rest
                if fabric_id:
                    fabric_id = re.sub(r"\s+", " ", fabric_id)
                    fabric_id = fabric_id.lower().replace(" ", "_").replace("&", "and").replace("-", "_")
                    fabric_id = re.sub(r"_+", "_", fabric_id).strip("_")
                else:
                    fabric_id = ""
                return fit_id, fabric_id
        fit_id = product_name.split()[0].lower().replace(" ", "_") if product_name else ""
        return fit_id, ""

    def _get_details_panel_element(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Return the Details slide-out panel element (contains 'Details' and 'Made in' or 'Organic cotton')."""
        if not soup:
            return None
        # Find element that contains "Details" as heading and panel content
        for elem in soup.find_all(string=re.compile(r"^\s*Details\s*$", re.I)):
            parent = elem.parent
            if not parent:
                continue
            # Panel is usually the container of this heading (section, div, aside)
            panel = parent.find_parent(["section", "div", "aside", "nav"])
            if not panel:
                panel = parent
            text = panel.get_text()
            if ("Made in" in text or "Organic cotton" in text or "organic cotton" in text) and "oz." in text:
                return panel
            # Try parent of parent
            panel = parent.find_parent(["section", "div", "aside"])
            if panel:
                text = panel.get_text()
                if ("Made in" in text or "Organic cotton" in text) and "oz." in text:
                    return panel
        # Fallback: find any container that has both "Close" (panel close) and "Made in"
        for tag in soup.find_all(["section", "div"], class_=True):
            text = tag.get_text()
            if "Made in" in text and ("Organic cotton" in text or "oz." in text) and "Close" in text:
                return tag
        return None

    def _get_details_panel_text(self, panel: Optional[BeautifulSoup]) -> str:
        """Bullet-style text from the Details panel only (list items in order). Joined with newline to preserve order."""
        if not panel:
            return ""
        parts = []
        for tag in panel.find_all(["li", "p"]):
            t = tag.get_text(strip=True)
            if t:
                parts.append(t)
        return "\n".join(parts)

    def _get_description_from_panel(self, panel: Optional[BeautifulSoup]) -> tuple:
        """Return (description_plain_text, description_html) from panel. Both from same block."""
        if not panel:
            return "", ""
        # Find "Description" heading: element whose text is exactly "Description"
        for elem in panel.find_all(string=re.compile(r"^\s*Description\s*$", re.I)):
            parent = elem.parent
            if not parent:
                continue
            next_sib = parent.find_next_sibling()
            if next_sib:
                return next_sib.get_text(separator=" ", strip=True), str(next_sib)
            for p in parent.find_all_next("p", limit=5):
                if p.get_text(strip=True):
                    return p.get_text(separator=" ", strip=True), str(p)
            break
        # Fallback: find element that contains only "Description" as text
        for tag in panel.find_all(["h2", "h3", "span", "div"]):
            if re.match(r"^\s*Description\s*$", tag.get_text(strip=True), re.I):
                next_sib = tag.find_next_sibling()
                if next_sib:
                    return next_sib.get_text(separator=" ", strip=True), str(next_sib)
                for p in tag.find_all_next("p", limit=5):
                    if p.get_text(strip=True):
                        return p.get_text(separator=" ", strip=True), str(p)
                break
        return "", ""

    def _extract_wash_state(self, product_name: str, desc_paragraph: str) -> str:
        """Dry in name -> 'dry'; else extract wash phrase(s) from description. Support 'rinsed', 'rinse wash', etc."""
        if "Dry" in product_name:
            return "dry"
        # Explicit "rinse wash" or "rinsed" (no "wash" in phrase)
        if re.search(r"\brinse\s+wash\b", desc_paragraph, re.I):
            return "rinse wash"
        if re.search(r"\brinsed\b", desc_paragraph, re.I):
            return "rinsed"
        wash_phrases = re.findall(r"\b(\w+(?:\s+\w+)*\s+wash)\b", desc_paragraph, re.I)
        cleaned = []
        for w in wash_phrases:
            w = w.strip()
            if "wash" in w.lower() and w not in cleaned:
                cleaned.append(w)
        return ", ".join(cleaned) if cleaned else ""

    def _generate_product_id(self, product_name: str) -> str:
        """Product id = product name words joined by underscore. If same name seen again in this run, append _2, _3, ..."""
        words = re.sub(r"[^\w\s]", " ", product_name).split()
        base = "_".join(w.lower() for w in words if w).strip("_")
        base = re.sub(r"_+", "_", base).strip("_") or "unnamed"
        counter = getattr(self, "_product_id_counter", None)
        if counter is not None:
            count = counter.get(base, 0)
            counter[base] = count + 1
            return base if count == 0 else f"{base}_{count + 1}"
        return base

    def _extract_inseam_lengths(self, soup: BeautifulSoup) -> str:
        """Length (inseam) options only, not waist. Find 'Length' label then collect from the immediate next block only."""
        # Inseam options on Nudie are typically 28, 30, 32, 34, 36 (waist is 24-38).
        lengths = []
        for label in soup.find_all(string=re.compile(r"^\s*Length\s*$", re.I)):
            parent = label.parent
            if not parent:
                continue
            # Next sibling of the label's parent is usually the Length options container (not Waist).
            length_container = parent.find_next_sibling()
            if not length_container and parent.find_parent():
                length_container = parent.find_parent().find_next_sibling()
            if length_container:
                for el in length_container.find_all(["button", "a", "span", "div", "li"]):
                    t = el.get_text(strip=True)
                    if t.isdigit() and len(t) == 2 and 26 <= int(t) <= 38 and t not in lengths:
                        lengths.append(t)
            if lengths:
                break
        # If we got too many (e.g. waist 24-38), we may have hit a wrapper; prefer set that looks like inseams only
        if len(lengths) > 6:
            lengths = [t for t in lengths if int(t) in (28, 30, 32, 34, 36)]
        return ", ".join(sorted(set(lengths), key=int)) if lengths else ""

    def _extract_colorway(self, desc_paragraph: str, product_name: str) -> str:
        """Colors referring to the jeans (exclude thread/trim); comma-separated."""
        color_words = ["black", "indigo", "blue", "grey", "gray", "white", "navy", "redcast", "greenish", "misty", "pale"]
        found = []
        text = (product_name + " " + desc_paragraph).lower()
        for c in color_words:
            if c in text and c not in found:
                if "thread" in text and c in ["orange", "black", "navy"] and "thread" in text[text.find(c):text.find(c)+30]:
                    continue
                if "trim" in text or "trims" in text:
                    pass
                found.append(c)
        return ", ".join(found) if found else ""

    def _extract_notes(self, soup: BeautifulSoup, product_name: str, panel_text: str) -> str:
        """Members only, Limited (from main/product area or panel); Deadstock from product name or panel only."""
        notes = []
        main_text = ""
        main = soup.find("main")
        if main:
            main_text = main.get_text()
        search_text = (product_name + " " + panel_text + " " + main_text)
        if "Members only" in search_text or "members only" in search_text:
            notes.append("Members only")
        if re.search(r"Limited\s*:\s*\d+\s*PCS?", search_text, re.I) or "Limited to " in search_text:
            notes.append("Limited")
        if "Deadstock" in product_name or "Deadstock" in panel_text:
            notes.append("Deadstock")
        return "; ".join(notes) if notes else ""

    def _extract_status_and_prices(self, soup: BeautifulSoup) -> tuple:
        """Return (status, regular_price, sales_price). Prices as numbers."""
        status = "regular"
        regular_price = None
        sales_price = None
        page_text = soup.get_text()
        numbers = re.findall(r"[\d.]+", page_text)
        prices = []
        for elem in soup.find_all(string=re.compile(r"\d+\s*CAD|\$\d+")):
            m = re.search(r"[\d.]+", elem)
            if m:
                try:
                    prices.append(float(m.group()))
                except ValueError:
                    pass
        if len(prices) >= 2 and prices[1] < prices[0]:
            status = "on-sales"
            regular_price = prices[0]
            sales_price = prices[1]
        elif prices:
            regular_price = prices[0]
            sales_price = None
        return status, (regular_price if regular_price is not None else ""), (sales_price if sales_price is not None else "")

    def _extract_denim_weight_oz(self, panel_text: str) -> str:
        """Second bullet in Details panel (first line with oz + denim) - extract numeric weight."""
        bullets = [b.strip() for b in panel_text.split("\n") if b.strip()]
        oz_denim_bullets = [
            b for b in bullets
            if re.search(r"\d+(?:\.\d+)?\s*oz", b, re.I) and "denim" in b.lower()
        ]
        if not oz_denim_bullets:
            return ""
        target = oz_denim_bullets[0]
        m = re.search(r"(\d+(?:\.\d+)?)\s*oz", target, re.I)
        return m.group(1) if m else ""

    def _extract_denim_cat(self, panel_text: str) -> str:
        """Second bullet in Details panel (first line with oz + denim) - full phrase."""
        bullets = [b.strip() for b in panel_text.split("\n") if b.strip()]
        oz_denim_bullets = [
            b for b in bullets
            if re.search(r"\d+(?:\.\d+)?\s*oz", b, re.I) and "denim" in b.lower()
        ]
        if not oz_denim_bullets:
            return ""
        return oz_denim_bullets[0]

    def _extract_material(self, panel_text: str) -> str:
        """Line with % Cotton / Elastane (usually under Made in)."""
        m = re.search(r"(\d+%\s*Cotton(?:\s*\d+%\s*Elastane)?)", panel_text, re.I)
        return m.group(1).strip() if m else ""

    def _extract_made_in(self, panel_text: str) -> str:
        m = re.search(r"Made\s+in\s+([A-Za-z\s]+?)(?:\d|$)", panel_text)
        if m:
            return f"Made in {m.group(1).strip()}"
        return ""

    def save_to_csv(self, data: List[Dict], filename: str = "nudie_jeans_products.csv") -> str:
        """Save to CSV with schema comparable to N&F (nudie_product_url instead of nf_product_url)."""
        os.makedirs("data/processed", exist_ok=True)
        filepath = os.path.join("data/processed", filename)
        columns = [
            "product_id", "sku", "product_name", "fit_id", "fabric_id", "wash_state",
            "gender", "default_inseam_label", "colorway", "status", "regular_price", "sales_price",
            "nudie_product_url", "description_html", "release_season", "run_code", "notes",
            "denim_weight_oz", "denim_cat", "material", "made_in", "product_description",
            "collections", "is_jeans", "scraped_at",
        ]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(columns)
            for row in data:
                writer.writerow([str(row.get(c, "")) for c in columns])
        self.logger.info(f"Saved {len(data)} products to {filepath}")
        return filepath

    def scrape_all(self, sample_size: Optional[int] = None) -> List[Dict]:
        """Get all product URLs by fit, then scrape each. If sample_size set, only scrape that many (for testing)."""
        self.logger.info("Starting Nudie Jeans scrape (men's fits)")
        urls = self.get_product_urls()
        self.logger.info(f"Found {len(urls)} product URLs")
        if sample_size is not None:
            urls = urls[:sample_size]
            self.logger.info(f"Sample run: scraping first {len(urls)} products")
        self._product_id_counter: Dict[str, int] = {}  # base slug -> count for collision suffix _2, _3, ...
        products = []
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Scraping product {i}/{len(urls)}: {url}")
            row = self.scrape_product(url)
            if row:
                products.append(row)
            time.sleep(2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_to_csv(products, f"nudie_jeans_products_{timestamp}.csv")
        self.save_to_json(products, f"nudie_jeans_products_{timestamp}.json")
        self.logger.info(f"Scraping completed. Found {len(products)} products.")
        return products
