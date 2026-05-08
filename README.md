# ClearLaunch AI Agent

> A 5-step autonomous AI agent that audits retail products before launch and delivers a **Safe to Launch / Launch with Caution / Not Safe to Launch** decision — powered by Python, Streamlit, and the Anthropic Claude API.

---

## The Problem

Every retailer launches hundreds of products per year. Before a product goes live, five things must be true simultaneously — enough stock, complete product data, competitive pricing, and a live product page. In most companies these checks are done **manually by different teams** with no single system owning the full picture.

The result: products launch broken.

- A SKU goes live with zero images
- A price is set 40% above the category average
- The product page returns a 404 error
- Customers see the broken listing before anyone notices

| Impact | Cost |
|---|---|
| Lost sales on launch day | $50K–$500K per major SKU |
| Manual audit across teams | 2–3 days, 40–80 analyst hours |
| Emergency cross-team fix | $10K–$50K per incident |
| Increased return rate from bad data | 4–8% margin reduction |

**ClearLaunch replaces the fragmented manual checklist with a single agent that audits any product in under 30 seconds.**

---

## Architecture

```
ClearLaunch AI Agent
│
├── app.py                          # Main application — agent logic and UI
│
├── Data Inputs
│   ├── inventory.csv               # Warehouse stock levels per product
│   │   ├── sku
│   │   ├── warehouse_id
│   │   ├── qty_on_hand
│   │   └── launch_threshold
│   │
│   ├── products.csv                # Product attributes and content data
│   │   ├── sku
│   │   ├── name
│   │   ├── category
│   │   ├── price
│   │   ├── description
│   │   ├── image_count
│   │   ├── has_size_chart
│   │   └── weight_kg
│   │
│   ├── pricing.csv                 # Product prices + category peer data
│   │   ├── sku
│   │   ├── name
│   │   ├── category
│   │   ├── price
│   │   └── cost
│   │
│   └── page_status.csv             # Product page URL and HTTP status
│       ├── sku
│       ├── page_url
│       └── http_status
│
├── Agent Steps
│   ├── Step 1 — Inventory Check    # Reads inventory.csv
│   ├── Step 2 — Data Validation    # Reads products.csv
│   ├── Step 3 — Pricing Scan       # Reads pricing.csv
│   ├── Step 4 — Page Verification  # Reads page_status.csv
│   └── Step 5 — AI Decision        # Calls Claude API → decision + narrative
│
└── Output
    ├── Safe to Launch
    ├── Launch with Caution
    └── Not Safe to Launch
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Data processing | pandas |
| AI narrative | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Business logic | Python 3 |
| Styling | Custom CSS — dark navy theme |

---

## Project Structure

```
launch_agent/
│
├── app.py                  # Main Streamlit app — all agent logic and UI
│
├── inventory.csv           # Warehouse stock data
├── products.csv            # Product attributes and content data
├── pricing.csv             # Product pricing + category peer data
├── page_status.csv         # Product page URLs and HTTP status codes
│
└── requirements.txt        # Python dependencies
```

---

## Input Files

The agent reads four CSV files uploaded through the sidebar.

### `inventory.csv`
One row per product per warehouse. The agent sums `qty_on_hand` across all warehouses and compares the total to `launch_threshold`.

| Column | Type | Description |
|---|---|---|
| `sku` | Text | Unique product identifier |
| `warehouse_id` | Text | Warehouse location code |
| `qty_on_hand` | Integer | Units currently in that warehouse |
| `launch_threshold` | Integer | Minimum total units required to launch |

> One product can appear on multiple rows — one per warehouse. The agent adds them all up.

---

### `products.csv`
One row per product. The agent checks every required attribute for completeness.

| Column | Type | Description |
|---|---|---|
| `sku` | Text | Unique product identifier |
| `name` | Text | Product display name |
| `category` | Text | Product category |
| `price` | Decimal | Selling price (USD) |
| `description` | Text | Product description — must not be blank |
| `image_count` | Integer | Number of uploaded images — must be > 0 |
| `has_size_chart` | Boolean | True if size chart is attached |
| `weight_kg` | Decimal | Product weight in kilograms |

---

### `pricing.csv`
Contains the audited products **plus** peer products in the same category. The peer rows are used only to calculate the category average — the agent never audits them directly.

| Column | Type | Description |
|---|---|---|
| `sku` | Text | Product identifier |
| `name` | Text | Product name |
| `category` | Text | Category — must match exactly across rows |
| `price` | Decimal | Selling price (USD) |
| `cost` | Decimal | Unit cost |

> This file intentionally has more rows than `products.csv`. Peer rows (e.g. `SKU-P01`) exist as comparison benchmarks only. Minimum 3 peers per category recommended.

---

### `page_status.csv`
One row per product. Records the HTTP status of the product page.

| Column | Type | Description |
|---|---|---|
| `sku` | Text | Product identifier — must match `products.csv` |
| `page_url` | Text | Full product page URL |
| `http_status` | Integer | HTTP status: 200 = live, 301/302 = redirect, 404 = not found |

---

## Output

After all 5 steps run, the agent produces:

1. **Step trace cards** — a color-coded card per step showing status and exact detail message
2. **Launch decision banner** — the final Safe / Caution / Not Safe verdict in large text
3. **AI narrative** — a 3–4 sentence plain-English summary written by Claude, ready to share
4. **Audit summary** — metrics showing checks run, blocking issues, warnings, and decision

---

## Test Data

The included CSV files contain 9 product codes covering all 3 outcomes.

### ✅ Safe to Launch
| Code | Product | Why |
|---|---|---|
| `SKU-1001` | Bamboo Yoga Mat | All 4 checks pass — full stock, complete data, price in range, HTTP 200 |
| `SKU-1002` | Ceramic Tumbler Set | All 4 checks pass — full stock, complete data, price in range, HTTP 200 |
| `SKU-1003` | Stainless Steel Water Bottle | All 4 checks pass — full stock, complete data, price in range, HTTP 200 |

### ⚠️ Launch with Caution
| Code | Product | Warning |
|---|---|---|
| `SKU-2001` | Wireless Desk Lamp | Missing size chart attribute |
| `SKU-2002` | Trail Runner Pro X2 | Missing weight + HTTP 301 redirect |
| `SKU-2003` | Linen Summer Dress | Price 20% above category average |

### 🚫 Not Safe to Launch
| Code | Product | Blocking Issue |
|---|---|---|
| `SKU-3001` | Organic Cotton Hoodie | Low stock + 4 missing attributes + HTTP 404 |
| `SKU-3002` | Smart Indoor Planter | Price 142% above category average |
| `SKU-3003` | Leather Weekend Bag | Low stock + missing images + HTTP 404 |

**Recommended demo sequence:** `SKU-1001` → `SKU-2001` → `SKU-3001` — shows all 3 outcomes in under 2 minutes.

---

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### Install

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install streamlit pandas anthropic
```

