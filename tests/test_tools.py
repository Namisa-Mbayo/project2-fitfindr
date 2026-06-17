from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    new_item = results[0]
    outfit = suggest_outfit(new_item, get_empty_wardrobe())
    assert outfit == []  # empty wardrobe should return empty outfit

def test_create_fit_card_missing_item():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    new_item = results[0]
    outfit = suggest_outfit(new_item, get_example_wardrobe())
    # Simulate an incomplete outfit by removing an item
    if outfit:
        outfit.pop()
    fit_card = create_fit_card(outfit, new_item)
    assert isinstance(fit_card, str)
    assert len(fit_card) > 0  # Should still return a string even if outfit is incomplete

def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    new_item = results[0]
    response = create_fit_card("", new_item)
    assert isinstance(response, str)
    assert "fit card" in response.lower()
    assert "incomplete" in response.lower() or "missing" in response.lower()