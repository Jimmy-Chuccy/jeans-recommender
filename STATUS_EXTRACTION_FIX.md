# Status Extraction Fix - Breakdown

## Problem
All products were incorrectly being marked as "on-sales" even when they only had a single regular price.

## Root Cause Analysis

The original logic was too aggressive and matched ANY element with `line-through` class anywhere on the page, including:
- Template text like "Regular price$223.00 CAD"
- Prices from related products
- Prices from product variants
- Other non-relevant elements

## Solution

The new logic requires **BOTH** conditions to be met:
1. **A crossed-out original price** (`compare-at-price` element with `line-through` class)
2. **A sale price** (`sale-price` element) 
3. **Both must be in the same price container** (to avoid matching prices from different products)
4. **The sale price must be lower** than the original price

## Implementation Details

### Step 1: Find Main Product Price Container
- Looks for common price container selectors (`div.product-price`, `div.price`, etc.)
- Prefers containers in the main product area (not related products)

### Step 2: Check for Both Price Types
- Searches for `compare-at-price` elements (original/crossed-out price)
- Searches for `sale-price` elements (current sale price)
- Only considers elements in the main product area

### Step 3: Verify Same Container
- Checks if both price elements share a common parent container
- This ensures they're for the same product, not different products on the page

### Step 4: Validate Price Relationship
- Extracts numeric values from both prices
- Verifies sale price < original price
- Only then returns "on-sales"

### Fallback Logic
- If main container not found, searches parent containers up to 4 levels
- Still requires both price types in same container with valid price relationship

## Result

- **Regular price products**: Return "regular" (only one price shown)
- **On-sale products**: Return "on-sales" (both crossed-out and sale price present)
- **Sold out products**: Return "discontinued" (if sold out indicator found)

