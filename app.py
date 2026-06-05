import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="APL Logistics Commercial Intelligence",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("APL_Logistics_Cleaned.csv")

    if "Customer Full Name" not in df.columns:
        fname = df["Customer Fname"].fillna("").astype(str)
        lname = df["Customer Lname"].fillna("").astype(str)
        df["Customer Full Name"] = (fname + " " + lname).str.strip()

    if "Profit Margin %" not in df.columns:
        df["Profit Margin %"] = (
            df["Order Profit Per Order"]
            / df["Sales"].replace(0, np.nan)
        ) * 100

    return df


df = load_data()

# ============================
# SIDEBAR FILTERS
# ============================

st.sidebar.title("🛠 Control Panel")

segments = st.sidebar.multiselect(
    "Customer Segment",
    sorted(df["Customer Segment"].dropna().unique()),
    default=sorted(df["Customer Segment"].dropna().unique())
)

market = st.sidebar.selectbox(
    "Global Market",
    ["All"] + sorted(df["Market"].dropna().unique().tolist())
)

categories = st.sidebar.multiselect(
    "Product Category",
    sorted(df["Category Name"].dropna().unique()),
    default=sorted(df["Category Name"].dropna().unique())
)

products = st.sidebar.multiselect(
    "Product Name",
    sorted(df["Product Name"].dropna().unique()),
    default=sorted(df["Product Name"].dropna().unique())
)

regions_available = (
    df["Order Region"].dropna().unique()
    if market == "All"
    else df[df["Market"] == market]["Order Region"].dropna().unique()
)

regions = st.sidebar.multiselect(
    "Order Region",
    sorted(regions_available),
    default=sorted(regions_available)
)

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Discount Scenario Simulator")

discount_cap = st.sidebar.slider(
    "Maximum Discount Rate (%)",
    min_value=0,
    max_value=25,
    value=15
) / 100

# ============================
# FILTER DATA
# ============================

filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["Customer Segment"].isin(segments)
]

filtered_df = filtered_df[
    filtered_df["Category Name"].isin(categories)
]

filtered_df = filtered_df[
    filtered_df["Product Name"].isin(products)
]

filtered_df = filtered_df[
    filtered_df["Order Region"].isin(regions)
]

if market != "All":
    filtered_df = filtered_df[
        filtered_df["Market"] == market
    ]

# ============================
# EXECUTIVE OVERVIEW
# ============================

st.title("🚢 APL Logistics Commercial Intelligence Dashboard")

total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Order Profit Per Order"].sum()

avg_margin = (
    total_profit / total_sales * 100
) if total_sales > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Revenue", f"${total_sales:,.2f}")
k2.metric("Total Profit", f"${total_profit:,.2f}")
k3.metric("Profit Margin", f"{avg_margin:.2f}%")
k4.metric("Orders Analyzed", f"{len(filtered_df):,}")

st.markdown("---")

# ============================
# CUSTOMER DASHBOARD
# ============================

st.subheader("👥 Customer Value Dashboard")

c1, c2 = st.columns(2)

with c1:
    seg_sales = (
        filtered_df.groupby("Customer Segment")["Sales"]
        .sum()
        .reset_index()
    )

    fig_seg = px.pie(
        seg_sales,
        values="Sales",
        names="Customer Segment",
        hole=0.4,
        title="Revenue Contribution by Customer Segment"
    )
    st.plotly_chart(fig_seg, use_container_width=True)

with c2:
    cust_profit = (
        filtered_df.groupby("Customer Full Name")
        ["Order Profit Per Order"]
        .sum()
        .reset_index()
    )

    top5 = cust_profit.nlargest(
        5,
        "Order Profit Per Order"
    )

    bottom5 = cust_profit.nsmallest(
        5,
        "Order Profit Per Order"
    )

    fig_tb = px.bar(
        pd.concat([top5, bottom5]),
        x="Order Profit Per Order",
        y="Customer Full Name",
        orientation="h",
        title="Top & Bottom Customers by Profit"
    )

    st.plotly_chart(fig_tb, use_container_width=True)

customer_tiers = (
    filtered_df.groupby("Customer Id")
    ["Order Profit Per Order"]
    .sum()
    .reset_index()
)

if len(customer_tiers) > 4:
    customer_tiers["Tier"] = pd.qcut(
        customer_tiers["Order Profit Per Order"],
        4,
        labels=["Bronze", "Silver", "Gold", "Platinum"],
        duplicates="drop"
    )

    fig_tiers = px.histogram(
        customer_tiers,
        x="Tier",
        title="Customer Value Segmentation"
    )

    st.plotly_chart(fig_tiers, use_container_width=True)

pareto = customer_tiers.sort_values(
    "Order Profit Per Order",
    ascending=False
).reset_index(drop=True)

pareto["CumProfit"] = pareto["Order Profit Per Order"].cumsum()

total_customer_profit = pareto["Order Profit Per Order"].sum()

if total_customer_profit > 0:
    pareto["CumPercent"] = (
        pareto["CumProfit"] / total_customer_profit
    ) * 100