### Run

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

If the command is not found:

```bash
python -m streamlit run app.py
```

To stop:

```bash
Ctrl + C
```

### Usage

1. Upload all 4 CSV files in the left sidebar
2. Paste your Anthropic API key in the sidebar
3. Type a product code into the input box (e.g. `SKU-1001`)
4. Click **Run Agent**
5. Watch the 5 steps execute and read the decision + narrative

---

## Analytics Behind Each Step

**Inventory** — grouped aggregation (`SUM` of `qty_on_hand` per SKU) compared against a configurable threshold. Equivalent to SQL `GROUP BY sku HAVING SUM(qty) < threshold`.

**Product Data** — completeness audit across 6 required attributes. Checks for nulls, empty strings, zero values, and boolean False. Severity scales with count of missing fields.

**Pricing** — category-relative deviation calculation. Filters peer products by category, computes mean price, measures percentage difference. Thresholds: ±15% = pass, ±25% = warn, beyond 25% = fail.

**Page Status** — HTTP response code evaluation. 200 = purchasable, 301/302 = redirect risk, 404 = hard block. In production this would be a live HTTP GET request.

**AI Synthesis** — all 4 results are structured into a prompt and sent to Claude. The model counts blocking vs warning issues, applies the decision rule, and writes a stakeholder-ready narrative in JSON format. Falls back to rule-based logic if the API is unavailable.

---

## Conclusion

ClearLaunch AI Agent replaces a fragmented, multi-team, multi-day manual process with a single autonomous workflow that runs in 30 seconds. It applies the same business rules consistently on every audit — no variation based on analyst experience or time pressure.

The AI narrative layer bridges raw data outputs and human decision-making. Instead of handing a product manager a table of check results, ClearLaunch gives them a sentence they can act on immediately.

**Built to demonstrate:** multi-step agent architecture, pandas data processing, LLM API integration, structured prompt engineering, Streamlit UI development, and enterprise-grade business logic — applied to a real problem that retail companies face every day.

---

*Built with Python · Streamlit · pandas · Anthropic Claude API*
