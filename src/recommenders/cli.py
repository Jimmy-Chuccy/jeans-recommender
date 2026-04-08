"""
Interactive command-line interface for the recommender
"""

from .recommender import recommend
from .models import UserInput
from .fit_mapper import get_fit_options_for_brand

REFERENCE_BRAND_CHOICES = [
    ("1", "nf", "Naked & Famous"),
    ("2", "nudie", "Nudie Jeans"),
    ("3", "levis", "Levi's"),
    ("4", "none", "None of the above"),
]


def interactive_recommendation():
    print("=" * 60)
    print("  Jeans Recommender – N&F, Nudie, Levi's")
    print("=" * 60)
    print()
    print("Step 1: What fit style do you prefer?")
    print("Options: relaxed, slim, tapered, straight, bootcut, skinny")
    fit_preference = input("Enter preference (or Enter to skip): ").strip().lower() or None
    if fit_preference and fit_preference not in ["relaxed", "slim", "tapered", "straight", "bootcut", "skinny"]:
        print("Invalid. Using skip.")
        fit_preference = None

    print("\nStep 2: Do you own jeans from Naked & Famous, Nudie Jeans or Levi's?")
    print("1 – Naked & Famous  2 – Nudie Jeans  3 – Levi's  4 – None")
    ref_choice = input("Enter 1–4: ").strip()
    reference_brand = "none"
    for num, key, _ in REFERENCE_BRAND_CHOICES:
        if ref_choice == num:
            reference_brand = key
            break

    reference_fit_or_model = None
    if reference_brand != "none":
        options = get_fit_options_for_brand(reference_brand, "mens")
        brand_label = next((l for n, k, l in REFERENCE_BRAND_CHOICES if k == reference_brand), reference_brand)
        print(f"\nWhat jeans do you wear from {brand_label}?")
        for i, o in enumerate(options, 1):
            print(f"  {i}. {o.get('name', o.get('id'))}")
        model_in = input("Enter number or fit name: ").strip()
        try:
            idx = int(model_in)
            if 1 <= idx <= len(options):
                reference_fit_or_model = options[idx - 1].get("id", "")
        except ValueError:
            for o in options:
                if (o.get("id") or "").lower() == model_in.lower() or (o.get("name") or "").lower() == model_in.lower():
                    reference_fit_or_model = o.get("id", "")
                    break
        if not reference_fit_or_model and options:
            reference_fit_or_model = options[0].get("id", "")

    print("\nWhat size do you wear?" if reference_brand != "none" else "What size do you comfortably wear on most jeans?")
    try:
        reference_size = int(input("Size (e.g. 30, 32, 34): ").strip())
    except ValueError:
        print("Invalid. Using 32.")
        reference_size = 32

    print("\nStep 3: Fine-tune preferences")
    rise_preference = input("Rise: higher/lower/similar [similar]: ").strip().lower() or "similar"
    thigh_preference = input("Thigh: more/less/similar [similar]: ").strip().lower() or "similar"
    leg_opening_preference = input("Leg opening: wider/narrower/similar [similar]: ").strip().lower() or "similar"

    user_input = UserInput(
        fit_preference=fit_preference,
        reference_brand=reference_brand,
        reference_fit_or_model=reference_fit_or_model,
        reference_size=reference_size,
        gender="mens",
        rise_preference=rise_preference,
        thigh_preference=thigh_preference,
        leg_opening_preference=leg_opening_preference,
    )
    print("\nProcessing...")
    try:
        recommendations = recommend(user_input)
        if not recommendations:
            print("No recommendations found.")
            return
        print(f"\n✅ Top recommendations (up to 5 per brand):\n")
        by_brand = {}
        for r in recommendations:
            b = r.get("brand", "")
            by_brand.setdefault(b, []).append(r)
        for brand in ["nf", "nudie", "levis"]:
            recs = by_brand.get(brand, [])
            if not recs:
                continue
            label = {"nf": "Naked & Famous", "nudie": "Nudie Jeans", "levis": "Levi's"}.get(brand, brand)
            print(f"  {label}")
            for r in recs:
                print(f"    {r['product_name']} – size {r['tag_size']}  {r.get('price', '')}")
                print(f"    {r['product_url']}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    interactive_recommendation()