else:
    pareto["CumPercent"] = 0

fig_pareto = px.line(
    pareto,
    y="CumPercent",
    title="Pareto Analysis (Customer Profit Concentration)"
)

st.plotly_chart(fig_pareto, use_container_width=True)

st.markdown("---")

# ============================
# PRODUCT & CATEGORY ANALYSIS
# ============================

st.subheader("📦 Product & Category Performance")

product_perf = (
    filtered_df.groupby("Product Name")
    .agg({
        "Sales": "sum",
        "Order Profit Per Order": "sum"
    })
    .reset_index()
)

product_perf["Margin %"] = (
    product_perf["Order Profit Per Order"]
    / product_perf["Sales"].replace(0, np.nan)
) * 100

top_products = product_perf.nlargest(
    15,
    "Order Profit Per Order"
)

fig_products = px.bar(
    top_products,
    x="Order Profit Per Order",
    y="Product Name",
    orientation="h",
    title="Top 15 Products by Profit"
)

st.plotly_chart(fig_products, use_container_width=True)

category_perf = (
    filtered_df.groupby("Category Name")
    .agg({
        "Sales": "sum",
        "Order Profit Per Order": "sum"
    })
    .reset_index()
)

category_perf["Margin %"] = (
    category_perf["Order Profit Per Order"]
    / category_perf["Sales"].replace(0, np.nan)
) * 100

if not category_perf.empty:

    best = category_perf.loc[
        category_perf["Margin %"].idxmax()
    ]

    worst = category_perf.loc[
        category_perf["Margin %"].idxmin()
    ]

    m1, m2 = st.columns(2)

    m1.metric(
        "Most Profitable Category",
        str(best["Category Name"])
    )

    m2.metric(
        "Least Profitable Category",
        str(worst["Category Name"])
    )

pivot_data = filtered_df.pivot_table(
    index="Category Name",
    columns="Order Region",
    values="Order Profit Per Order",
    aggfunc="mean"
)

if not pivot_data.empty:

    fig_heat = px.imshow(
        pivot_data,
        aspect="auto",
        title="Category vs Region Profitability Heatmap"
    )

    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ============================
# DISCOUNT IMPACT ANALYZER
# ============================

st.subheader("📉 Discount Impact Analyzer")

if len(filtered_df) > 0:

    sample_df = filtered_df.sample(
        min(2000, len(filtered_df)),
        random_state=42
    )

    fig_disc = px.scatter(
        sample_df,
        x="Order Item Discount Rate",
        y="Profit Margin %",
        color="Category Name",
        trendline="lowess",
        title="Discount Rate vs Profit Margin"
    )

    st.plotly_chart(fig_disc, use_container_width=True)

sim_df = filtered_df.copy()

sim_df["Saved Discount"] = sim_df.apply(
    lambda x: max(
        0,
        (x["Order Item Discount Rate"] - discount_cap)
        * x["Sales"]
    ),
    axis=1
)

projected_profit = (
    total_profit + sim_df["Saved Discount"].sum()
)

projected_margin = (
    projected_profit / total_sales * 100
) if total_sales > 0 else 0.0

s1, s2, s3 = st.columns(3)

s1.metric(
    "Current Profit",
    f"${total_profit:,.2f}"
)

s2.metric(
    "Projected Profit",
    f"${projected_profit:,.2f}"
)

s3.metric(
    "Projected Margin",
    f"{projected_margin:.2f}%"
)

st.markdown("---")

# ============================
# MARKET INTELLIGENCE
# ============================

st.subheader("🌍 Market & Regional Profitability")

market_perf = (
    filtered_df.groupby("Market")
    .agg({
        "Sales": "sum",
        "Order Profit Per Order": "sum"
    })
    .reset_index()
)

if not market_perf.empty:

    market_perf["Margin %"] = (
        market_perf["Order Profit Per Order"]
        / market_perf["Sales"].replace(0, np.nan)
    ) * 100

    fig_market = px.bar(
        market_perf,
        x="Market",
        y="Margin %",
        color="Margin %",
        title="Market Profitability"
    )

    st.plotly_chart(fig_market, use_container_width=True)

region_perf = (
    filtered_df.groupby("Order Region")
    .agg({
        "Sales": "sum",
        "Order Profit Per Order": "sum"
    })
    .reset_index()
)

if not region_perf.empty:

    fig_region = px.bar(
        region_perf,
        x="Order Region",
        y="Order Profit Per Order",
        color="Order Profit Per Order",
        title="Regional Profitability"
    )

    st.plotly_chart(fig_region, use_container_width=True)

country_perf = (
    filtered_df.groupby("Order Country")
    ["Order Profit Per Order"]
    .sum()
    .reset_index()
)

if not country_perf.empty:

    fig_map = px.choropleth(
        country_perf,
        locations="Order Country",
        locationmode="country names",
        color="Order Profit Per Order",
        title="Country Profitability Map"
    )

    st.plotly_chart(fig_map, use_container_width=True)
