"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card
import re

# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────
def _parse_query(query: str) -> dict:
    """
    Extract a rough description, size, and max_price from the user's query.

    This parser is intentionally simple:
    - max_price comes from phrases like "under $30" or "$30"
    - size comes from phrases like "size M" or "in size M"
    - description is the query with price and size phrases removed
    """
    parsed = {
        "description": query.strip(),
        "size": None,
        "max_price": None,
    }

    # Extract price, e.g. "under $30", "$30", "under 30"
    price_match = re.search(r"(?:under\s*)?\$?(\d+(?:\.\d{1,2})?)", query, re.IGNORECASE)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))

    # Extract size, e.g. "size M", "in size M"
    size_match = re.search(r"\bsize\s+([A-Za-z0-9./-]+)\b", query, re.IGNORECASE)
    if size_match:
        parsed["size"] = size_match.group(1).upper()

    # Remove price and size phrases from description
    description = query
    description = re.sub(r"(?:under\s*)?\$?\d+(?:\.\d{1,2})?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\b(?:in\s+)?size\s+[A-Za-z0-9./-]+\b", "", description, flags=re.IGNORECASE)

    # Clean common filler words
    description = description.replace(",", " ")
    description = re.sub(r"\s+", " ", description).strip()

    parsed["description"] = description

    return parsed


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Guard against empty query
    #if not query or not query.strip():
        #session["error"] = "Please enter what kind of thrifted item you're looking for."
        #return session
    
    # Step 2: Parse user query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # Step 3: Call search_listings()
    search_results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )
    session["search_results"] = search_results
    
    # Branch: no results found
    if not search_results:
        session["error"] = (
            "No listings matched your request. Try broadening the description, "
            "choosing a different size, or increasing your max price."
        )
        return session
    
    # Step 4: Select top item
    selected_item = search_results[0]
    session["selected_item"] = selected_item

    # Step 5: Call suggest_outfit()
    outfit_suggestion = suggest_outfit(
        new_item=selected_item,
        wardrobe=wardrobe,
    )
    session["outfit_suggestion"] = outfit_suggestion

    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = (
            "I found a listing, but I couldn't create an outfit suggestion for it. "
            "Please ensure your wardrobe has enough items and try again.")
        return session
    
    # Step 6: Call create_fit_card
    fit_card = create_fit_card(
        outfit=outfit_suggestion,
        new_item=selected_item,
    )
    session["fit_card"] = fit_card

    if not fit_card or not fit_card.strip():
        session["error"] = (
            "I created an outfit suggestion, but I couldn't create a fit card from it."
        )
        return session
    
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
