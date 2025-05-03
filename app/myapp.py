import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# Helper function for map colors
def get_color_based_on_price(price, min_price, max_price):
    # Generate color from green (affordable) to red (expensive)
    ratio = (price - min_price) / (max_price - min_price)
    r = min(255, int(ratio * 255))
    g = min(255, int((1 - ratio) * 255))
    return f"#{r:02x}{g:02x}00"

# Set page configuration
st.set_page_config(
    page_title="Chennai Real Estate Land Cost Analysis",
    page_icon="🏙️",
    layout="wide"
)

# App title and description
st.title("Chennai Real Estate Land Cost Analyzer")
st.markdown("""
This application analyzes land costs across different neighborhoods in Chennai.
Explore property prices, trends, and get insights on the best investment areas.
""")

# Function to load data (using PropReturns API - you'll need to sign up for an API key)
@st.cache_data(ttl=86400)  # Cache data for 1 day
def load_property_data():
    # In a real app, you would use the actual API key and endpoint
    # API_KEY = "your_api_key_here"
    # url = f"https://api.propreturns.in/properties/search?city=chennai&api_key={API_KEY}"
    
    # For demo purposes, we'll create synthetic data that mimics what we might get from an API
    neighborhoods = [
        "T Nagar", "Adyar", "Anna Nagar", "Velachery", "Porur", 
        "Mylapore", "Tambaram", "Sholinganallur", "Perungudi", "Chromepet",
        "Pallavaram", "Thoraipakkam", "Medavakkam", "Madipakkam", "Siruseri"
    ]
    
    # Generate synthetic data
    num_properties = 200
    data = {
        "id": list(range(1, num_properties + 1)),
        "neighborhood": np.random.choice(neighborhoods, num_properties),
        "price_per_sqft": np.random.normal(8000, 3000, num_properties),  # Mean price 8000 INR/sqft with variation
        "total_price": np.random.normal(10000000, 5000000, num_properties),  # Mean 1 crore INR with variation
        "area_sqft": np.random.normal(1200, 400, num_properties),  # Mean 1200 sqft with variation
        "property_type": np.random.choice(["Residential Plot", "Commercial Plot", "Agricultural Land"], num_properties),
        "listing_date": [datetime.now().date() - pd.Timedelta(days=np.random.randint(1, 365)) for _ in range(num_properties)],
    }
    
    # Add geospatial data - approximate Chennai neighborhood coordinates
    # In reality, these would be more precise for each property
    neighborhood_coords = {
        "T Nagar": (13.0418, 80.2341),
        "Adyar": (13.0012, 80.2565),
        "Anna Nagar": (13.0837, 80.2143),
        "Velachery": (12.9815, 80.2180),
        "Porur": (13.0374, 80.1571),
        "Mylapore": (13.0332, 80.2668),
        "Tambaram": (12.9249, 80.1000),
        "Sholinganallur": (12.9010, 80.2279),
        "Perungudi": (12.9542, 80.2312),
        "Chromepet": (12.9516, 80.1462),
        "Pallavaram": (12.9675, 80.1491),
        "Thoraipakkam": (12.9421, 80.2388),
        "Medavakkam": (12.9179, 80.1927),
        "Madipakkam": (12.9639, 80.1936),
        "Siruseri": (12.8266, 80.2197)
    }
    
    data["latitude"] = [neighborhood_coords[n][0] + np.random.normal(0, 0.005) for n in data["neighborhood"]]
    data["longitude"] = [neighborhood_coords[n][1] + np.random.normal(0, 0.005) for n in data["neighborhood"]]
    
    df = pd.DataFrame(data)
    
    # Clean the data
    df["price_per_sqft"] = df["price_per_sqft"].apply(lambda x: max(x, 2000))  # Ensure minimum reasonable price
    df["total_price"] = df["price_per_sqft"] * df["area_sqft"]
    df["price_per_sqft"] = df["price_per_sqft"].round(2)
    df["total_price"] = df["total_price"].round(2)
    df["area_sqft"] = df["area_sqft"].round(2)
    
    return df

# Load data
property_data = load_property_data()

