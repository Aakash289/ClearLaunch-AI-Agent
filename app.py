"""
ClearLaunch AI Agent
================================
A 5-step AI agent that audits any SKU against 4 CSV datasets
and produces a SAFE TO LAUNCH / LAUNCH WITH CAUTION / NOT SAFE TO LAUNCH
decision with a Claude-generated plain-English narrative.

How to run:
    pip install streamlit pandas anthropic
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import anthropic
import os

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ClearLaunch AI Agent",
    page_icon="◈",
    layout="wide",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — navy/slate professional theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Main background — deep navy */
    .stApp { background-color: #0f1623; }

    /* Sidebar background */
    [data-testid="stSidebar"] { background-color: #151e2d !important; border-right: 1px solid #1e2d45; }
    [data-testid="stSidebar"] * { color: #94a3b8 !important; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 { color: #e2e8f0 !important; }

    /* Block container padding */
    .block-container { padding-top: 2.5rem; padding-bottom: 2rem; }

    /* Main text color */
    .stMarkdown, .stMarkdown p, h1, h2, h3, h4 { color: #e2e8f0; }

    /* Step cards — dark surface */
    .step-card {
        background: #1a2335;
        border: 1px solid #1e2d45;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
        border-left: 4px solid #1e2d45;
        font-family: 'Inter', sans-serif;
    }
    .step-card.pass  {
        border-left-color: #10b981;
        background: #0d1f1a;
        border-color: #10b98130;
    }
    .step-card.warn  {
        border-left-color: #f59e0b;
        background: #1c1609;
        border-color: #f59e0b30;
    }
    .step-card.fail  {
        border-left-color: #ef4444;
        background: #1c0a0a;
        border-color: #ef444430;
    }
    .step-card.running {
        border-left-color: #3b82f6;
        background: #0d1627;
        border-color: #3b82f630;
    }

    .step-title {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 5px;
        color: #e2e8f0;
        letter-spacing: 0.01em;
    }
    .step-detail {
        font-size: 12px;
        color: #64748b;
        font-family: 'SF Mono', 'Fira Code', monospace;
        line-height: 1.5;
    }
    .step-card.pass  .step-detail { color: #34d399; }
    .step-card.warn  .step-detail { color: #fbbf24; }
    .step-card.fail  .step-detail { color: #f87171; }
    .step-card.running .step-detail { color: #60a5fa; }

    /* Verdict boxes */
    .verdict-safe {
        background: #0a1f16;
        border: 1.5px solid #10b981;
        border-radius: 12px;
        padding: 22px 28px;
    }
    .verdict-caution {
        background: #1a1305;
        border: 1.5px solid #f59e0b;
        border-radius: 12px;
        padding: 22px 28px;
    }
    .verdict-unsafe {
        background: #1a0808;
        border: 1.5px solid #ef4444;
        border-radius: 12px;
        padding: 22px 28px;
    }

    /* Narrative box */
    .narrative-box {
        background: #1a2335;
        border: 1px solid #1e2d45;
        border-radius: 10px;
        padding: 20px 24px;
        margin-top: 14px;
    }
    .narrative-label {
        font-size: 10px;
        font-family: monospace;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #475569;
        margin-bottom: 10px;
    }
    .narrative-text {
        font-size: 14px;
        line-height: 1.85;
        color: #94a3b8;
    }

    /* Streamlit metric override */
    [data-testid="stMetricValue"] { color: #e2e8f0 !important; font-size: 22px !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; }

    /* Input field */
    .stTextInput input {
        background: #1a2335 !important;
        border: 1px solid #1e2d45 !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px #3b82f620 !important;
    }

    /* Button */
    .stButton button {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
    }
    .stButton button:hover { background: #2563eb !important; }

    /* Code block */
    .stCode { background: #1a2335 !important; }

    /* Divider */
    hr { border-color: #1e2d45 !important; }

    /* Info box */
    .stAlert { background: #1a2335 !important; border-color: #1e2d45 !important; color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR — File uploads + API key
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ClearLaunch AI Agent")
    st.markdown("Upload your 4 CSV files, enter your Claude API key, then enter a product code to audit.")

    st.markdown("---")
    st.markdown("### API Key")
    api_key = st.text_input("Anthropic API Key", type="password",
                            placeholder="sk-ant-...",
                            help="Get yours at console.anthropic.com")

    st.markdown("---")
    st.markdown("### Upload CSV Files")

    inv_file  = st.file_uploader("inventory.csv",    type="csv")
    prod_file = st.file_uploader("products.csv",     type="csv")
    price_file= st.file_uploader("pricing.csv",      type="csv")
    page_file = st.file_uploader("page_status.csv",  type="csv")

    st.markdown("---")
    st.markdown("#### Expected columns")
    with st.expander("inventory.csv"):
        st.code("sku, warehouse_id, qty_on_hand, launch_threshold")
    with st.expander("products.csv"):
        st.code("sku, name, category, price, description,\nimage_count, has_size_chart, weight_kg")
    with st.expander("pricing.csv"):
        st.code("sku, name, category, price, cost")
    with st.expander("page_status.csv"):
        st.code("sku, page_url, http_status")


# ─────────────────────────────────────────────
# HELPER — load CSVs
# ─────────────────────────────────────────────
@st.cache_data
def load_csv(file):
    return pd.read_csv(file)


# ─────────────────────────────────────────────
# AGENT STEP FUNCTIONS
# Each returns a dict:
#   { status: "pass"|"warn"|"fail", detail: str, data: dict }
# ─────────────────────────────────────────────

def step_inventory(sku: str, df: pd.DataFrame) -> dict:
    """
    Step 1 — Inventory Check
    -------------------------
    Groups inventory.csv by SKU, sums qty_on_hand across all warehouses,
    and compares the total to the launch_threshold.

    Business rule:
      total stock < launch_threshold  → FAIL (blocking)
      total stock >= launch_threshold → PASS
    """
    rows = df[df["sku"] == sku]
    if rows.empty:
        return {"status": "fail",
                "detail": f"SKU {sku} not found in inventory.csv",
                "data": {}}

    total_stock     = int(rows["qty_on_hand"].sum())
    threshold       = int(rows["launch_threshold"].iloc[0])
    warehouses      = rows["warehouse_id"].tolist()
    per_wh          = dict(zip(rows["warehouse_id"], rows["qty_on_hand"].astype(int)))
    status          = "pass" if total_stock >= threshold else "fail"

    detail = (f"{total_stock} units across {warehouses} — "
              f"{'above' if status == 'pass' else 'BELOW'} threshold of {threshold}")

    return {"status": status, "detail": detail,
            "data": {"total_stock": total_stock, "threshold": threshold,
                     "warehouses": per_wh}}


def step_product_data(sku: str, df: pd.DataFrame) -> dict:
    """
    Step 2 — Product Data Validation
    ----------------------------------
    Checks every required attribute in products.csv for the SKU.
    Required fields: name, price, description, image_count > 0,
                     has_size_chart == True, weight_kg present.

    Business rule:
      2+ missing fields → FAIL (blocking)
      1 missing field   → WARN
      0 missing fields  → PASS
    """
    row = df[df["sku"] == sku]
    if row.empty:
        return {"status": "fail",
                "detail": f"SKU {sku} not found in products.csv",
                "data": {}}

    r        = row.iloc[0]
    missing  = []

    if pd.isna(r.get("name")) or str(r.get("name", "")).strip() == "":
        missing.append("name")
    if pd.isna(r.get("description")) or str(r.get("description", "")).strip() == "":
        missing.append("description")
    if pd.isna(r.get("image_count")) or int(r.get("image_count", 0)) == 0:
        missing.append("images (0 uploaded)")
    if str(r.get("has_size_chart", "False")).strip().lower() in ("false", "0", ""):
        missing.append("size chart")
    if pd.isna(r.get("weight_kg")) or str(r.get("weight_kg", "")).strip() == "":
        missing.append("weight/dimensions")

    if len(missing) == 0:
        status = "pass"
        detail = "All required attributes populated ✓"
    elif len(missing) == 1:
        status = "warn"
        detail = f"Missing 1 attribute: {missing[0]}"
    else:
        status = "fail"
        detail = f"Missing {len(missing)} attributes: {', '.join(missing)}"

    return {"status": status, "detail": detail,
            "data": {"missing": missing, "product_name": r.get("name", sku),
                     "category": r.get("category", ""), "price": r.get("price", 0)}}


def step_pricing(sku: str, df: pd.DataFrame) -> dict:
    """
    Step 3 — Pricing Conflict Scan
    --------------------------------
    Finds the SKU's price, computes the average price of OTHER SKUs in the
    same category, and calculates % deviation.

    Also checks for near-identical SKUs priced significantly lower
    (potential sales cannibalization).

    Business rules:
      deviation > 25%  → FAIL  (blocking — severely overpriced)
      deviation 15–25% → WARN  (review recommended)
      deviation < 15%  → PASS
    """
    row = df[df["sku"] == sku]
    if row.empty:
        return {"status": "warn",
                "detail": f"SKU {sku} not found in pricing.csv — cannot validate price",
                "data": {}}

    r            = row.iloc[0]
    sku_price    = float(r["price"])
    category     = r["category"]

    # Category peers (exclude current SKU)
    peers        = df[(df["category"] == category) & (df["sku"] != sku)]
    cat_avg      = float(peers["price"].mean()) if not peers.empty else sku_price
    deviation    = ((sku_price - cat_avg) / cat_avg) * 100

    # Cheaper conflict SKUs in same category
    conflicts    = peers[peers["price"] < sku_price * 0.85][["name", "price"]].to_dict("records")

    if abs(deviation) > 25:
        status = "fail"
    elif abs(deviation) > 15:
        status = "warn"
    else:
        status = "pass"

    conflict_note = ""
    if conflicts:
        conflict_note = f" | Cheaper alternatives: {', '.join([c['name'] + ' @ $' + str(c['price']) for c in conflicts[:2]])}"

    detail = (f"${sku_price:.2f} vs category avg ${cat_avg:.2f} "
              f"({'+' if deviation >= 0 else ''}{deviation:.1f}%){conflict_note}")

    return {"status": status, "detail": detail,
            "data": {"sku_price": sku_price, "cat_avg": round(cat_avg, 2),
                     "deviation_pct": round(deviation, 1), "conflicts": conflicts}}


def step_page_status(sku: str, df: pd.DataFrame) -> dict:
    """
    Step 4 — Page URL Verification
    --------------------------------
    Checks page_status.csv for the SKU's product page HTTP status.
    200 = live and purchasable.
    Anything else (404, 301, missing) = problem.

    Business rule:
      HTTP 200          → PASS
      HTTP 301 redirect → WARN (may resolve but not guaranteed)
      HTTP 404 / other  → FAIL (blocking — product cannot be purchased)
      SKU not in file   → FAIL
    """
    row = df[df["sku"] == sku]
    if row.empty:
        return {"status": "fail",
                "detail": f"SKU {sku} not found in page_status.csv — no URL on record",
                "data": {}}

    r      = row.iloc[0]
    code   = int(r["http_status"])
    url    = r.get("page_url", "unknown")

    if code == 200:
        status = "pass"
        detail = f"HTTP {code} — page live and indexable at {url} ✓"
    elif code in (301, 302):
        status = "warn"
        detail = f"HTTP {code} — redirect detected at {url} — verify destination"
    else:
        status = "fail"
        detail = f"HTTP {code} — page not accessible at {url} ✗"

    return {"status": status, "detail": detail,
            "data": {"http_status": code, "url": url}}


def step_ai_decision(sku: str, product_name: str, results: list, api_key: str) -> dict:
    """
    Step 5 — AI Decision + Narrative
    ----------------------------------
    Sends all 4 check results to Claude via the Anthropic API.
    Claude:
      1. Counts blocking (fail) vs warning issues
      2. Makes the final SAFE TO LAUNCH / LAUNCH WITH CAUTION / NOT SAFE TO LAUNCH decision
      3. Writes a 3–4 sentence plain-English briefing for the product manager

    Prompt engineering:
      - Structured input (each check result as labelled text)
      - Explicit output format requested (JSON)
      - Temperature kept default for analytical consistency
    """
    step_labels = [
        "Inventory Check",
        "Product Data Validation",
        "Pricing Conflict Scan",
        "Page URL Verification",
    ]

    summary_lines = []
    for i, r in enumerate(results):
        summary_lines.append(
            f"{step_labels[i]}: {r['status'].upper()} — {r['detail']}"
        )
    checks_text = "\n".join(summary_lines)

    blocking = [r for r in results if r["status"] == "fail"]
    warnings = [r for r in results if r["status"] == "warn"]

    prompt = f"""You are a retail merchandising analyst reviewing a product launch audit.

