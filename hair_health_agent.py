"""
AI Hair Health & Diet Tracker
- Generates a personalized AI hair-nutrition plan (Groq)
- Logs daily food intake (seeds, nuts, fish, greens …)
- Tracks Biotin, Zinc, Iron, Protein, Omega-3, Vit-D/E/C/A, Selenium
- Shows weekly & monthly progress with charts
- Persists all data to hair_health_data.json
"""

import time
import json
import os
from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from agno.agent import Agent
from agno.models.groq import Groq

# ─────────────────────────────────────────
#  Config
# ─────────────────────────────────────────
DATA_FILE = "hair_health_data.json"

st.set_page_config(
    page_title="🧴 Hair Health Diet Tracker",
    page_icon="💆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main { padding: 1.5rem; }
.stButton>button { width:100%; border-radius:6px; height:3em; }
.metric-card {
    background: linear-gradient(135deg,#1a1a2e,#16213e);
    padding:1rem; border-radius:10px; text-align:center;
    border:1px solid #0f3460; margin-bottom:0.5rem;
}
.nutrient-ok   { color:#48bb78; font-weight:700; }
.nutrient-warn { color:#f6ad55; font-weight:700; }
.nutrient-low  { color:#fc8181; font-weight:700; }
div[data-testid="stExpander"] div[role="button"] p { font-size:1.1rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  Reference data
# ─────────────────────────────────────────
HAIR_NUTRIENTS: dict[str, dict] = {
    "Biotin (mcg)":    {"daily_goal": 100,  "unit": "mcg", "desc": "Keratin production & hair growth"},
    "Zinc (mg)":       {"daily_goal": 11,   "unit": "mg",  "desc": "Hair follicle repair & growth"},
    "Iron (mg)":       {"daily_goal": 18,   "unit": "mg",  "desc": "Carries oxygen to follicles"},
    "Protein (g)":     {"daily_goal": 65,   "unit": "g",   "desc": "Hair is ~95 % keratin (protein)"},
    "Vitamin D (IU)":  {"daily_goal": 800,  "unit": "IU",  "desc": "Stimulates follicle cycling"},
    "Vitamin E (mg)":  {"daily_goal": 15,   "unit": "mg",  "desc": "Scalp antioxidant protection"},
    "Omega-3 (g)":     {"daily_goal": 1.6,  "unit": "g",   "desc": "Reduces scalp inflammation"},
    "Selenium (mcg)":  {"daily_goal": 55,   "unit": "mcg", "desc": "Prevents dandruff & oxidative stress"},
    "Vitamin C (mg)":  {"daily_goal": 90,   "unit": "mg",  "desc": "Collagen + iron-absorption booster"},
    "Vitamin A (mcg)": {"daily_goal": 900,  "unit": "mcg", "desc": "Sebum: keeps scalp moisturised"},
}

# Per-serving nutrient values (keys must match HAIR_NUTRIENTS)
HAIR_FOODS: dict[str, dict] = {
    "Eggs – 1 large": {
        "Biotin (mcg)":10,"Zinc (mg)":0.6,"Iron (mg)":0.6,"Protein (g)":6,
        "Vitamin D (IU)":44,"Vitamin E (mg)":0.5,"Omega-3 (g)":0.1,
        "Selenium (mcg)":15,"Vitamin C (mg)":0,"Vitamin A (mcg)":75,
    },
    "Salmon – 100 g": {
        "Biotin (mcg)":5,"Zinc (mg)":0.4,"Iron (mg)":0.8,"Protein (g)":25,
        "Vitamin D (IU)":570,"Vitamin E (mg)":3.5,"Omega-3 (g)":2.3,
        "Selenium (mcg)":36,"Vitamin C (mg)":3,"Vitamin A (mcg)":50,
    },
    "Sardines – 100 g": {
        "Biotin (mcg)":5,"Zinc (mg)":1.3,"Iron (mg)":2.9,"Protein (g)":25,
        "Vitamin D (IU)":270,"Vitamin E (mg)":2.0,"Omega-3 (g)":1.5,
        "Selenium (mcg)":52,"Vitamin C (mg)":0,"Vitamin A (mcg)":16,
    },
    "Chicken Breast – 100 g": {
        "Biotin (mcg)":7,"Zinc (mg)":1.0,"Iron (mg)":1.0,"Protein (g)":31,
        "Vitamin D (IU)":10,"Vitamin E (mg)":0.3,"Omega-3 (g)":0.1,
        "Selenium (mcg)":27,"Vitamin C (mg)":0,"Vitamin A (mcg)":6,
    },
    "Pumpkin Seeds – 30 g": {
        "Biotin (mcg)":8,"Zinc (mg)":2.2,"Iron (mg)":2.5,"Protein (g)":9,
        "Vitamin D (IU)":0,"Vitamin E (mg)":2.6,"Omega-3 (g)":0.05,
        "Selenium (mcg)":2,"Vitamin C (mg)":0,"Vitamin A (mcg)":0,
    },
    "Sunflower Seeds – 30 g": {
        "Biotin (mcg)":7,"Zinc (mg)":1.5,"Iron (mg)":1.5,"Protein (g)":5.5,
        "Vitamin D (IU)":0,"Vitamin E (mg)":11,"Omega-3 (g)":0.03,
        "Selenium (mcg)":22,"Vitamin C (mg)":0,"Vitamin A (mcg)":0,
    },
    "Flaxseeds – 15 g (1 tbsp)": {
        "Biotin (mcg)":2,"Zinc (mg)":0.7,"Iron (mg)":0.7,"Protein (g)":2.7,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.3,"Omega-3 (g)":3.5,
        "Selenium (mcg)":3,"Vitamin C (mg)":0,"Vitamin A (mcg)":0,
    },
    "Chia Seeds – 15 g (1 tbsp)": {
        "Biotin (mcg)":2,"Zinc (mg)":0.5,"Iron (mg)":1.0,"Protein (g)":2.5,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.1,"Omega-3 (g)":2.6,
        "Selenium (mcg)":1,"Vitamin C (mg)":0.5,"Vitamin A (mcg)":0,
    },
    "Walnuts – 30 g (handful)": {
        "Biotin (mcg)":9,"Zinc (mg)":0.9,"Iron (mg)":0.8,"Protein (g)":4.3,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.7,"Omega-3 (g)":2.5,
        "Selenium (mcg)":1.2,"Vitamin C (mg)":0.4,"Vitamin A (mcg)":0,
    },
    "Almonds – 30 g (handful)": {
        "Biotin (mcg)":15,"Zinc (mg)":0.9,"Iron (mg)":1.1,"Protein (g)":6,
        "Vitamin D (IU)":0,"Vitamin E (mg)":7.3,"Omega-3 (g)":0.0,
        "Selenium (mcg)":1.2,"Vitamin C (mg)":0,"Vitamin A (mcg)":0,
    },
    "Brazil Nuts – 3 nuts (30 g)": {
        "Biotin (mcg)":3,"Zinc (mg)":1.2,"Iron (mg)":0.7,"Protein (g)":4.1,
        "Vitamin D (IU)":0,"Vitamin E (mg)":1.6,"Omega-3 (g)":0.1,
        "Selenium (mcg)":544,"Vitamin C (mg)":0.2,"Vitamin A (mcg)":0,
    },
    "Spinach – 100 g": {
        "Biotin (mcg)":7,"Zinc (mg)":0.5,"Iron (mg)":2.7,"Protein (g)":2.9,
        "Vitamin D (IU)":0,"Vitamin E (mg)":2.0,"Omega-3 (g)":0.1,
        "Selenium (mcg)":1,"Vitamin C (mg)":28,"Vitamin A (mcg)":469,
    },
    "Kale – 100 g": {
        "Biotin (mcg)":0.5,"Zinc (mg)":0.4,"Iron (mg)":1.5,"Protein (g)":4.3,
        "Vitamin D (IU)":0,"Vitamin E (mg)":1.5,"Omega-3 (g)":0.1,
        "Selenium (mcg)":0.9,"Vitamin C (mg)":93,"Vitamin A (mcg)":241,
    },
    "Sweet Potato – 1 medium": {
        "Biotin (mcg)":4,"Zinc (mg)":0.3,"Iron (mg)":0.7,"Protein (g)":2,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.3,"Omega-3 (g)":0.0,
        "Selenium (mcg)":0.2,"Vitamin C (mg)":20,"Vitamin A (mcg)":961,
    },
    "Avocado – half": {
        "Biotin (mcg)":6,"Zinc (mg)":0.4,"Iron (mg)":0.3,"Protein (g)":1.5,
        "Vitamin D (IU)":0,"Vitamin E (mg)":2.1,"Omega-3 (g)":0.1,
        "Selenium (mcg)":0.4,"Vitamin C (mg)":8,"Vitamin A (mcg)":7,
    },
    "Greek Yogurt – 150 g": {
        "Biotin (mcg)":4,"Zinc (mg)":0.8,"Iron (mg)":0.1,"Protein (g)":15,
        "Vitamin D (IU)":100,"Vitamin E (mg)":0.1,"Omega-3 (g)":0.1,
        "Selenium (mcg)":9,"Vitamin C (mg)":0,"Vitamin A (mcg)":20,
    },
    "Lentils – 100 g cooked": {
        "Biotin (mcg)":5,"Zinc (mg)":1.3,"Iron (mg)":3.3,"Protein (g)":9,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.1,"Omega-3 (g)":0.1,
        "Selenium (mcg)":2.8,"Vitamin C (mg)":1.5,"Vitamin A (mcg)":1,
    },
    "Chickpeas – 100 g cooked": {
        "Biotin (mcg)":4,"Zinc (mg)":1.5,"Iron (mg)":2.9,"Protein (g)":9,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.4,"Omega-3 (g)":0.05,
        "Selenium (mcg)":3,"Vitamin C (mg)":1.3,"Vitamin A (mcg)":1,
    },
    "Oysters – 100 g": {
        "Biotin (mcg)":10,"Zinc (mg)":39,"Iron (mg)":5.6,"Protein (g)":9,
        "Vitamin D (IU)":320,"Vitamin E (mg)":1.7,"Omega-3 (g)":0.7,
        "Selenium (mcg)":77,"Vitamin C (mg)":3.5,"Vitamin A (mcg)":24,
    },
    "Edamame / Soybeans – 100 g": {
        "Biotin (mcg)":8,"Zinc (mg)":0.9,"Iron (mg)":2.3,"Protein (g)":11,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.4,"Omega-3 (g)":0.3,
        "Selenium (mcg)":1.5,"Vitamin C (mg)":6.1,"Vitamin A (mcg)":9,
    },
    "Berries / Strawberries – 100 g": {
        "Biotin (mcg)":1,"Zinc (mg)":0.1,"Iron (mg)":0.4,"Protein (g)":0.7,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.3,"Omega-3 (g)":0.1,
        "Selenium (mcg)":0.4,"Vitamin C (mg)":59,"Vitamin A (mcg)":1,
    },
    "Carrot – 1 medium": {
        "Biotin (mcg)":2,"Zinc (mg)":0.2,"Iron (mg)":0.3,"Protein (g)":0.6,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.4,"Omega-3 (g)":0.0,
        "Selenium (mcg)":0.1,"Vitamin C (mg)":5.9,"Vitamin A (mcg)":835,
    },
    "Tofu – 100 g": {
        "Biotin (mcg)":3,"Zinc (mg)":0.8,"Iron (mg)":2.7,"Protein (g)":8,
        "Vitamin D (IU)":0,"Vitamin E (mg)":0.1,"Omega-3 (g)":0.3,
        "Selenium (mcg)":8.9,"Vitamin C (mg)":0,"Vitamin A (mcg)":0,
    },
}

FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

# ─────────────────────────────────────────
#  Data persistence helpers
# ─────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"daily_logs": {}, "hair_profile": {}, "ai_plan": ""}


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ─────────────────────────────────────────
#  Nutrient calculation helpers
# ─────────────────────────────────────────
def calc_totals(food_list: list[str]) -> dict[str, float]:
    totals = {n: 0.0 for n in HAIR_NUTRIENTS}
    for food in food_list:
        if food in HAIR_FOODS:
            for nutrient, val in HAIR_FOODS[food].items():
                totals[nutrient] = totals.get(nutrient, 0.0) + val
    return totals


def pct_goal(actual: float, goal: float) -> float:
    return min(round(actual / goal * 100, 1), 999.0) if goal else 0.0


def status_color(pct: float) -> str:
    if pct >= 80:
        return "nutrient-ok"
    elif pct >= 50:
        return "nutrient-warn"
    return "nutrient-low"


# ─────────────────────────────────────────
#  Groq helpers
# ─────────────────────────────────────────
def get_working_model(api_key: str):
    for model_id in FALLBACK_MODELS:
        try:
            m = Groq(id=model_id, api_key=api_key)
            Agent(model=m).run("hi")
            return m, model_id
        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err.lower():
                time.sleep(2)
                continue
            elif "404" in err or "model_not_found" in err.lower():
                continue
            else:
                raise
    return None, None


def run_with_retry(agent, prompt, retries=3, wait=20):
    for attempt in range(retries):
        try:
            return agent.run(prompt)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < retries - 1:
                    st.warning(f"⏳ Rate limit – retrying in {wait}s (attempt {attempt+1}/{retries})…")
                    time.sleep(wait)
                else:
                    raise
            else:
                raise


# ─────────────────────────────────────────
#  UI helpers
# ─────────────────────────────────────────
def render_nutrient_gauges(totals: dict, title: str = "Today's Nutrient Progress"):
    st.markdown(f"### {title}")
    cols = st.columns(5)
    for i, (nutrient, info) in enumerate(HAIR_NUTRIENTS.items()):
        actual = totals.get(nutrient, 0)
        goal   = info["daily_goal"]
        pct    = pct_goal(actual, goal)
        cls    = status_color(pct)
        with cols[i % 5]:
            st.markdown(
                f"""<div class="metric-card">
                    <p style="font-size:0.75rem;color:#a0aec0;margin:0">{nutrient}</p>
                    <p class="{cls}" style="font-size:1.3rem;margin:4px 0">{actual:.1f}</p>
                    <p style="font-size:0.7rem;color:#a0aec0;margin:0">/ {goal} {info['unit']}</p>
                    <p style="font-size:0.85rem;margin:0">{"✅" if pct>=80 else "⚠️" if pct>=50 else "❌"} {pct}%</p>
                </div>""",
                unsafe_allow_html=True,
            )


def render_radar_chart(totals: dict, day_label: str = "Today"):
    nutrients = list(HAIR_NUTRIENTS.keys())
    actual_pcts = [pct_goal(totals.get(n, 0), HAIR_NUTRIENTS[n]["daily_goal"]) for n in nutrients]
    goal_pcts   = [100] * len(nutrients)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=goal_pcts,  theta=nutrients, fill="toself",
                                  name="Goal (100%)", line_color="#4299e1", opacity=0.3))
    fig.add_trace(go.Scatterpolar(r=actual_pcts, theta=nutrients, fill="toself",
                                  name=day_label, line_color="#68d391"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 120])),
        showlegend=True, height=380,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────
def main():
    app_data = load_data()

    # ── Sidebar ──────────────────────────
    with st.sidebar:
        st.title("💆 Hair Health Tracker")
        st.markdown("---")
        groq_api_key = st.text_input("🔑 Groq API Key", type="password",
                                     help="Get yours at console.groq.com/keys")
        if not groq_api_key:
            st.warning("Enter your Groq API key to continue.")
            st.markdown("[Get key →](https://console.groq.com/keys)")
            st.stop()

        st.success("API key set ✓")
        st.markdown("---")

        # Hair profile
        st.subheader("👤 Your Hair Profile")
        hair_type    = st.selectbox("Hair Type", ["Straight","Wavy","Curly","Coily"])
        hair_concern = st.multiselect("Main Concerns",
            ["Hair thinning","Hair fall","Receding hairline","Dryness/frizz",
             "Dandruff","Slow growth","Premature graying"],
            default=["Hair thinning","Receding hairline"])
        age   = st.number_input("Age", 10, 80, 28)
        sex   = st.selectbox("Sex", ["Male","Female","Other"])
        diet  = st.selectbox("Dietary Style",
            ["Omnivore","Vegetarian","Vegan","Keto","Gluten-Free"])
        stress = st.selectbox("Stress Level", ["Low","Moderate","High","Very High"])
        sleep  = st.slider("Sleep (hrs/night)", 4, 10, 7)
        water  = st.slider("Water intake (L/day)", 1.0, 5.0, 2.5, 0.5)

        profile = {
            "hair_type": hair_type, "concerns": hair_concern,
            "age": age, "sex": sex, "diet": diet,
            "stress": stress, "sleep_hrs": sleep, "water_L": water,
        }
        app_data["hair_profile"] = profile
        save_data(app_data)

    # ── Main header ──────────────────────
    st.title("🧴 AI Hair Health Diet Tracker")
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a365d,#2a4365);padding:1rem;
    border-radius:8px;margin-bottom:1.5rem;border-left:4px solid #4299e1'>
    Track the exact nutrients your hair needs — <b>Biotin, Zinc, Iron, Protein,
    Omega-3, Selenium, Vitamins D/E/C/A</b> — log every meal, and watch your
    30-day progress bring your hair back to life.
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Hair Plan",
        "🍽️ Daily Food Log",
        "📊 Progress Dashboard",
        "📚 Nutrient Guide",
    ])

    # ════════════════════════════════════
    #  TAB 1 – AI HAIR PLAN
    # ════════════════════════════════════
    with tab1:
        st.header("🤖 Your AI-Personalized Hair Nutrition Plan")

        if app_data.get("ai_plan"):
            with st.expander("📋 Your saved plan (click to expand)", expanded=True):
                st.markdown(app_data["ai_plan"])

        col_gen, col_info = st.columns([1, 2])
        with col_gen:
            gen_btn = st.button("✨ Generate / Refresh My Hair Plan", use_container_width=True)

        if gen_btn:
            with st.spinner("🔍 Finding available Groq model…"):
                groq_model, model_id = get_working_model(groq_api_key)

            if not groq_model:
                st.error("All Groq models are rate-limited. Please wait a minute and retry.")
                st.stop()

            st.sidebar.success(f"Model: `{model_id}`")

            prompt = f"""
You are an expert trichologist and nutritionist.

USER PROFILE:
- Age: {age}, Sex: {sex}
- Hair type: {hair_type}
- Hair concerns: {', '.join(hair_concern)}
- Dietary style: {diet}
- Stress level: {stress}
- Sleep: {sleep} hrs/night
- Water: {water} L/day

Create a comprehensive, science-backed HAIR HEALTH NUTRITION PLAN with:

1. **Root-Cause Analysis** – Why this person is likely experiencing these issues (nutrient deficiencies, lifestyle, etc.)

2. **Key Nutrients for Hair Recovery** – Explain the role of Biotin, Zinc, Iron, Protein, Omega-3, Selenium, Vitamin D, E, C, A specifically for THEIR concerns. Include recommended daily targets.

3. **30-Day Daily Meal Plan Template** – A full day's meals (Breakfast, Mid-morning snack, Lunch, Evening snack, Dinner) optimised for hair nutrients. Use real whole foods. Include specific quantities (e.g., "30 g pumpkin seeds", "2 eggs", "100 g salmon").

4. **Top 15 Hair Superfoods** – Seeds, nuts, fish, greens, etc. with the primary hair nutrient each provides and how much to eat daily/weekly.

5. **Foods to Avoid** – That worsen hair loss or thinning.

6. **Weekly Shopping List** – Organised by category (seeds & nuts, proteins, greens, fruits, dairy/alternatives).

7. **Lifestyle Tips** – Sleep, stress management, scalp care routines that complement the diet.

8. **30-Day Milestones** – What to expect week by week.

Format using clear markdown headings. Be specific, actionable, and encouraging.
"""
            hair_agent = Agent(
                name="Trichologist AI",
                role="Expert hair nutritionist and trichologist",
                model=groq_model,
                instructions=[
                    "Be specific with food quantities and nutrient amounts.",
                    "Use markdown formatting with clear sections.",
                    "Always relate advice back to the user's specific hair concerns.",
                    "Include scientific reasoning where helpful.",
                ],
            )

            with st.spinner("🧬 Generating your personalised hair nutrition plan…"):
                response = run_with_retry(hair_agent, prompt)
                plan_text = response.content

            app_data["ai_plan"] = plan_text
            save_data(app_data)
            st.success("✅ Plan generated and saved!")
            st.markdown(plan_text)

    # ════════════════════════════════════
    #  TAB 2 – DAILY FOOD LOG
    # ════════════════════════════════════
    with tab2:
        st.header("🍽️ Daily Food Log")

        selected_date = st.date_input("📅 Log date", value=date.today())
        date_key = selected_date.strftime("%Y-%m-%d")

        if date_key not in app_data["daily_logs"]:
            app_data["daily_logs"][date_key] = []

        today_foods: list = app_data["daily_logs"][date_key]

        # ── Add foods ───────────────────
        st.subheader("➕ Add Foods Eaten Today")
        col_sel, col_qty = st.columns([3, 1])

        with col_sel:
            new_food = st.selectbox(
                "Choose a food item",
                options=sorted(HAIR_FOODS.keys()),
                key="food_selector",
            )
        with col_qty:
            qty = st.number_input("Servings", min_value=0.5, max_value=10.0, value=1.0, step=0.5,
                                  key="qty_input")

        if st.button("➕ Add to Today's Log", use_container_width=True):
            for _ in range(int(qty * 2)):  # store as 0.5-serving units
                pass
            # store as (food, servings) tuples encoded as list
            entry = f"{new_food} ×{qty}"
            # We store raw food name × qty in a simple list for nutrient math
            for _ in range(int(qty)):
                today_foods.append(new_food)
            # fractional last serving
            remainder = qty - int(qty)
            if remainder > 0:
                today_foods.append(f"_PARTIAL_{new_food}_{remainder}")
            app_data["daily_logs"][date_key] = today_foods
            save_data(app_data)
            st.success(f"Added **{new_food}** × {qty} serving(s)!")
            st.rerun()

        # ── Today's log table ────────────
        st.markdown("---")
        st.subheader(f"📋 Food Log for {selected_date.strftime('%A, %d %b %Y')}")

        if not today_foods:
            st.info("No foods logged yet for this day. Add some above! 🥗")
        else:
            # Summarise unique foods with counts
            food_counts: dict[str, float] = {}
            for item in today_foods:
                if item.startswith("_PARTIAL_"):
                    _, _, fname, frac = item.split("_", 3)
                    food_counts[fname] = food_counts.get(fname, 0) + float(frac)
                else:
                    food_counts[item] = food_counts.get(item, 0) + 1.0

            log_rows = []
            for food, servings in food_counts.items():
                row = {"Food": food, "Servings": servings}
                if food in HAIR_FOODS:
                    for nutrient in HAIR_NUTRIENTS:
                        row[nutrient] = round(HAIR_FOODS[food].get(nutrient, 0) * servings, 2)
                log_rows.append(row)

            log_df = pd.DataFrame(log_rows)
            st.dataframe(log_df.set_index("Food"), use_container_width=True)

            # Remove item
            remove_food = st.selectbox("🗑️ Remove a food entry", ["(none)"] + list(food_counts.keys()))
            if st.button("Remove one serving") and remove_food != "(none)":
                idx = len(today_foods) - 1 - today_foods[::-1].index(remove_food)
                today_foods.pop(idx)
                app_data["daily_logs"][date_key] = today_foods
                save_data(app_data)
                st.rerun()

            # ── Nutrient totals ─────────────
            st.markdown("---")

            # Build proper totals accounting for partials
            def calc_totals_from_raw(raw_list):
                totals = {n: 0.0 for n in HAIR_NUTRIENTS}
                for item in raw_list:
                    if item.startswith("_PARTIAL_"):
                        parts = item.split("_", 3)
                        fname, frac = parts[2], float(parts[3])
                        if fname in HAIR_FOODS:
                            for nutrient, val in HAIR_FOODS[fname].items():
                                totals[nutrient] = totals.get(nutrient, 0.0) + val * frac
                    else:
                        if item in HAIR_FOODS:
                            for nutrient, val in HAIR_FOODS[item].items():
                                totals[nutrient] = totals.get(nutrient, 0.0) + val
                return totals

            totals = calc_totals_from_raw(today_foods)
            render_nutrient_gauges(totals)

            st.markdown("---")
            col_radar, col_bar = st.columns(2)
            with col_radar:
                render_radar_chart(totals, day_label=selected_date.strftime("%d %b"))
            with col_bar:
                bar_df = pd.DataFrame({
                    "Nutrient": list(HAIR_NUTRIENTS.keys()),
                    "% of Goal": [pct_goal(totals.get(n, 0), HAIR_NUTRIENTS[n]["daily_goal"])
                                  for n in HAIR_NUTRIENTS],
                })
                fig_bar = px.bar(bar_df, x="% of Goal", y="Nutrient", orientation="h",
                                 color="% of Goal",
                                 color_continuous_scale=["#fc8181","#f6ad55","#68d391"],
                                 range_color=[0, 100],
                                 title="% of Daily Goal Achieved")
                fig_bar.add_vline(x=80, line_dash="dash", line_color="#4299e1", annotation_text="80% target")
                fig_bar.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                                      coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)

    # ════════════════════════════════════
    #  TAB 3 – PROGRESS DASHBOARD
    # ════════════════════════════════════
    with tab3:
        st.header("📊 30-Day Progress Dashboard")

        if not app_data["daily_logs"]:
            st.info("Start logging your daily food intake in the **Daily Food Log** tab to see progress here.")
        else:
            # Build per-day totals for all logged days
            all_days = sorted(app_data["daily_logs"].keys())
            records = []
            for dk in all_days:
                raw = app_data["daily_logs"][dk]
                t = {n: 0.0 for n in HAIR_NUTRIENTS}
                for item in raw:
                    if item.startswith("_PARTIAL_"):
                        parts = item.split("_", 3)
                        fname, frac = parts[2], float(parts[3])
                        if fname in HAIR_FOODS:
                            for n, v in HAIR_FOODS[fname].items():
                                t[n] = t.get(n, 0) + v * frac
                    else:
                        if item in HAIR_FOODS:
                            for n, v in HAIR_FOODS[item].items():
                                t[n] = t.get(n, 0) + v
                t["date"] = dk
                records.append(t)

            prog_df = pd.DataFrame(records)
            prog_df["date"] = pd.to_datetime(prog_df["date"])
            prog_df = prog_df.sort_values("date")

            # ── Filter ──────────────────
            view = st.radio("View", ["Last 7 days", "Last 30 days", "All time"], horizontal=True)
            today_dt = pd.Timestamp(date.today())
            if view == "Last 7 days":
                prog_df = prog_df[prog_df["date"] >= today_dt - pd.Timedelta(days=6)]
            elif view == "Last 30 days":
                prog_df = prog_df[prog_df["date"] >= today_dt - pd.Timedelta(days=29)]

            if prog_df.empty:
                st.info("No data in the selected range yet.")
            else:
                # ── Summary stats ──────────────
                st.subheader("📈 Average Daily Intake vs Goal")
                avg_row = prog_df.drop(columns="date").mean()

                cols = st.columns(5)
                for i, (nutrient, info) in enumerate(HAIR_NUTRIENTS.items()):
                    avg_val = avg_row.get(nutrient, 0)
                    goal    = info["daily_goal"]
                    pct     = pct_goal(avg_val, goal)
                    cls     = status_color(pct)
                    with cols[i % 5]:
                        st.markdown(
                            f"""<div class="metric-card">
                                <p style="font-size:0.7rem;color:#a0aec0;margin:0">Avg {nutrient}</p>
                                <p class="{cls}" style="font-size:1.2rem;margin:4px 0">{avg_val:.1f}</p>
                                <p style="font-size:0.65rem;color:#a0aec0;margin:0">goal {goal} {info['unit']}</p>
                                <p style="font-size:0.8rem;margin:0">{"✅" if pct>=80 else "⚠️" if pct>=50 else "❌"} {pct}%</p>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")

                # ── % goal achieved per day heatmap ──
                st.subheader("🗓️ Daily Nutrient Achievement (% of goal)")
                heat_df = prog_df.copy()
                heat_df["Date"] = heat_df["date"].dt.strftime("%d %b")
                for nutrient in HAIR_NUTRIENTS:
                    goal = HAIR_NUTRIENTS[nutrient]["daily_goal"]
                    heat_df[nutrient] = heat_df[nutrient].apply(
                        lambda x: min(round(x / goal * 100, 0), 100) if goal else 0)
                heat_df = heat_df.set_index("Date")[list(HAIR_NUTRIENTS.keys())]

                fig_heat = px.imshow(
                    heat_df.T,
                    color_continuous_scale=["#2d3748", "#fc8181", "#f6ad55", "#68d391"],
                    range_color=[0, 100],
                    labels=dict(x="Date", y="Nutrient", color="% Goal"),
                    title="% of Daily Goal (0=red, 100=green)",
                    aspect="auto",
                )
                fig_heat.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                                       font_color="#e2e8f0")
                st.plotly_chart(fig_heat, use_container_width=True)

                # ── Line chart per nutrient ──────────
                st.markdown("---")
                st.subheader("📉 Nutrient Trend Over Time")
                chosen_nutrients = st.multiselect(
                    "Select nutrients to plot",
                    options=list(HAIR_NUTRIENTS.keys()),
                    default=["Biotin (mcg)", "Zinc (mg)", "Iron (mg)", "Protein (g)"],
                )
                if chosen_nutrients:
                    fig_line = go.Figure()
                    colors = px.colors.qualitative.Plotly
                    for j, n in enumerate(chosen_nutrients):
                        fig_line.add_trace(go.Scatter(
                            x=prog_df["date"], y=prog_df[n],
                            mode="lines+markers", name=n,
                            line=dict(color=colors[j % len(colors)], width=2),
                        ))
                        goal = HAIR_NUTRIENTS[n]["daily_goal"]
                        fig_line.add_hline(y=goal, line_dash="dot",
                                           line_color=colors[j % len(colors)],
                                           annotation_text=f"Goal {n}", opacity=0.5)
                    fig_line.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)",
                                           plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
                    st.plotly_chart(fig_line, use_container_width=True)

                # ── Weekly summary table ──────────────
                st.markdown("---")
                st.subheader("📆 Weekly Summary")
                prog_df["Week"] = prog_df["date"].dt.to_period("W").apply(
                    lambda r: f"{r.start_time.strftime('%d %b')} – {r.end_time.strftime('%d %b')}"
                )
                weekly_df = prog_df.groupby("Week")[list(HAIR_NUTRIENTS.keys())].mean().round(1)
                weekly_df.columns = [f"Avg {c}" for c in weekly_df.columns]
                st.dataframe(weekly_df, use_container_width=True)

                # ── Days logged ─────────────────────
                st.markdown("---")
                total_days = len(prog_df)
                streak = 0
                d = date.today()
                while d.strftime("%Y-%m-%d") in app_data["daily_logs"]:
                    streak += 1
                    d -= timedelta(days=1)

                c1, c2, c3 = st.columns(3)
                c1.metric("📅 Days Logged", total_days)
                c2.metric("🔥 Current Streak", f"{streak} day{'s' if streak != 1 else ''}")
                c3.metric("📆 Month Progress", f"{min(total_days, 30)}/30 days")

    # ════════════════════════════════════
    #  TAB 4 – NUTRIENT GUIDE
    # ════════════════════════════════════
    with tab4:
        st.header("📚 Hair Nutrients Reference Guide")

        st.markdown("""
        > Every nutrient below has a direct, evidence-backed role in hair growth,
        > thickness, and scalp health. Use this as your daily cheat-sheet.
        """)

        for nutrient, info in HAIR_NUTRIENTS.items():
            with st.expander(f"💊 **{nutrient}** — {info['desc']}", expanded=False):
                st.markdown(f"**Daily Goal:** {info['daily_goal']} {info['unit']}")
                top_foods = sorted(
                    [(food, HAIR_FOODS[food].get(nutrient, 0)) for food in HAIR_FOODS],
                    key=lambda x: x[1], reverse=True
                )[:6]
                st.markdown("**Top food sources (per serving listed):**")
                food_rows = [{"Food": f, f"{nutrient} per serving": v}
                             for f, v in top_foods if v > 0]
                if food_rows:
                    st.table(pd.DataFrame(food_rows))

        st.markdown("---")
        st.subheader("🌱 Full Food Nutrient Database")
        db_df = pd.DataFrame(HAIR_FOODS).T.reset_index()
        db_df.rename(columns={"index": "Food (per serving)"}, inplace=True)
        st.dataframe(db_df.set_index("Food (per serving)"), use_container_width=True)

        st.markdown("---")
        st.subheader("💡 Quick Daily Checklist for Hair Recovery")
        checklist = [
            ("🥚 2 Eggs", "Biotin + Protein + Selenium"),
            ("🐟 Salmon or Sardines 3×/week", "Omega-3 + Vitamin D + Protein"),
            ("🌻 30g Pumpkin Seeds", "Zinc + Iron + Vitamin E"),
            ("🌰 30g Walnuts or Almonds", "Biotin + Vitamin E + Omega-3"),
            ("🥬 100g Spinach or Kale", "Iron + Vitamin C + Vitamin A"),
            ("🍠 1 Sweet Potato", "Vitamin A (beta-carotene)"),
            ("🫐 100g Berries", "Vitamin C (iron absorption)"),
            ("🥑 Half an Avocado", "Vitamin E + Healthy Fats"),
            ("🫙 150g Greek Yogurt", "Protein + Selenium"),
            ("🌱 1 tbsp Flax/Chia seeds", "Omega-3 fatty acids"),
        ]
        for food, nutrients in checklist:
            st.checkbox(f"**{food}** — {nutrients}", key=f"chk_{food}")

        st.info("""
        **💧 Don't forget:**
        - Drink **2.5–3 L** of water daily — dehydration weakens hair structure
        - Avoid: processed sugar, excess alcohol, crash diets, very high Vitamin A supplements
        - Consistency matters — most people see noticeable improvement in **8–12 weeks**
        """)


if __name__ == "__main__":
    main()

