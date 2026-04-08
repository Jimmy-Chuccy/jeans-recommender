# Naked & Famous Size Recommender

A recommendation system that helps users find the right Naked & Famous jeans based on their fit preferences and Levi's sizing reference.

## Features

- **Fit Preference Matching**: Map user preferences (relaxed, slim, tapered, etc.) to N&F fits
- **Cross-Brand Sizing**: Use Levi's jeans as a reference point for sizing
- **Measurement-Based Scoring**: Score candidates based on rise, thigh room, and leg opening preferences
- **Intelligent Filtering**: Return top 10 recommendations or all if fewer than 10

## Architecture

```
src/recommenders/
├── __init__.py          # Package exports
├── models.py            # Data models (UserInput, CandidateProduct)
├── data_loader.py       # CSV file loading utilities
├── fit_mapper.py        # Preference and Levi's model mapping
├── size_matcher.py      # N&F waist / size matching
├── nudie_matcher.py     # Nudie: fit-level rank, dry + random to 5
├── levis_matcher.py     # Levi's: fit-level rank, random SKUs to 5
├── scorer.py            # Scoring algorithm with tie-breaking
├── recommender.py       # Main recommendation engine
└── cli.py               # Interactive command-line interface
```

## Usage

### Interactive CLI

Run the interactive recommender:

```bash
python run_recommender.py
```

The CLI will prompt you for:
1. **Fit preference**: relaxed, slim, tapered, straight, bootcut, or skinny
2. **Levi's reference**: Model number (e.g., 501, 511) and your size
3. **Fine-tuning questions**:
   - Rise preference (higher/lower/similar)
   - Thigh room (more/less/similar)
   - Leg opening (wider/narrower/similar)

### Programmatic Usage

```python
from src.recommenders.recommender import recommend
from src.recommenders.models import UserInput

user_input = UserInput(
    fit_preference="relaxed",
    levis_model="501",
    levis_size=34,
    gender="mens",
    rise_preference="higher",
    thigh_preference="more",
    leg_opening_preference="wider"
)

recommendations = recommend(user_input)

for rec in recommendations:
    print(f"{rec['product_name']}: {rec['product_url']}")
```

## Nudie Jeans matching

Measurements are **per fit**, not per SKU. The pipeline:

1. Map fit preference → candidate Nudie fits (`fit_mapper`).
2. For each fit, pick the best tag size for the user’s target waist (same waist rule as before).
3. **Rank fits** with the same rise/thigh/leg scorer (one row per fit).
4. **Top matched fits**: fits within 40 points of the best score (up to 5 fits).
5. For each top fit: pick **one `wash_state == dry`** product if available; else a random regular product.
6. **Fill to 5** with random products from those top fits (correct tag size per fit, no duplicate URLs).

N&F matching is unchanged.

### Levi's Jeans matching

Same pattern as Nudie at the **fit (model) level**: preference maps to candidate models (`501`, `541`, …). Each model’s manual row (size 32 baseline) is **scaled** to `reference_size`. Fits are **ranked** with the same rise/thigh/leg scorer. **Top fits** are those within 40 points of the best score (up to 5). Up to **5 SKUs** are chosen **at random** from products whose `fit_id` is in that top set, all at the user’s size.

## How It Works

### 1. Fit Mapping
- User preference (e.g., "relaxed") → Maps to N&F fits (e.g., ["strong_guy", "easy_guy"])
- If no preference → Uses Levi's model to infer fit characteristics

### 2. Size Matching
- Finds N&F tag sizes with waist measurement >= user's Levi's size
- Example: User wears Levi's 501 size 34 → Finds N&F sizes with waist >= 34"

### 3. Scoring
- Scores candidates based on Q&A preferences:
  - **Rise**: Higher/lower/similar preference
  - **Thigh room**: More/less/similar (using knee measurement as proxy)
  - **Leg opening**: Wider/narrower/similar
- Equal weights for all preferences
- Tie-breaking priority: Rise > Thigh > Leg Opening

### 4. Output
- Returns top 10 if >=10 candidates
- Returns all if <10 candidates
- Each recommendation includes product name and URL

## Preference Mapping

| User Preference | N&F Fits |
|----------------|----------|
| relaxed | strong_guy, easy_guy |
| slim | super_guy, true_guy, weird_guy |
| tapered | weird_guy, easy_guy, super_guy |
| straight | true_guy, strong_guy |
| bootcut | groovy_guy |
| skinny | super_guy, stacked_guy |

## Data Requirements

The recommender loads from these CSV files in `data/processed/` (see `data_loader.py`):

**N&F (Naked & Famous)**
- `naked_famous_products_latest.csv` - N&F product catalog (or dated equivalent)
- `naked_famous_size_charts_latest.csv` - N&F size chart measurements
- `fits_new.csv` - N&F fit metadata

**Nudie Jeans**
- `nudie_jeans_products_latest.csv` - Nudie product catalog
- `Nudie_Jeans_measurements_manual.csv` - Nudie measurements by fit/size
- `Nudie_Jeans_fits.csv` - Nudie fit metadata

**Levi's**
- `levis_product_manual_new_20260317.csv` - Levi's product catalog (with price)
- `levis_measurements_manual.csv` - Levi's baseline measurements (e.g. size 32)

## Testing

Run the test suite:

```bash
python test_recommender.py
```

## Future Enhancements

- [ ] Text analytics for Levi's model to N&F fit mapping
- [ ] Support for women's fits
- [ ] Additional measurement comparisons
- [ ] User feedback loop for improving recommendations
- [ ] Web interface