Product: {product_name} ({sku})

Audit results:
{checks_text}

Blocking issues (fail): {len(blocking)}
Warnings: {len(warnings)}

Based on these results:
- If there are ANY blocking issues → decision is NOT SAFE TO LAUNCH
- If there are warnings but no blocking issues → decision is LAUNCH WITH CAUTION
- If all checks passed → decision is SAFE TO LAUNCH

Respond in this exact JSON format (no markdown, no preamble):
{{
  "decision": "SAFE TO LAUNCH" | "LAUNCH WITH CAUTION" | "NOT SAFE TO LAUNCH",
  "narrative": "3-4 sentence plain-English summary for the product manager. Be specific about what passed and what failed. Name the exact issues. Tell them what needs to happen next."
}}"""

    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model      = "claude-sonnet-4-20250514",
            max_tokens = 1000,
            messages   = [{"role": "user", "content": prompt}],
        )
        import json
        text   = response.content[0].text.strip()
        parsed = json.loads(text)
        return {"decision": parsed["decision"], "narrative": parsed["narrative"], "error": None}

    except Exception as e:
        # Fallback rule-based decision if API fails
        if blocking:
            decision = "NOT SAFE TO LAUNCH"
        elif warnings:
            decision = "LAUNCH WITH CAUTION"
        else:
            decision = "SAFE TO LAUNCH"

        return {
            "decision":  decision,
            "narrative": f"API narrative unavailable ({e}). Decision based on rule engine: "
                         f"{len(blocking)} blocking issues, {len(warnings)} warnings.",
            "error":     str(e),
        }


# ─────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────

STATUS_ICON  = {"pass": "◆", "warn": "◆", "fail": "◆", "running": "◆"}
STATUS_LABEL = {"pass": "PASS", "warn": "WARNING", "fail": "FAIL", "running": "RUNNING..."}
STATUS_COLOR = {"pass": "#10b981", "warn": "#f59e0b", "fail": "#ef4444", "running": "#3b82f6"}

def render_step(num: int, title: str, status: str, detail: str):
    label = STATUS_LABEL.get(status, status.upper())
    color = STATUS_COLOR.get(status, "#64748b")
    st.markdown(f"""
    <div class="step-card {status}">
        <div class="step-title">
            <span style="color:{color};margin-right:8px;font-size:10px">◆</span>
            Step {num} — {title}
            <span style="float:right;font-size:11px;font-family:monospace;
                         color:{color};letter-spacing:0.08em">{label}</span>
        </div>
        <div class="step-detail">{detail}</div>
    </div>
    """, unsafe_allow_html=True)


def render_verdict(decision: str, narrative: str):
    cls_map   = {
        "SAFE TO LAUNCH":      "verdict-safe",
        "LAUNCH WITH CAUTION": "verdict-caution",
        "NOT SAFE TO LAUNCH":  "verdict-unsafe",
    }
    color_map = {
        "SAFE TO LAUNCH":      "#10b981",
        "LAUNCH WITH CAUTION": "#f59e0b",
        "NOT SAFE TO LAUNCH":  "#ef4444",
    }
    cls   = cls_map.get(decision, "verdict-caution")
    color = color_map.get(decision, "#f59e0b")

    st.markdown(f"""
    <div class="{cls}">
        <div style="font-size:10px;font-family:monospace;text-transform:uppercase;
                    letter-spacing:0.12em;color:{color};opacity:0.7;margin-bottom:8px">
            Launch Decision
        </div>
        <div style="font-size:22px;font-weight:700;color:{color};letter-spacing:0.01em">
            {decision}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="narrative-box">
        <div class="narrative-label">AI Narrative — Claude's Assessment</div>
        <div class="narrative-text">{narrative}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────

