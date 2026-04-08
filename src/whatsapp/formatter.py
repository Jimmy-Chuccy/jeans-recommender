"""
Message formatting utilities for WhatsApp
"""

from typing import List, Dict


def format_welcome_message() -> str:
    """Greeting and first step: fit style"""
    return """👖 *Let me help you find the best jeans for you.*

*Step 1:* What fit style are you looking for?

Options: *Relaxed*, *Slim*, *Tapered*, *Straight*, *Bootcut*, *Skinny*

(Reply with one of the options above, or type *skip* to skip)"""


def format_fit_question() -> str:
    """Fit preference question (same as welcome step 1)"""
    return """*Step 1:* What fit style are you looking for?
Options: Relaxed, Slim, Tapered, Straight, Bootcut, Skinny
(Reply with your preference or type *skip*)"""


def format_reference_brand_question() -> str:
    """Do you own jeans from N&F, Nudie, or Levi's?"""
    return """*Step 2:* Do you own a pair of jeans from Naked & Famous, Nudie Jeans or Levi's that can help us reference?

Reply with a number:
*1* – Naked & Famous
*2* – Nudie Jeans
*3* – Levi's
*4* – None of the above"""


def format_reference_model_question(brand_label: str, options: List[Dict[str, str]]) -> str:
    """What jeans do you wear from X? (numbered list of fits/models)"""
    lines = [f"*What jeans do you wear from {brand_label}?*", ""]
    for i, opt in enumerate(options, 1):
        lines.append(f"*{i}* – {opt.get('name', opt.get('id', ''))}")
    lines.append("")
    lines.append("(Reply with the number or the fit name)")
    return "\n".join(lines)


def format_needs_reference_or_promo_message() -> str:
    """User skipped fit and has no reference brand — offer promotions instead."""
    return """We need at least either your *fit preference* or a *reference product* to make a full jeans recommendation, so we can't suggest specific fits right now.

*Would you like to see some promotions?* (on-sale picks from Naked & Famous and Levi's, matched to your size and shape preferences)

Reply *yes* or *no*"""


def format_promo_declined_thanks() -> str:
    return "Thank you! Type *start* anytime if you'd like to try again."


def format_promotional_recommendations(recommendations: List[Dict]) -> str:
    """Up to 10 on-sale SKUs (N&F-heavy; Nudie omitted if no sale data)."""
    if not recommendations:
        return """We couldn't find on-sale items that match your size right now.

Type *start* to try again."""

    parts = [
        "🛍️ *Promotional picks* (on-sale only)",
        "_Compared to a straight-fit benchmark for your size (Nudie Rad Rufus)._",
        "",
    ]
    for i, rec in enumerate(recommendations, 1):
        name = rec.get("product_name", "")
        size = rec.get("tag_size", "")
        price = rec.get("price", "")
        url = rec.get("product_url", "")
        brand = _brand_display_name(rec.get("brand", ""))
        price_str = f" – ${price}" if price else ""
        parts.append(f"{i}. *{brand}* – {name}")
        parts.append(f"   Size {size}{price_str}")
        parts.append(f"   {url}")
        parts.append("")
    parts.append("Type *start* for a new session!")
    msg = "\n".join(parts)
    if len(msg) > 4000:
        msg = msg[:3900] + "\n\n... (truncated)"
    return msg


def format_no_reference_size_question() -> str:
    """When user has no reference brand: ask general size"""
    return """That's cool! Tell me – what size do you comfortably wear on most jeans?

(Reply with your usual waist size, e.g. 30, 32, 34)"""


def format_reference_size_question() -> str:
    """What size do you wear in that model?"""
    return """*What size do you wear?*

(Reply with your size, e.g. 30, 32, 34)"""


def format_rise_question() -> str:
    return """*Step 3:* Let's fine-tune your preferences:

1️⃣ *Rise:* Do you prefer higher (vintage look) or lower (modern look)?
Reply: *higher* / *lower* / *similar*"""


def format_thigh_question() -> str:
    return """2️⃣ *Thigh room:* Would you like more or less room around the thighs?
Reply: *more* / *less* / *similar*"""


def format_leg_opening_question() -> str:
    return """3️⃣ *Leg opening:* Would you prefer wider or narrower leg opening?
Reply: *wider* / *narrower* / *similar*"""


def format_processing_message() -> str:
    return "⏳ Finding the best recommendations for you..."


def _brand_display_name(brand: str) -> str:
    if brand == "nf":
        return "Naked & Famous"
    if brand == "nudie":
        return "Nudie Jeans"
    if brand == "levis":
        return "Levi's"
    return brand


def format_recommendations(recommendations: List[Dict]) -> str:
    """
    Format: product name, size, price, URL. Top 5 per brand (N&F, Nudie, Levi's).
    """
    if not recommendations:
        return """❌ No recommendations found.

This might be because no products match your criteria or sizes.

Type *start* to try again!"""

    by_brand: Dict[str, List[Dict]] = {"nf": [], "nudie": [], "levis": []}
    for r in recommendations:
        b = r.get("brand", "")
        if b in by_brand:
            by_brand[b].append(r)

    parts = ["✅ *Here are your top recommendations:*", ""]
    for brand in ["nf", "nudie", "levis"]:
        recs = by_brand.get(brand, [])
        if not recs:
            continue
        parts.append(f"*{_brand_display_name(brand)}*")
        parts.append("")
        for i, rec in enumerate(recs[:5], 1):
            name = rec.get("product_name", "")
            size = rec.get("tag_size", "")
            price = rec.get("price", "")
            url = rec.get("product_url", "")
            price_str = f" – ${price}" if price else ""
            parts.append(f"{i}. {name} – size {size}{price_str}")
            parts.append(url)
            parts.append("")
        parts.append("")
    parts.append("Type *start* for new recommendations!")

    message = "\n".join(parts)
    if len(message) > 4000:
        message = message[:3900] + "\n\n... (truncated)"
    return message


def format_error_message(error: str) -> str:
    return f"❌ Error: {error}\n\nType *start* to begin again."


def format_invalid_input_message(field: str, valid_options: List[str] = None) -> str:
    msg = f"⚠️ Invalid input for {field}."
    if valid_options:
        msg += f"\nValid options: {', '.join(valid_options)}"
    msg += "\n\nPlease try again."
    return msg


def format_help_message() -> str:
    return """*Help*

• *start* – Begin new recommendation
• *help* – Show this message
• *reset* – Reset current session

*Flow:* Fit style → Reference brand → Model & size (if applicable) → Fine-tune → recommendations.

If you skip fit *and* have no reference brand, we can show *on-sale picks* instead."""


# Legacy aliases for bot that might still reference these
def format_levis_model_question() -> str:
    return format_reference_size_question()


def format_levis_size_question() -> str:
    return format_reference_size_question()
