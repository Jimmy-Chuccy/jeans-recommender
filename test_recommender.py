#!/usr/bin/env python3
"""
Test script for the recommender system
"""

from src.recommenders.recommender import recommend
from src.recommenders.models import UserInput


def test_basic_recommendation():
    """Test: reference Levi's 501 size 34, get top 5 per brand"""
    print("Testing basic recommendation (reference: Levi's 501 size 34)...")
    user_input = UserInput(
        fit_preference="relaxed",
        reference_brand="levis",
        reference_fit_or_model="501",
        reference_size=34,
        gender="mens",
        rise_preference="higher",
        thigh_preference="more",
        leg_opening_preference="wider",
    )
    recommendations = recommend(user_input)
    print(f"\nFound {len(recommendations)} recommendations:")
    for rec in recommendations:
        print(f"  [{rec['brand']}] {rec['product_name']} - size {rec['tag_size']} - {rec.get('price', '')} - {rec['product_url']}")
    assert len(recommendations) > 0, "Should have at least one recommendation"
    print("✅ Basic test passed!")


def test_reference_none():
    """Test: no reference brand, general size 32"""
    print("\nTesting no reference brand (general size 32)...")
    user_input = UserInput(
        fit_preference="slim",
        reference_brand="none",
        reference_fit_or_model=None,
        reference_size=32,
        gender="mens",
        rise_preference="similar",
        thigh_preference="similar",
        leg_opening_preference="similar",
    )
    recommendations = recommend(user_input)
    print(f"\nFound {len(recommendations)} recommendations:")
    for rec in recommendations[:6]:
        print(f"  [{rec['brand']}] {rec['product_name']} - size {rec['tag_size']}")
    print("✅ No reference test passed!")


if __name__ == "__main__":
    try:
        test_basic_recommendation()
        test_reference_none()
        print("\n" + "=" * 60)
        print("All tests passed! ✅")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