st.markdown("# ClearLaunch AI Agent")
st.markdown(
    "Enter a product code to run a 5-step autonomous audit. "
    "The agent checks inventory, product data, pricing, and page status — "
    "then Claude writes the Safe to Launch / Launch with Caution / Not Safe to Launch decision."
)
st.markdown("---")

# Check all files uploaded
files_ready = all([inv_file, prod_file, price_file, page_file])
if not files_ready:
    st.info("👈 Upload all 4 CSV files in the sidebar to get started.")
    st.stop()

# Load dataframes
df_inv   = load_csv(inv_file)
df_prod  = load_csv(prod_file)
df_price = load_csv(price_file)
df_page  = load_csv(page_file)

# Show available SKUs
all_skus = sorted(df_inv["sku"].unique().tolist())
st.markdown("**Available SKUs in your data:**")
st.code("  ".join(all_skus))

# SKU input
col1, col2 = st.columns([3, 1])
with col1:
    sku_input = st.text_input(
        "Enter product code to audit",
        placeholder="e.g. SKU-9981",
        label_visibility="collapsed",
    )
with col2:
    run = st.button("▶ Run Agent", use_container_width=True, type="primary")

st.markdown("---")

# ── RUN THE AGENT ──
if run and sku_input:
    sku = sku_input.strip().upper()
    st.markdown(f"### Auditing `{sku}`")

    # Find product name for display
    prod_row = df_prod[df_prod["sku"] == sku]
    product_name = prod_row.iloc[0]["name"] if not prod_row.empty else sku

    st.markdown(f"**Product:** {product_name}")
    st.markdown("---")

    step_results = []
    placeholders = [st.empty() for _ in range(5)]

    # ── STEP 1 — Inventory ──
    placeholders[0].markdown("""
    <div class="step-card running">
        <div class="step-title"><span style="color:#3b82f6;margin-right:8px;font-size:10px">◆</span>Step 1 — Inventory Check <span style="float:right;font-size:11px;font-family:monospace;color:#3b82f6;letter-spacing:0.08em">RUNNING...</span></div>
        <div class="step-detail">Querying warehouse stock vs launch threshold...</div>
    </div>""", unsafe_allow_html=True)

    r1 = step_inventory(sku, df_inv)
    step_results.append(r1)
    with placeholders[0]:
        render_step(1, "Inventory Check", r1["status"], r1["detail"])

    # ── STEP 2 — Product Data ──
    placeholders[1].markdown("""
    <div class="step-card running">
        <div class="step-title"><span style="color:#3b82f6;margin-right:8px;font-size:10px">◆</span>Step 2 — Product Data Validation <span style="float:right;font-size:11px;font-family:monospace;color:#3b82f6;letter-spacing:0.08em">RUNNING...</span></div>
        <div class="step-detail">Auditing required product attributes...</div>
    </div>""", unsafe_allow_html=True)

    r2 = step_product_data(sku, df_prod)
    step_results.append(r2)
    with placeholders[1]:
        render_step(2, "Product Data Validation", r2["status"], r2["detail"])

    # ── STEP 3 — Pricing ──
    placeholders[2].markdown("""
    <div class="step-card running">
        <div class="step-title"><span style="color:#3b82f6;margin-right:8px;font-size:10px">◆</span>Step 3 — Pricing Conflict Scan <span style="float:right;font-size:11px;font-family:monospace;color:#3b82f6;letter-spacing:0.08em">RUNNING...</span></div>
        <div class="step-detail">Comparing price vs category average and similar products...</div>
    </div>""", unsafe_allow_html=True)

    r3 = step_pricing(sku, df_price)
    step_results.append(r3)
    with placeholders[2]:
        render_step(3, "Pricing Conflict Scan", r3["status"], r3["detail"])

    # ── STEP 4 — Page Status ──
    placeholders[3].markdown("""
    <div class="step-card running">
        <div class="step-title"><span style="color:#3b82f6;margin-right:8px;font-size:10px">◆</span>Step 4 — Page URL Verification <span style="float:right;font-size:11px;font-family:monospace;color:#3b82f6;letter-spacing:0.08em">RUNNING...</span></div>
        <div class="step-detail">Checking product page HTTP status...</div>
    </div>""", unsafe_allow_html=True)

    r4 = step_page_status(sku, df_page)
    step_results.append(r4)
    with placeholders[3]:
        render_step(4, "Page URL Verification", r4["status"], r4["detail"])

    # ── STEP 5 — AI Decision ──
    placeholders[4].markdown("""
    <div class="step-card running">
        <div class="step-title"><span style="color:#3b82f6;margin-right:8px;font-size:10px">◆</span>Step 5 — AI Decision Engine <span style="float:right;font-size:11px;font-family:monospace;color:#3b82f6;letter-spacing:0.08em">RUNNING...</span></div>
        <div class="step-detail">Sending results to Claude — generating decision and narrative...</div>
    </div>""", unsafe_allow_html=True)

    if not api_key:
        ai_result = {
            "decision":  "NOT SAFE TO LAUNCH" if any(r["status"] == "fail" for r in step_results) else
                         "LAUNCH WITH CAUTION" if any(r["status"] == "warn" for r in step_results) else "SAFE TO LAUNCH",
            "narrative": "Enter your Anthropic API key in the sidebar to get Claude's written narrative.",
            "error":     "No API key provided",
        }
    else:
        ai_result = step_ai_decision(sku, product_name, step_results, api_key)

    blocking_count = sum(1 for r in step_results if r["status"] == "fail")
    warn_count     = sum(1 for r in step_results if r["status"] == "warn")
    step5_detail   = f"Decision: {ai_result['decision']} — {blocking_count} blocking, {warn_count} warnings"
    step5_status   = "fail" if ai_result["decision"] == "NOT SAFE TO LAUNCH" else \
                     "warn" if ai_result["decision"] == "LAUNCH WITH CAUTION" else "pass"

    with placeholders[4]:
        render_step(5, "AI Decision Engine", step5_status, step5_detail)

    # ── VERDICT ──
    st.markdown("---")
    render_verdict(ai_result["decision"], ai_result["narrative"])

    # ── SUMMARY METRICS ──
    st.markdown("---")
    st.markdown("#### Audit summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Checks run",     "4")
    c2.metric("Blocking issues", blocking_count,  delta=f"{blocking_count} fail",  delta_color="inverse")
    c3.metric("Warnings",        warn_count,       delta=f"{warn_count} warn",      delta_color="off")
    c4.metric("Decision",        ai_result["decision"])

elif run and not sku_input:
    st.warning("Please enter a SKU first.")
