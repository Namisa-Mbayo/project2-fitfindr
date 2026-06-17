"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

from http import client
import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # 1. Load all listings
    listings = load_listings()

    # 2. Filter by max_price and size
    filtered = []

    for listing in listings:
        if max_price is not None and listing.get("price", 0) > max_price:
            continue

        if size is not None:
            listing_size = listing.get("size", "").lower()
            if size.lower() not in listing_size:
                continue

        filtered.append(listing)

    # 3. Score each listing by keyword overlap with `description`
    description = description or ""
    keywords = set(description.lower().split())

    def score_listing(listing: dict) -> int:
        searchable = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand") or "",
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]).lower()

        return sum(1 for kw in keywords if kw in searchable)

    scored = [(listing, score_listing(listing)) for listing in filtered]

    # 4. Drop listings with score 0
    scored = [(listing, score) for listing, score in scored if score > 0]

    if not scored:
        return []

    # 5. Sort by score descending and return listing dicts
    scored.sort(key=lambda x: x[1], reverse=True)

    return [listing for listing, _ in scored[:3]]  # Return top 3 matches

    #except Exception:
        #return (
            #"No listings were found that matched your request. "
            #"Try broadening the description, choosing a different size, "
            #"or increasing the budget.")


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """

    # 1. Empty wardrobe — general styling advice
    if not new_item:
            return (
                "I need a thrifted item before I can suggest an outfit. "
                "Try searching for an item first."
            )
    
    items = wardrobe.get("items", [])

    if not items:
        prompt = f"""You are a personal stylist. A user just thrifted this item:

Item: {new_item.get('title', 'Unknown item')}
Description: {new_item.get('description', 'N/A')}
Category: {new_item.get('category', 'N/A')}
Colors: {', '.join(new_item.get('colors', []))}
Style tags: {', '.join(new_item.get('style_tags', []))}

They don't have any wardrobe items saved yet. Give them brief, general styling advice:
- What types of pieces pair well with this item?
- What overall vibe or aesthetic does it suit?
- Suggest 1–2 hypothetical outfit ideas using common wardrobe staples.

Keep it friendly, specific, and practical. Do not ask follow-up questions."""

    # 2. Wardrobe exists — suggest specific combinations
    else:
        wardrobe_lines = "\n".join(
            f"- [{item.get('category', '?')}] {item.get('name', '?')} "
            f"(colors: {', '.join(item.get('colors', []))}; "
            f"tags: {', '.join(item.get('style_tags', []))})"
            for item in items
        )

        prompt = f"""You are a personal stylist. A user just thrifted this item:

Item: {new_item.get('title', 'Unknown item')}
Description: {new_item.get('description', 'N/A')}
Category: {new_item.get('category', 'N/A')}
Colors: {', '.join(new_item.get('colors', []))}
Style tags: {', '.join(new_item.get('style_tags', []))}

Here is their current wardrobe:
{wardrobe_lines}

Suggest 1–2 specific, complete outfits using the thrifted item and named pieces from their wardrobe.
For each outfit: name every piece, describe how to wear it together, and explain why it works.
Keep the tone brief and friendly. Do not suggest items outside their wardrobe. Do not ask follow-up questions."""

    # 3. Call the LLM
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a practical personal stylist for a thrift shopping app. "
                        "Give specific, wearable outfit advice. Keep the response concise, "
                        "friendly, and useful."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        result = response.choices[0].message.content.strip()

        if not result:
            return (
                "An outfit suggestion could not be created. "
                "Please check that your wardrobe has enough items and try again."
            )

        return result

    except Exception:
        return (
            "The styling tool ran into an error."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # 1. Guard against empty or whitespace-only outfit string
    if not outfit or not outfit.strip():
        return (
            "The fit card could not be created because the outfit description is incomplete. "
            "Please ensure an outfit suggestion was generated before creating a fit card."
        )
    
    if not new_item:
        return (
            "The fit card could not be created because the thrifted item is missing. "
            "Please search for an item before creating a fit card."
        )

    # 2. Build the prompt

    item_name = new_item.get("title", "thrifted item")
    price = new_item.get("price")
    platform = new_item.get("platform", "a thrift platform")
    price_str = f"${price:.2f}" if price is not None else "unknown price"

    prompt = f"""You are writing an OOTD (outfit of the day) caption for Instagram or TikTok.
    The caption should be casual and authentic, mentioning the item name, price, and platform naturally.
    
    The user thrifted this item:
    - Name: {item_name}
    - Price: {price_str}
    - Platform: {platform}

    Their full outfit:
    {outfit}

    Write a 2–4 sentence caption that:
    - Sounds casual and authentic, like a real person posting their outfit — not a product description
    - Mentions the item name, price, and platform naturally (once each)
    - Captures the specific vibe of the outfit
    - Uses language that fits the thrift/fashion community (e.g. "found this", "thrifted", "fit check")

    Do not use hashtags. Do not use quotation marks. Do not add any preamble."""

    # 3. Call the LLM with higher temperature for variety
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            temperature=1.0,  
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write short, stylish, shareable outfit captions for a thrift shopping app. "
                        "Sound casual and authentic, like a real OOTD post. Do not sound like a product listing."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        result = response.choices[0].message.content.strip()

        if not result:
            return (
                "A fit card caption could not be created."
                "Please ensure an outfit suggestion was generated before creating a fit card."
            )
        return result

    except Exception:
        return (
            "A fit card caption could not be created because the caption tool ran into an error. "
            "Please check your Groq API key and try again."
        )
