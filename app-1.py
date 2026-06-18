import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import os

warnings.filterwarnings("ignore")

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Food Wastage Management System",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Design Tokens ──────────────────────────────────────────────────────────
COLORS = {
    "forest":   "#1B4332",
    "moss":     "#40916C",
    "sage":     "#74C69D",
    "mist":     "#D8F3DC",
    "soil":     "#6B4226",
    "wheat":    "#F4A261",
    "alert":    "#E76F51",
    "charcoal": "#212529",
    "stone":    "#6C757D",
    "paper":    "#F8F9FA",
}

PALETTE = [COLORS["forest"], COLORS["moss"], COLORS["sage"],
           COLORS["wheat"], COLORS["alert"], COLORS["soil"]]

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {COLORS['paper']};
    color: {COLORS['charcoal']};
  }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
    background: {COLORS['forest']};
    color: white;
  }}
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span {{
    color: white !important;
  }}
  [data-testid="stSidebar"] .stMarkdown h2 {{
    color: {COLORS['sage']} !important;
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
  }}

  /* Hero Banner */
  .hero-banner {{
    background: linear-gradient(135deg, {COLORS['forest']} 0%, {COLORS['moss']} 100%);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    color: white;
    margin-bottom: 1.5rem;
  }}
  .hero-banner h1 {{
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.5px;
  }}
  .hero-banner p {{
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 0;
  }}

  /* KPI Cards */
  .kpi-row {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
  .kpi-card {{
    flex: 1; min-width: 140px;
    background: white;
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    border-left: 4px solid {COLORS['moss']};
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
  }}
  .kpi-card .val {{
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: {COLORS['forest']};
    line-height: 1;
  }}
  .kpi-card .lbl {{
    font-size: 0.78rem;
    color: {COLORS['stone']};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
  }}
  .kpi-card.alert {{ border-left-color: {COLORS['alert']}; }}
  .kpi-card.alert .val {{ color: {COLORS['alert']}; }}
  .kpi-card.warn {{ border-left-color: {COLORS['wheat']}; }}
  .kpi-card.warn .val {{ color: {COLORS['soil']}; }}

  /* Section headers */
  .sec-header {{
    font-family: 'DM Serif Display', serif;
    font-size: 1.45rem;
    color: {COLORS['forest']};
    border-bottom: 2px solid {COLORS['mist']};
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
  }}

  /* Risk badges */
  .badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
  }}
  .badge-high   {{ background: #FDECEA; color: #C62828; }}
  .badge-medium {{ background: #FFF3E0; color: #E65100; }}
  .badge-low    {{ background: {COLORS['mist']}; color: {COLORS['forest']}; }}

  /* Chart containers */
  .chart-box {{
    background: white;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    margin-bottom: 1.2rem;
  }}

  /* Streamlit element tweaks */
  .stDataFrame {{ border-radius: 8px; overflow: hidden; }}
  .stSelectbox > div > div {{ border-radius: 6px; }}
  div[data-testid="metric-container"] {{
    background: white;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
  }}
</style>
""", unsafe_allow_html=True)

# ─── Data Layer ──────────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    """Load or generate data. Tries SQLite first, falls back to synthetic."""
    DB_PATHS = ["food_wastage.db", "database/food_wastage.db", "../food_wastage.db"]
    for p in DB_PATHS:
        if os.path.exists(p):
            try:
                conn = sqlite3.connect(p)
                food   = pd.read_sql("SELECT * FROM food_listings", conn)
                donors = pd.read_sql("SELECT * FROM donors", conn)
                claims = pd.read_sql("SELECT * FROM claims", conn)
                conn.close()
                return food, donors, claims, "SQLite"
            except Exception:
                pass
    return _synthetic_data()

def _synthetic_data():
    np.random.seed(42)
    n = 340
    categories   = ["Vegetables","Fruits","Dairy","Bakery","Cooked Food","Grains","Beverages"]
    locations    = ["Downtown","North Zone","South Zone","East Side","West End","Central Hub"]
    donor_types  = ["Restaurant","Supermarket","Household","Hotel","Catering","NGO"]
    statuses     = ["Available","Claimed","Expired","Partially Claimed"]
    risk_levels  = ["Low","Medium","High"]

    today = datetime.today()
    exp_delta = np.random.randint(-5, 15, n)
    expiry_dates = [(today + timedelta(days=int(d))).strftime("%Y-%m-%d") for d in exp_delta]

    food = pd.DataFrame({
        "food_id":       range(1, n+1),
        "food_name":     np.random.choice(
            ["Rice","Bread","Milk","Apples","Pasta","Soup","Bananas",
             "Yogurt","Tomatoes","Lentils","Cake","Juice","Cheese"], n),
        "category":      np.random.choice(categories, n, p=[.22,.18,.12,.12,.15,.12,.09]),
        "quantity_kg":   np.round(np.random.exponential(8, n) + 1, 1),
        "location":      np.random.choice(locations, n),
        "expiry_date":   expiry_dates,
        "status":        np.random.choice(statuses, n, p=[.35,.40,.15,.10]),
        "risk_level":    np.random.choice(risk_levels, n, p=[.45,.35,.20]),
        "provider_type": np.random.choice(donor_types, n),
        "date_added":    [(today - timedelta(days=int(d))).strftime("%Y-%m-%d")
                          for d in np.random.randint(0, 60, n)],
        "calories_per_kg": np.random.randint(300, 2500, n),
        "wastage_kg":    np.round(np.random.exponential(3, n), 1),
    })

    donors = pd.DataFrame({
        "donor_id":    range(1, 61),
        "name":        [f"Provider {i}" for i in range(1, 61)],
        "type":        np.random.choice(donor_types, 60),
        "location":    np.random.choice(locations, 60),
        "total_donated_kg": np.round(np.random.exponential(50, 60) + 10, 1),
        "active":      np.random.choice([True, False], 60, p=[.8,.2]),
    })

    claims = pd.DataFrame({
        "claim_id":     range(1, 181),
        "food_id":      np.random.randint(1, n+1, 180),
        "receiver_org": np.random.choice(["City Shelter","Food Bank","Community Kitchen",
                                          "School Meal Program","Refugee Center"], 180),
        "quantity_claimed_kg": np.round(np.random.exponential(5, 180) + 0.5, 1),
        "claim_date":   [(today - timedelta(days=int(d))).strftime("%Y-%m-%d")
                         for d in np.random.randint(0, 60, 180)],
        "status":       np.random.choice(["Fulfilled","Pending","Cancelled"], 180, p=[.70,.20,.10]),
    })

    return food, donors, claims, "Synthetic"

# ─── Load ────────────────────────────────────────────────────────────────────
food_df, donors_df, claims_df, data_source = get_data()

# Derived columns
food_df["expiry_date"] = pd.to_datetime(food_df["expiry_date"], errors="coerce")
food_df["date_added"]  = pd.to_datetime(food_df["date_added"],  errors="coerce")
food_df["days_to_expiry"] = (food_df["expiry_date"] - datetime.today()).dt.days
claims_df["claim_date"] = pd.to_datetime(claims_df["claim_date"], errors="coerce")

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 FoodSave Analytics")
    st.caption(f"Data source: **{data_source}**")
    st.markdown("---")
    page = st.radio("Navigate", [
        "📊 Overview Dashboard",
        "🔍 Exploratory Data Analysis",
        "⚠️ Expiry & Risk Predictor",
        "📈 Trends & Forecasting",
        "🗃️ Data Explorer",
    ])
    st.markdown("---")
    st.markdown("**Filters (global)**")
    sel_category = st.multiselect(
        "Category", options=sorted(food_df["category"].unique()),
        default=list(food_df["category"].unique()))
    sel_location = st.multiselect(
        "Location", options=sorted(food_df["location"].unique()),
        default=list(food_df["location"].unique()))

# Apply global filters
df = food_df[
    food_df["category"].isin(sel_category) &
    food_df["location"].isin(sel_location)
].copy()

# ─── Helper: chart style ─────────────────────────────────────────────────────
def apply_style(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor("white")
    ax.figure.patch.set_facecolor("white")
    ax.set_title(title, fontsize=12, fontweight="bold", color=COLORS["charcoal"], pad=10)
    ax.set_xlabel(xlabel, fontsize=9, color=COLORS["stone"])
    ax.set_ylabel(ylabel, fontsize=9, color=COLORS["stone"])
    ax.tick_params(colors=COLORS["stone"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#E9ECEF")
    ax.yaxis.grid(True, color="#F1F3F5", linewidth=0.7)
    ax.set_axisbelow(True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 · OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview Dashboard":
    st.markdown("""
    <div class="hero-banner">
      <h1>🌿 Local Food Wastage Management System</h1>
      <p>Real-time analytics · Expiry risk predictions · Supply–demand matching</p>
    </div>
    """, unsafe_allow_html=True)

    total_qty   = df["quantity_kg"].sum()
    total_waste = df["wastage_kg"].sum()
    high_risk   = (df["risk_level"] == "High").sum()
    expiring_3d = (df["days_to_expiry"].between(0, 3)).sum()
    efficiency  = round(claims_df[claims_df["status"]=="Fulfilled"].shape[0] /
                        max(claims_df.shape[0], 1) * 100, 1)
    active_donors = donors_df["active"].sum()

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="val">{total_qty:,.0f} kg</div>
        <div class="lbl">Total Food Listed</div>
      </div>
      <div class="kpi-card warn">
        <div class="val">{total_waste:,.0f} kg</div>
        <div class="lbl">Estimated Waste</div>
      </div>
      <div class="kpi-card alert">
        <div class="val">{high_risk}</div>
        <div class="lbl">High-Risk Items</div>
      </div>
      <div class="kpi-card alert">
        <div class="val">{expiring_3d}</div>
        <div class="lbl">Expiring ≤ 3 Days</div>
      </div>
      <div class="kpi-card">
        <div class="val">{efficiency}%</div>
        <div class="lbl">Claim Fulfilment Rate</div>
      </div>
      <div class="kpi-card">
        <div class="val">{active_donors}</div>
        <div class="lbl">Active Donors</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="sec-header">Food Status Distribution</p>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(5, 3.5))
        status_counts = df["status"].value_counts()
        wedge_colors = [COLORS["moss"], COLORS["sage"], COLORS["alert"], COLORS["wheat"]]
        wedges, texts, autotexts = ax.pie(
            status_counts, labels=status_counts.index, autopct="%1.1f%%",
            colors=wedge_colors[:len(status_counts)], startangle=140,
            wedgeprops=dict(width=0.6, edgecolor="white", linewidth=2),
            textprops={"fontsize": 8, "color": COLORS["charcoal"]}
        )
        for at in autotexts:
            at.set_fontsize(7.5)
            at.set_color("white")
            at.set_fontweight("bold")
        ax.set_title("Item Status Breakdown", fontsize=11, fontweight="bold",
                     color=COLORS["charcoal"], pad=10)
        fig.patch.set_facecolor("white")
        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col2:
        st.markdown('<p class="sec-header">Quantity by Category</p>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(5, 3.5))
        cat_qty = df.groupby("category")["quantity_kg"].sum().sort_values(ascending=True)
        bars = ax.barh(cat_qty.index, cat_qty.values, color=COLORS["moss"],
                       height=0.6, edgecolor="white")
        for bar, val in zip(bars, cat_qty.values):
            ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                    f"{val:.0f} kg", va="center", ha="left",
                    fontsize=7.5, color=COLORS["stone"])
        apply_style(ax, title="Total Food Quantity by Category (kg)",
                    xlabel="Quantity (kg)", ylabel="")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<p class="sec-header">Waste by Location</p>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(5, 3.2))
        loc_waste = df.groupby("location")["wastage_kg"].sum().sort_values(ascending=False)
        ax.bar(loc_waste.index, loc_waste.values,
               color=[COLORS["alert"], COLORS["wheat"], COLORS["moss"],
                      COLORS["sage"], COLORS["soil"], COLORS["forest"]][:len(loc_waste)],
               edgecolor="white", linewidth=0.8)
        apply_style(ax, title="Estimated Wastage by Location (kg)",
                    xlabel="", ylabel="Wastage (kg)")
        ax.set_xticklabels(loc_waste.index, rotation=30, ha="right", fontsize=7.5)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col4:
        st.markdown('<p class="sec-header">Claim Fulfilment Trend</p>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(5, 3.2))
        claims_df["week"] = claims_df["claim_date"].dt.isocalendar().week
        weekly = claims_df.groupby(["week","status"]).size().unstack(fill_value=0)
        if "Fulfilled" in weekly.columns:
            ax.fill_between(weekly.index, weekly["Fulfilled"],
                            color=COLORS["moss"], alpha=0.7, label="Fulfilled")
        if "Pending" in weekly.columns:
            ax.fill_between(weekly.index, weekly["Pending"],
                            color=COLORS["wheat"], alpha=0.6, label="Pending")
        apply_style(ax, title="Weekly Claims by Status",
                    xlabel="Week of Year", ylabel="Claims")
        ax.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

    st.markdown('<p class="sec-header">Top Donors by Contribution</p>', unsafe_allow_html=True)
    top_donors = donors_df.nlargest(8, "total_donated_kg")[
        ["name","type","location","total_donated_kg","active"]]
    top_donors["active"] = top_donors["active"].map({True:"✅ Active", False:"⏸ Inactive"})
    top_donors.columns = ["Donor","Type","Location","Donated (kg)","Status"]
    st.dataframe(top_donors, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 · EDA
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Exploratory Data Analysis":
    st.markdown('<p class="sec-header">Exploratory Data Analysis</p>', unsafe_allow_html=True)
    st.caption(f"Analysing **{len(df)}** food listings after applied filters.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Distributions", "🔗 Correlations", "🗺️ Location Analysis", "🏷️ Category Deep-Dive"
    ])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            ax.hist(df["quantity_kg"].clip(upper=df["quantity_kg"].quantile(0.97)),
                    bins=30, color=COLORS["moss"], edgecolor="white", alpha=0.9)
            ax.axvline(df["quantity_kg"].mean(), color=COLORS["alert"],
                       lw=1.5, linestyle="--", label=f'Mean {df["quantity_kg"].mean():.1f} kg')
            apply_style(ax, title="Distribution of Listing Quantity",
                        xlabel="Quantity (kg)", ylabel="Count")
            ax.legend(fontsize=8)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            ax.hist(df["days_to_expiry"].dropna().clip(-10, 20),
                    bins=30, color=COLORS["wheat"], edgecolor="white", alpha=0.9)
            ax.axvline(0, color=COLORS["alert"], lw=1.5, linestyle="--", label="Today")
            ax.axvline(3, color=COLORS["forest"], lw=1.2, linestyle=":", label="3-day threshold")
            apply_style(ax, title="Days to Expiry Distribution",
                        xlabel="Days", ylabel="Count")
            ax.legend(fontsize=8)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        col3, col4 = st.columns(2)
        with col3:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            provider_counts = df["provider_type"].value_counts()
            ax.bar(provider_counts.index, provider_counts.values,
                   color=PALETTE[:len(provider_counts)], edgecolor="white")
            apply_style(ax, title="Listings by Provider Type",
                        xlabel="", ylabel="Count")
            ax.set_xticklabels(provider_counts.index, rotation=30, ha="right", fontsize=7.5)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        with col4:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            risk_counts = df["risk_level"].value_counts().reindex(["Low","Medium","High"])
            bar_colors  = [COLORS["moss"], COLORS["wheat"], COLORS["alert"]]
            ax.bar(risk_counts.index, risk_counts.values,
                   color=bar_colors, edgecolor="white", width=0.5)
            for i, (idx, val) in enumerate(risk_counts.items()):
                ax.text(i, val + 1, str(val), ha="center", fontsize=9,
                        fontweight="bold", color=COLORS["charcoal"])
            apply_style(ax, title="Items by Risk Level", xlabel="", ylabel="Count")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        st.markdown("**Descriptive Statistics**")
        st.dataframe(df[["quantity_kg","wastage_kg","days_to_expiry","calories_per_kg"]]
                     .describe().round(2), use_container_width=True)

    with tab2:
        numeric_cols = df[["quantity_kg","wastage_kg","days_to_expiry","calories_per_kg"]].dropna()
        corr = numeric_cols.corr()

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(5, 4))
            mask = np.triu(np.ones_like(corr, dtype=bool))
            sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="YlGn",
                        ax=ax, linewidths=0.5, linecolor="white",
                        annot_kws={"size": 9}, cbar_kws={"shrink": 0.8})
            ax.set_title("Correlation Matrix", fontsize=11, fontweight="bold",
                         color=COLORS["charcoal"])
            fig.patch.set_facecolor("white")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.scatter(df["quantity_kg"].clip(upper=80),
                       df["wastage_kg"].clip(upper=30),
                       c=df["risk_level"].map({"Low": COLORS["moss"],
                                               "Medium": COLORS["wheat"],
                                               "High": COLORS["alert"]}),
                       alpha=0.55, s=28, edgecolors="white", linewidth=0.4)
            apply_style(ax, title="Quantity vs Wastage (coloured by Risk)",
                        xlabel="Listed Quantity (kg)", ylabel="Wastage (kg)")
            patches = [
                mpatches.Patch(color=COLORS["moss"],  label="Low"),
                mpatches.Patch(color=COLORS["wheat"], label="Medium"),
                mpatches.Patch(color=COLORS["alert"], label="High"),
            ]
            ax.legend(handles=patches, fontsize=8)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        fig, axes = plt.subplots(1, 4, figsize=(12, 3))
        for ax_i, col in zip(axes, ["quantity_kg","wastage_kg","days_to_expiry","calories_per_kg"]):
            sns.boxplot(x="risk_level", y=col, data=df,
                        order=["Low","Medium","High"],
                        palette={"Low": COLORS["moss"],
                                 "Medium": COLORS["wheat"],
                                 "High": COLORS["alert"]},
                        ax=ax_i)
            apply_style(ax_i, title=col.replace("_", " ").title(),
                        xlabel="Risk Level", ylabel="")
        plt.suptitle("Feature Distribution by Risk Level",
                     y=1.02, fontsize=11, fontweight="bold", color=COLORS["charcoal"])
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(5.5, 4))
            loc_cat = df.groupby(["location","category"])["quantity_kg"].sum().unstack(fill_value=0)
            loc_cat.plot(kind="bar", ax=ax, color=PALETTE[:len(loc_cat.columns)],
                         edgecolor="white", linewidth=0.5, width=0.75)
            apply_style(ax, title="Quantity by Location & Category",
                        xlabel="", ylabel="Quantity (kg)")
            ax.set_xticklabels(loc_cat.index, rotation=35, ha="right", fontsize=7.5)
            ax.legend(fontsize=7, bbox_to_anchor=(1.01, 1), borderaxespad=0)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(5.5, 4))
            loc_risk = df.groupby(["location","risk_level"]).size().unstack(fill_value=0)
            if "High" in loc_risk.columns:
                ax.bar(loc_risk.index, loc_risk.get("High", 0),
                       label="High", color=COLORS["alert"], edgecolor="white")
            if "Medium" in loc_risk.columns:
                ax.bar(loc_risk.index, loc_risk.get("Medium", 0),
                       bottom=loc_risk.get("High", 0),
                       label="Medium", color=COLORS["wheat"], edgecolor="white")
            if "Low" in loc_risk.columns:
                bottom = loc_risk.get("High", 0) + loc_risk.get("Medium", 0)
                ax.bar(loc_risk.index, loc_risk.get("Low", 0),
                       bottom=bottom,
                       label="Low", color=COLORS["moss"], edgecolor="white")
            apply_style(ax, title="Risk Levels by Location", xlabel="", ylabel="Count")
            ax.set_xticklabels(loc_risk.index, rotation=30, ha="right", fontsize=7.5)
            ax.legend(fontsize=8)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        fig, ax = plt.subplots(figsize=(10, 3.5))
        loc_summary = df.groupby("location").agg(
            total_qty=("quantity_kg","sum"),
            total_waste=("wastage_kg","sum"),
            high_risk=("risk_level", lambda x: (x=="High").sum())
        ).reset_index()
        x = np.arange(len(loc_summary))
        w = 0.28
        ax.bar(x - w, loc_summary["total_qty"],  width=w, color=COLORS["moss"],  label="Total Qty", edgecolor="white")
        ax.bar(x,     loc_summary["total_waste"], width=w, color=COLORS["alert"], label="Wastage",   edgecolor="white")
        ax.bar(x + w, loc_summary["high_risk"],   width=w, color=COLORS["wheat"], label="High Risk", edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(loc_summary["location"], rotation=25, ha="right", fontsize=8)
        apply_style(ax, title="Location Summary: Quantity · Waste · High Risk",
                    xlabel="", ylabel="Value")
        ax.legend(fontsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

    with tab4:
        selected_cat = st.selectbox("Select Category", sorted(df["category"].unique()))
        cat_df = df[df["category"] == selected_cat]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Items",    len(cat_df))
        m2.metric("Total Qty (kg)", f'{cat_df["quantity_kg"].sum():.0f}')
        m3.metric("Avg Wastage (kg)", f'{cat_df["wastage_kg"].mean():.1f}')
        m4.metric("High-Risk Items", (cat_df["risk_level"]=="High").sum())

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            ax.hist(cat_df["quantity_kg"].clip(upper=cat_df["quantity_kg"].quantile(0.95)),
                    bins=20, color=COLORS["sage"], edgecolor="white")
            apply_style(ax, title=f"{selected_cat} – Quantity Distribution",
                        xlabel="Quantity (kg)", ylabel="Count")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            status_c = cat_df["status"].value_counts()
            ax.pie(status_c, labels=status_c.index, autopct="%1.0f%%",
                   colors=PALETTE[:len(status_c)],
                   wedgeprops=dict(width=0.55, edgecolor="white"),
                   textprops={"fontsize": 8})
            ax.set_title(f"{selected_cat} – Status Mix", fontsize=10,
                         fontweight="bold", color=COLORS["charcoal"])
            fig.patch.set_facecolor("white")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True); plt.close()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 · EXPIRY & RISK PREDICTOR
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚠️ Expiry & Risk Predictor":
    st.markdown('<p class="sec-header">Expiry & Risk Predictor</p>', unsafe_allow_html=True)
    st.caption("Rule-based risk scoring calibrated on category decay rates and quantity thresholds.")

    def predict_risk(days, qty, category):
        decay = {"Dairy":1,"Cooked Food":1.2,"Vegetables":0.9,"Fruits":0.85,
                 "Bakery":0.8,"Beverages":0.4,"Grains":0.2}
        d = decay.get(category, 0.7)
        score = 0
        if days   <= 1:  score += 40
        elif days <= 3:  score += 25
        elif days <= 7:  score += 10
        else:             score += 0
        if qty >= 20:     score += 15
        elif qty >= 10:   score += 8
        score = int(score * d)
        if score >= 35:   return "High",   COLORS["alert"], score
        elif score >= 15: return "Medium", COLORS["wheat"], score
        else:             return "Low",    COLORS["moss"],  score

    st.markdown("### 🧪 Single Item Risk Check")
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            p_name  = st.text_input("Food Item", value="Bread")
        with c2:
            p_cat   = st.selectbox("Category", sorted(df["category"].unique()))
        with c3:
            p_qty   = st.number_input("Quantity (kg)", 1.0, 500.0, 10.0, step=0.5)
        with c4:
            p_days  = st.number_input("Days to Expiry", -5, 30, 4)

        if st.button("🔮 Predict Risk", use_container_width=True):
            risk, color, score = predict_risk(p_days, p_qty, p_cat)
            badge_cls = {"High":"badge-high","Medium":"badge-medium","Low":"badge-low"}[risk]
            col_a, col_b = st.columns([1,2])
            with col_a:
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:1.4rem;
                            border-left:5px solid {color};box-shadow:0 1px 8px rgba(0,0,0,0.08);">
                  <div style="font-size:1rem;font-weight:600;color:{COLORS['charcoal']}">{p_name}</div>
                  <div style="font-size:2.2rem;font-weight:700;color:{color};margin:8px 0">{risk} Risk</div>
                  <div style="font-size:0.85rem;color:{COLORS['stone']}">Score: {score}/55</div>
                  <div style="font-size:0.8rem;color:{COLORS['stone']};margin-top:6px">
                    {p_qty} kg · {p_cat} · {p_days}d left
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if risk == "High":
                    st.error("🚨 **Immediate action needed.** Prioritise this item for redistribution within 24 hours.")
                elif risk == "Medium":
                    st.warning("⚠️ **Monitor closely.** Flag for redistribution within 2–3 days.")
                else:
                    st.success("✅ **Within safe window.** Continue regular monitoring.")

    st.divider()
    st.markdown("### 📋 Batch Risk Assessment")

    risk_df = df[["food_name","category","quantity_kg","days_to_expiry","location","status"]].copy()
    risk_df["predicted_risk"] = risk_df.apply(
        lambda r: predict_risk(r["days_to_expiry"], r["quantity_kg"], r["category"])[0], axis=1)
    risk_df["risk_score"] = risk_df.apply(
        lambda r: predict_risk(r["days_to_expiry"], r["quantity_kg"], r["category"])[2], axis=1)

    fil_risk = st.selectbox("Filter by predicted risk", ["All","High","Medium","Low"])
    show_df  = risk_df if fil_risk == "All" else risk_df[risk_df["predicted_risk"] == fil_risk]

    def style_risk(val):
        colors_map = {"High":"background-color:#FDECEA;color:#C62828",
                      "Medium":"background-color:#FFF3E0;color:#E65100",
                      "Low":f"background-color:{COLORS['mist']};color:{COLORS['forest']}"}
        return colors_map.get(val, "")

    styled = show_df.nlargest(50, "risk_score").style.applymap(
        style_risk, subset=["predicted_risk"]).format(
        {"quantity_kg": "{:.1f}", "days_to_expiry": "{:.0f}", "risk_score": "{:.0f}"})
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 📊 Risk Score Distribution")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(5, 3.4))
        for level, color in [("Low", COLORS["moss"]), ("Medium", COLORS["wheat"]), ("High", COLORS["alert"])]:
            sub = risk_df[risk_df["predicted_risk"] == level]["risk_score"]
            ax.hist(sub, bins=15, color=color, edgecolor="white", alpha=0.85, label=level)
        apply_style(ax, title="Risk Score Distribution by Level",
                    xlabel="Score", ylabel="Count")
        ax.legend(fontsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(5, 3.4))
        cat_risk = risk_df[risk_df["predicted_risk"]=="High"].groupby("category").size().sort_values()
        ax.barh(cat_risk.index, cat_risk.values, color=COLORS["alert"],
                edgecolor="white", height=0.6)
        apply_style(ax, title="High-Risk Items by Category", xlabel="Count", ylabel="")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 · TRENDS & FORECASTING
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Trends & Forecasting":
    st.markdown('<p class="sec-header">Trends & Forecasting</p>', unsafe_allow_html=True)

    df_t = df.dropna(subset=["date_added"]).copy()
    df_t["week"] = df_t["date_added"].dt.to_period("W").astype(str)
    weekly = df_t.groupby("week").agg(
        listings=("food_id","count"),
        total_qty=("quantity_kg","sum"),
        total_waste=("wastage_kg","sum"),
    ).reset_index().sort_values("week").tail(10)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        x = range(len(weekly))
        ax.plot(x, weekly["total_qty"], color=COLORS["moss"], lw=2.5, marker="o",
                markersize=5, label="Total Listed")
        ax.fill_between(x, weekly["total_qty"], alpha=0.12, color=COLORS["moss"])
        ax.plot(x, weekly["total_waste"], color=COLORS["alert"], lw=2, marker="s",
                markersize=4, linestyle="--", label="Wastage")

        # Simple linear forecast
        if len(weekly) >= 3:
            coef = np.polyfit(range(len(weekly)), weekly["total_waste"], 1)
            future_x = np.array([len(weekly), len(weekly)+1, len(weekly)+2])
            forecast  = np.polyval(coef, future_x)
            ax.plot([len(weekly)-1] + list(future_x),
                    [weekly["total_waste"].iloc[-1]] + list(forecast),
                    color=COLORS["alert"], lw=1.5, linestyle=":", alpha=0.7, label="Forecast")
            ax.axvspan(len(weekly)-0.5, len(weekly)+2.5, alpha=0.04,
                       color=COLORS["alert"], label="Forecast window")

        ax.set_xticks(x)
        ax.set_xticklabels(weekly["week"], rotation=40, ha="right", fontsize=6.5)
        apply_style(ax, title="Weekly Food Listed vs Wastage",
                    xlabel="Week", ylabel="Quantity (kg)")
        ax.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        ax.bar(range(len(weekly)), weekly["listings"],
               color=COLORS["sage"], edgecolor="white", width=0.65, label="New Listings")
        coef2 = np.polyfit(range(len(weekly)), weekly["listings"], 1)
        ax.plot(range(len(weekly)), np.polyval(coef2, range(len(weekly))),
                color=COLORS["forest"], lw=2, linestyle="--", label="Trend")
        ax.set_xticks(range(len(weekly)))
        ax.set_xticklabels(weekly["week"], rotation=40, ha="right", fontsize=6.5)
        apply_style(ax, title="Weekly New Food Listings",
                    xlabel="Week", ylabel="Count")
        ax.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True); plt.close()

    st.markdown("### 📉 Wastage Rate by Category Over Time")
    fig, axes = plt.subplots(2, 4, figsize=(14, 5))
    axes = axes.flatten()
    for i, cat in enumerate(sorted(df_t["category"].unique())):
        if i >= 8: break
        ax = axes[i]
        cat_weekly = df_t[df_t["category"]==cat].groupby("week")["wastage_kg"].sum().tail(8)
        ax.plot(range(len(cat_weekly)), cat_weekly.values,
                color=PALETTE[i % len(PALETTE)], lw=2, marker="o", markersize=3)
        ax.fill_between(range(len(cat_weekly)), cat_weekly.values,
                        alpha=0.1, color=PALETTE[i % len(PALETTE)])
        apply_style(ax, title=cat, xlabel="", ylabel="Waste (kg)")
        ax.set_xticks([])
    for j in range(i+1, 8):
        axes[j].set_visible(False)
    plt.suptitle("Wastage Trend by Category",
                 fontsize=11, fontweight="bold", color=COLORS["charcoal"], y=1.01)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close()

    st.markdown("### 🔮 14-Day Waste Forecast")
    st.info("Forecast uses linear extrapolation on recent weekly wastage. Replace with ARIMA/Prophet for production use.")
    last_waste  = weekly["total_waste"].values
    coef_main   = np.polyfit(range(len(last_waste)), last_waste, 1)
    future_days = np.arange(len(last_waste), len(last_waste)+14)
    forecast_vals = np.polyval(coef_main, future_days)
    noise = np.random.normal(0, forecast_vals.std() * 0.08, 14)
    lo, hi = forecast_vals - abs(noise)*2, forecast_vals + abs(noise)*2

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(range(len(last_waste)), last_waste, color=COLORS["moss"],
            lw=2.5, marker="o", markersize=5, label="Historical Waste")
    ax.plot(future_days, forecast_vals, color=COLORS["alert"],
            lw=2, linestyle="--", label="Forecast")
    ax.fill_between(future_days, lo, hi, alpha=0.15, color=COLORS["alert"], label="Confidence band")
    ax.axvline(len(last_waste)-0.5, color=COLORS["stone"], lw=1, linestyle=":")
    ax.text(len(last_waste)-0.3, ax.get_ylim()[1]*0.95,
            "Forecast →", fontsize=8, color=COLORS["stone"])
    apply_style(ax, title="Wastage Forecast (Linear Extrapolation)",
                xlabel="Period", ylabel="Waste (kg)")
    ax.legend(fontsize=9)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 · DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗃️ Data Explorer":
    st.markdown('<p class="sec-header">Data Explorer</p>', unsafe_allow_html=True)

    tab_f, tab_d, tab_c = st.tabs(["🍱 Food Listings","👥 Donors","📦 Claims"])

    with tab_f:
        col1, col2, col3 = st.columns(3)
        with col1:
            srch = st.text_input("Search food name", "")
        with col2:
            stat_filter = st.multiselect("Status", df["status"].unique(),
                                         default=list(df["status"].unique()))
        with col3:
            risk_filter = st.multiselect("Risk Level", ["Low","Medium","High"],
                                         default=["Low","Medium","High"])

        filtered = df[
            df["status"].isin(stat_filter) &
            df["risk_level"].isin(risk_filter) &
            df["food_name"].str.contains(srch, case=False, na=False)
        ].sort_values("days_to_expiry")

        st.caption(f"Showing {len(filtered)} records")
        st.dataframe(filtered[[
            "food_name","category","quantity_kg","location",
            "expiry_date","days_to_expiry","status","risk_level","provider_type"
        ]].rename(columns={
            "food_name":"Item","category":"Category","quantity_kg":"Qty (kg)",
            "location":"Location","expiry_date":"Expiry","days_to_expiry":"Days Left",
            "status":"Status","risk_level":"Risk","provider_type":"Provider"
        }), use_container_width=True, hide_index=True)

    with tab_d:
        st.dataframe(donors_df.rename(columns={
            "name":"Donor","type":"Type","location":"Location",
            "total_donated_kg":"Total Donated (kg)","active":"Active"
        }), use_container_width=True, hide_index=True)

    with tab_c:
        st.dataframe(claims_df.rename(columns={
            "claim_id":"ID","food_id":"Food ID","receiver_org":"Receiver",
            "quantity_claimed_kg":"Claimed (kg)","claim_date":"Date","status":"Status"
        }), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**Quick SQL-Style Summary**")
    summary_q = st.selectbox("Select query", [
        "Top 5 categories by wastage",
        "Locations with most high-risk items",
        "Average quantity by provider type",
        "Claim fulfilment rate by receiver",
    ])

    if summary_q == "Top 5 categories by wastage":
        res = df.groupby("category")["wastage_kg"].sum().nlargest(5).reset_index()
        res.columns = ["Category","Total Wastage (kg)"]
    elif summary_q == "Locations with most high-risk items":
        res = df[df["risk_level"]=="High"].groupby("location").size().reset_index(name="High-Risk Count")
        res = res.sort_values("High-Risk Count", ascending=False)
    elif summary_q == "Average quantity by provider type":
        res = df.groupby("provider_type")["quantity_kg"].mean().round(1).reset_index()
        res.columns = ["Provider Type","Avg Quantity (kg)"]
    else:
        res = claims_df.groupby(["receiver_org","status"]).size().unstack(fill_value=0).reset_index()

    st.dataframe(res, use_container_width=True, hide_index=True)
