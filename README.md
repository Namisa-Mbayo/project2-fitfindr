# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```markdown
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):

```python
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:

```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:

```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Tool Inventory

### Tool 1

**Name:** `search_listings(description, size, max_price)`
**Purpose:** Searches the mock listings dataset for thrifted items matching the user’s request.
**Inputs:**

- `description` (str): User's description of the thrift item they are searching for.
- `size` (str): The size of the thrift item being searched.
- `max_price` (float): The maximum price the user is willing to pay for the thrift item.

**Outputs:** Returns a list of up to 3 matching listing dictionaries sorted by relevance. Each listing includes details such as title, price, platform, condition, size, brand, category, colors, style tags, and description.

### Tool 2

**Name:** `suggest_outfit(new_item, wardrobe)`
**Purpose:** Suggests one or more outfit ideas using the thrifted item and the user’s wardrobe.
**Inputs:**

- `new_item` (dict): The thrifted item found in `search_listings()`.
- `wardrobe` (dict): Items from the user's wardrobe.

**Outputs:** Returns a string containing a practical outfit suggestion.

### Tool 3

**Name:** `create_fit_card(outfit, new_item)`
**Purpose:** Generates a short, shareable outfit caption based on the outfit suggestion and selected thrifted item.
**Inputs:**

- `new_item` (dict): The thrifted item found in `search_listings()`.
- `outfit` (str): The suggested outfit description created in `suggest_outfit()`.

**Outputs:** Returns a 2–4 sentence caption written like an Instagram or TikTok outfit post. The caption mentions the thrifted item, price, platform, and outfit vibe.

## Planning Loop

The agent will use a conditional loop that checks the session state after each tool call before it decides what to do next.
The agent starts by analyzing the user's query and parsing it into `description`, `size`, `max_price`. Using that information, it will call `search_listings(description, size, max_price)`. If no listings are found, the agent returns a failure message telling the user that no listings were found and what to try differently. It does not call any of the other tools because there is no item to style for `suggest_outfit`. If listings are found, the best match is saved as `selected_item` in session state.
Once `selected_item` is saved the agent calls `suggest_outfit(new_item=selected_item, wardrobe=wardrobe)`. After running, it checks if an outfit suggestion was created. If no outfit suggestion was created, the agent returns an error message stating that the outfit could not be created and to ensure a thrifted item exists. If the wardrobe is empty, the agent will return basic outfit advice. If an outfit suggestion was created, the agent saves it in session state as `outfit_suggestion` and returns the suggestion. Once that's done it calls `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`. If the fit_card fails, the agent returns an error message stating that the fit card cannot be created. If the fit card is created successfully, the agent saves it in session state as `fit_card` and returns it as the final response.
The loop ends when the agent has either created a fit card or returns an error message.

## State Management

The agent stores information in a session state dictionary and is updated after each tool call.
The session state tracks:

- user_query: the original request
- description: the item description extracted from the user request
- size: the requested item size
- max_price: the maximum price the user is willing to pay
- wardrobe: the user's wardrobe items
- search_results: the listings returned by `search_listings`
- selected_item: the best matching listing chosen from the search results
- outfit_suggestion: the outfit suggestion returned by `suggest_outfit`
- fit_card: the outfit description returned by `create_fit_card`
- error: any failure message that should be shown to the user

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
| ---- | ------------ | -------------- |
| search_listings | No results match the query | Returns an empty list. The agent stores an error message and stops early without calling any other tools. |
| suggest_outfit | Wardrobe is empty | Returns general styling advice for the thrifted item instead of crashing. |
| create_fit_card | Outfit input is missing or incomplete | Returns a descriptive error message instead of raising an exception. |

## Failure Mode Testing

I deliberately tested three failure modes:

1. `search_listings` with an impossible query: `"designer ballgown size XXS under $5"`. The tool returned an empty list, and the agent stopped early with a helpful message instead of calling the later tools.

2. `suggest_outfit` with `get_empty_wardrobe()`. The tool returned general styling advice instead of crashing when `wardrobe["items"]` was empty.

3. `create_fit_card` with an empty outfit string. The tool returned a descriptive error message instead of raising an exception.
