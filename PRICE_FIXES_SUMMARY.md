# Price Extraction and Product ID Fixes

## Summary
Fixed two critical issues in the Naked & Famous scraper:
1. **Price extraction logic** - Products were incorrectly marked as "on-sales" when they only had regular prices
2. **Product ID generation** - Removed unnecessary alphanumeric hash suffixes

## Changes Made

### 1. Price Extraction Fix (`_extract_status_and_prices` method)

**Problem:**
- Products with only a regular price (like Cashmere Stretch at $306) were incorrectly marked as "on-sales"
- The scraper was finding a `sale-price` element (which is just the price display element, not necessarily indicating a sale)
- Then it was finding a `compare-at-price` from elsewhere on the page (possibly from related products or templates)
- This resulted in incorrect status and prices (e.g., regular_price=$345, sales_price=$306 when it should be regular_price=$306)

**Solution:**
- **Strict requirement**: Only mark as "on-sales" when BOTH a crossed-out `compare-at-price` AND a `sale-price` are found in the SAME container
- **Single price = regular**: If only one price is found, it's ALWAYS treated as the regular price (not on sale)
- **Removed aggressive fallback**: Removed the logic that searched for prices "more aggressively" which could pick up unrelated prices from other parts of the page

**Code Changes:**
```python
# OLD LOGIC (lines 1026-1077):
# - Would call _extract_status() to verify if on sale
# - Would search for compare-at-price "more aggressively" if only sale-price found
# - Could find prices from unrelated elements

# NEW LOGIC (lines 1026-1038):
# - Only mark as "on-sales" if BOTH regular_price AND sale_price found
# - If only one price found, it's ALWAYS regular_price
# - No aggressive searching that could find unrelated prices
```

**Expected Results:**
- `weird_guy_cashmere_stretch_blend_denim_raw`: 
  - Status: `regular` (not `on-sales`)
  - Regular Price: `306.00` (not `345.00`)
  - Sales Price: `` (empty, not `306.00`)
  
- `easy_guy_max_brush_selvedge_indigo_raw`:
  - Status: `regular` (not `on-sales`)
  - Regular Price: actual regular price (not `345.00`)
  - Sales Price: `` (empty)

### 2. Product ID Generation Fix (`_generate_product_id` method)

**Problem:**
- Product IDs had unnecessary alphanumeric hash suffixes
- Example: `easy_guy_solid_black_selvedge_raw_35f21c77`
- The user questioned if the hash suffix is necessary since `fit_id + fabric_id + wash_state` should be unique

**Solution:**
- Removed the hash suffix generation
- Product IDs now use the format: `{fit_id}_{fabric_id}_{wash_state}`
- Example: `easy_guy_solid_black_selvedge_raw` (no hash suffix)

**Code Changes:**
```python
# OLD LOGIC (lines 321-348):
# - Would check if URL slug is redundant
# - Would add URL slug or hash suffix for uniqueness
# - Result: product_id with hash like "easy_guy_solid_black_selvedge_raw_35f21c77"

# NEW LOGIC (lines 321-325):
# - Simply return base_product_id (fit + fabric + wash)
# - Result: "easy_guy_solid_black_selvedge_raw"
```

**Note on Uniqueness:**
- The combination of `fit_id + fabric_id + wash_state` should be unique for each product
- If duplicates occur in the future, we can add logic to handle them (e.g., add colorway or SKU)
- For now, keeping it simple as requested

## Testing

To test the fixes, run:
```bash
python test_price_fixes.py
```

Or test on the full dataset:
```bash
python test_scraper_fixes.py
```

**Expected Test Results:**
1. Products with only one price should have:
   - `status = 'regular'`
   - `regular_price = <actual price>`
   - `sales_price = ''` (empty)

2. Products actually on sale should have:
   - `status = 'on-sales'`
   - `regular_price = <original price>`
   - `sales_price = <sale price>`
   - Both prices found in the same container

3. Product IDs should NOT have hash suffixes:
   - ✅ `easy_guy_solid_black_selvedge_raw`
   - ❌ `easy_guy_solid_black_selvedge_raw_35f21c77`

## Files Modified

- `src/scrapers/naked_famous_new_scraper.py`:
  - `_extract_status_and_prices()` method (lines ~1026-1038)
  - `_generate_product_id()` method (lines ~321-325)

## Next Steps

1. Run the scraper on the full product catalog to verify fixes
2. Check the results CSV for:
   - Products that were incorrectly marked as "on-sales" should now be "regular"
   - Prices should match what's actually displayed on the website
   - Product IDs should be cleaner without hash suffixes
3. If duplicates occur in product_id, we can add additional distinguishing factors
