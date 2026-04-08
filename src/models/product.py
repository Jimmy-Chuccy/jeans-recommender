from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum

class Gender(str, Enum):
    MENS = "mens"
    WOMENS = "womens"
    UNISEX = "unisex"

class FitType(str, Enum):
    SKINNY = "skinny"
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    STRAIGHT = "straight"
    TAPERED = "tapered"
    BOOTCUT = "bootcut"
    WIDE = "wide"

class Product(BaseModel):
    # Basic Info
    brand: str
    name: str
    sku: Optional[str] = None
    gender: Gender
    category: str = "jeans"
    
    # Fit & Style
    fit: Optional[FitType] = None
    rise: Optional[str] = None  # low, mid, high
    leg_opening: Optional[float] = None  # inches
    
    # Fabric
    fabric_weight: Optional[str] = None  # oz
    fabric_composition: Optional[str] = None
    stretch: Optional[bool] = None
    selvedge: Optional[bool] = None
    
    # Sizing
    sizes_available: List[str] = []
    size_chart: Optional[Dict[str, Dict[str, float]]] = None  # size -> measurements
    
    # Measurements (in inches)
    waist: Optional[float] = None
    inseam: Optional[float] = None
    thigh: Optional[float] = None
    knee: Optional[float] = None
    leg_opening_width: Optional[float] = None
    
    # Pricing & Availability
    price: Optional[float] = None
    currency: str = "USD"
    in_stock: bool = True
    
    # URLs
    product_url: str
    image_urls: List[str] = []
    
    # Metadata
    description: Optional[str] = None
    features: List[str] = []
    care_instructions: Optional[str] = None
    
    # Source tracking
    scraped_from: str
    scraped_at: Optional[str] = None

class SizeChart(BaseModel):
    brand: str
    product_name: str
    gender: Gender
    measurements: Dict[str, Dict[str, float]]  # size -> measurement_type -> value
    units: str = "inches"