# Sidebar filters
st.sidebar.header("Filters")

selected_neighborhoods = st.sidebar.multiselect(
    "Select Neighborhoods", 
    options=sorted(property_data["neighborhood"].unique()),
    default=sorted(property_data["neighborhood"].unique())[:5]  # Default to first 5 alphabetically
)

min_price, max_price = st.sidebar.slider(
    "Price Range (₹ per sq.ft.)", 
    float(property_data["price_per_sqft"].min()), 
    float(property_data["price_per_sqft"].max()),
    (float(property_data["price_per_sqft"].min()), float(property_data["price_per_sqft"].max()))
)

property_types = st.sidebar.multiselect(
    "Property Type",
    options=sorted(property_data["property_type"].unique()),
    default=sorted(property_data["property_type"].unique())
)

# Filter data based on selection
filtered_data = property_data[
    (property_data["neighborhood"].isin(selected_neighborhoods)) &
    (property_data["price_per_sqft"] >= min_price) &
    (property_data["price_per_sqft"] <= max_price) &
    (property_data["property_type"].isin(property_types))
]

# Main content area
if filtered_data.empty:
    st.warning("No data found with the current filter settings. Please adjust your filters.")
else:
    # Layout with columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Property Price Map")
        
        # Create a folium map centered on Chennai
        m = folium.Map(location=[13.0827, 80.2707], zoom_start=11)
        
        # Add points to the map
        for idx, row in filtered_data.iterrows():
            popup_text = f"""
            <b>Neighborhood:</b> {row['neighborhood']}<br>
            <b>Price:</b> ₹{row['price_per_sqft']:,.2f}/sqft<br>
            <b>Property Type:</b> {row['property_type']}<br>
            <b>Area:</b> {row['area_sqft']} sqft<br>
            <b>Total Price:</b> ₹{row['total_price']:,.2f}
            """
            
            folium.CircleMarker(
                location=(row["latitude"], row["longitude"]),
                radius=5,
                popup=folium.Popup(popup_text, max_width=300),
                color="blue",
                fill=True,
                fill_color=get_color_based_on_price(row["price_per_sqft"], filtered_data["price_per_sqft"].min(), filtered_data["price_per_sqft"].max()),
                fill_opacity=0.7
            ).add_to(m)
        
        # Add heat map layer
        heat_data = [[row["latitude"], row["longitude"], row["price_per_sqft"]] for idx, row in filtered_data.iterrows()]
        HeatMap(heat_data, radius=15).add_to(m)
        
        # Display the map
        folium_static(m)
    
    with col2:
        st.subheader("Average Price by Neighborhood")
        neighborhood_avg = filtered_data.groupby("neighborhood")["price_per_sqft"].mean().reset_index()
        neighborhood_avg = neighborhood_avg.sort_values("price_per_sqft", ascending=False)
        
        fig = px.bar(
            neighborhood_avg, 
            x="neighborhood", 
            y="price_per_sqft",
            title="Average Price per Square Foot",
            labels={"neighborhood": "Neighborhood", "price_per_sqft": "Price (₹ per sq.ft.)"},
            color="price_per_sqft",
            color_continuous_scale=px.colors.sequential.Plasma
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Price distribution
    st.subheader("Price Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Price Distribution by Neighborhood")
        fig = px.box(
            filtered_data, 
            x="neighborhood", 
            y="price_per_sqft", 
            color="neighborhood",
            labels={"neighborhood": "Neighborhood", "price_per_sqft": "Price (₹ per sq.ft.)"}
        )
        fig.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("Price Distribution by Property Type")
        fig = px.violin(
            filtered_data,
            x="property_type",
            y="price_per_sqft",
            color="property_type",
            box=True,
            labels={"property_type": "Property Type", "price_per_sqft": "Price (₹ per sq.ft.)"}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    with st.expander("View Raw Data"):
        st.dataframe(filtered_data)
    
    # Inferential Report
    st.header("Inferential Report")
    
    # Calculate statistics
    overall_avg = filtered_data["price_per_sqft"].mean()
    overall_median = filtered_data["price_per_sqft"].median()
    price_std = filtered_data["price_per_sqft"].std()
    most_expensive = filtered_data.groupby("neighborhood")["price_per_sqft"].mean().idxmax()
    least_expensive = filtered_data.groupby("neighborhood")["price_per_sqft"].mean().idxmin()
    
    # Price trends over time (using listing dates)
    filtered_data["month_year"] = pd.to_datetime(filtered_data["listing_date"]).dt.to_period("M")
    time_trend = filtered_data.groupby("month_year")["price_per_sqft"].mean().reset_index()
    time_trend["month_year"] = time_trend["month_year"].astype(str)
    
    # Report summary
    st.subheader("Key Insights")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric("Average Price", f"₹{overall_avg:,.2f}/sqft")
    with metric_col2:
        st.metric("Median Price", f"₹{overall_median:,.2f}/sqft")
    with metric_col3:
        st.metric("Price Std Dev", f"₹{price_std:,.2f}")
        
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.info(f"**Most Expensive Area:** {most_expensive}\n\nAverage price: ₹{filtered_data[filtered_data['neighborhood'] == most_expensive]['price_per_sqft'].mean():,.2f}/sqft")
    
    with insight_col2:
        st.info(f"**Most Affordable Area:** {least_expensive}\n\nAverage price: ₹{filtered_data[filtered_data['neighborhood'] == least_expensive]['price_per_sqft'].mean():,.2f}/sqft")
    
    # Price trend chart
    st.subheader("Price Trends Over Time")
    fig = px.line(
        time_trend, 
        x="month_year", 
        y="price_per_sqft",
        markers=True,
        title="Average Price Trends",
        labels={"month_year": "Month", "price_per_sqft": "Average Price (₹ per sq.ft.)"}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation between factors
    st.subheader("Price Factors")
    
    # Additional fake factors for analysis
    filtered_data["distance_to_center"] = np.random.normal(8, 4, len(filtered_data))  # km from city center
    filtered_data["schools_nearby"] = np.random.randint(0, 10, len(filtered_data))  # number of schools within 1km
    filtered_data["hospitals_nearby"] = np.random.randint(0, 5, len(filtered_data))  # number of hospitals within 1km
    
    # Correlation analysis
    correlation_factors = filtered_data[["price_per_sqft", "area_sqft", "distance_to_center", "schools_nearby", "hospitals_nearby"]]
    corr = correlation_factors.corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax)
    st.pyplot(fig)
    
    # Investment recommendations
    st.subheader("Investment Recommendations")
    
    # Calculate price to amenities ratio (a made-up metric for demonstration)
    filtered_data["investment_score"] = filtered_data["price_per_sqft"] / (filtered_data["schools_nearby"] + filtered_data["hospitals_nearby"] + 1)
    
    top_investments = filtered_data.groupby("neighborhood").agg({
        "price_per_sqft": "mean",
        "investment_score": "mean",
        "schools_nearby": "mean",
        "hospitals_nearby": "mean"
    }).sort_values("investment_score")
    
    top_investments = top_investments.reset_index().head(5)
    
    st.write("Top 5 Areas for Investment Based on Price and Amenities:")
    st.dataframe(top_investments)
    
    # Written analysis
    st.subheader("Market Analysis Summary")
    
    st.markdown(f"""
    ### Chennai Real Estate Market Overview
    
    Based on the analysis of {len(filtered_data)} properties across {len(selected_neighborhoods)} neighborhoods in Chennai, we can draw the following conclusions:
    
    1. **Price Range**: Land costs in Chennai vary significantly, with an average of ₹{overall_avg:,.2f} per sq.ft. and a standard deviation of ₹{price_std:,.2f}.
    
This analysis provides a snapshot of the Chennai real estate market. For investment decisions, it is recommended to conduct further due diligence and consult with local real estate professionals.
""")

# Helper function for map colors
def get_color_based_on_price(price, min_price, max_price):
    # Generate color from green (affordable) to red (expensive)
    ratio = (price - min_price) / (max_price - min_price)
    r = min(255, int(ratio * 255))
    g = min(255, int((1 - ratio) * 255))
    return f"#{r:02x}{g:02x}00"