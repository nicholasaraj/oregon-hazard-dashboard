import streamlit as st
import folium
import geopandas as gpd
import pandas as pd
from streamlit_folium import st_folium
import tempfile
import requests
import gdown

# --- Streamlit setup ---
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Oregon Precipitation, Wildfires, and Landslides")

@st.cache_data
def load_data():
    def download_from_drive(file_id):
        output = tempfile.NamedTemporaryFile(delete=False, suffix=".geojson")
        gdown.download(id=file_id, output=output.name, quiet=True)
        return output.name

    # Google Drive File IDs
    county_csv_id = "1Af6Xh3ugLx_jAeQc1qPOOe-szzADKTX_"
    landslide_geojson_id = "1j5xOYXjNY9E1wequhjE-vxBLA8_WgVdj"
    fire_geojson_id = "1zQmcVrtqCU_RzZcrZzPTxZCoJXMbIob7"

    counties = pd.read_csv(f"https://drive.google.com/uc?export=download&id={county_csv_id}")
    landslides = gpd.read_file(download_from_drive(landslide_geojson_id))
    fires = gpd.read_file(download_from_drive(fire_geojson_id))

    return counties, landslides, fires

counties, landslides, fires = load_data()

# Clean and sample
landslides = landslides[pd.notnull(landslides["REPAIR_COST"])].sample(n=500, random_state=42)
fires = fires[pd.notnull(fires["BurnIndex"])].sample(n=500, random_state=42)

# Define bounds
min_precip_val = float(counties["AveragePrecip"].min())
max_precip_val = float(counties["AveragePrecip"].max())
min_burn_val = float(fires["BurnIndex"].min())
max_burn_val = float(fires["BurnIndex"].max())
min_cost_val = float(landslides["REPAIR_COST"].min())
max_cost_val = float(landslides["REPAIR_COST"].max())

# Sidebar
st.sidebar.header("Filter Options")

# Reset button
if st.sidebar.button("🔁 Reset Filters"):
    st.session_state.precip_min = min_precip_val
    st.session_state.precip_max = max_precip_val
    st.session_state.burn_min = min_burn_val
    st.session_state.burn_max = max_burn_val
    st.session_state.cost_min = min_cost_val
    st.session_state.cost_max = max_cost_val

# Precipitation filter
st.sidebar.markdown("#### Precipitation (in)")
precip_min = st.sidebar.number_input("Min Precip", value=st.session_state.get("precip_min", min_precip_val),
                                     min_value=min_precip_val, max_value=max_precip_val, key="precip_min")
precip_max = st.sidebar.number_input("Max Precip", value=st.session_state.get("precip_max", max_precip_val),
                                     min_value=min_precip_val, max_value=max_precip_val, key="precip_max")
precip_range = (precip_min, precip_max)

# Burn index filter
st.sidebar.markdown("#### Burn Index")
burn_min = st.sidebar.number_input("Min Burn Index", value=st.session_state.get("burn_min", min_burn_val),
                                   min_value=min_burn_val, max_value=max_burn_val, key="burn_min")
burn_max = st.sidebar.number_input("Max Burn Index", value=st.session_state.get("burn_max", max_burn_val),
                                   min_value=min_burn_val, max_value=max_burn_val, key="burn_max")
burn_range = (burn_min, burn_max)

# Repair cost filter
st.sidebar.markdown("#### Repair Cost ($)")
cost_min = st.sidebar.number_input("Min Repair Cost", value=st.session_state.get("cost_min", min_cost_val),
                                   min_value=min_cost_val, max_value=max_cost_val, key="cost_min", step=1000.0, format="%.0f")
cost_max = st.sidebar.number_input("Max Repair Cost", value=st.session_state.get("cost_max", max_cost_val),
                                   min_value=min_cost_val, max_value=max_cost_val, key="cost_max", step=1000.0, format="%.0f")
cost_range = (cost_min, cost_max)

# Toggles
show_fires = st.sidebar.checkbox("Show Wildfires", True)
show_landslides = st.sidebar.checkbox("Show Landslides", True)

# Apply filters
counties_filtered = counties.groupby(['subregion', 'group']).filter(
    lambda g: precip_range[0] <= g["AveragePrecip"].mean() <= precip_range[1]
)
fires_filtered = fires[
    (fires["BurnIndex"] >= burn_range[0]) & (fires["BurnIndex"] <= burn_range[1])
]
landslides_filtered = landslides[
    (landslides["REPAIR_COST"] >= cost_range[0]) & (landslides["REPAIR_COST"] <= cost_range[1])
]

# === Live Count Output ===
st.markdown(f"**Visible Counties**: {counties_filtered['subregion'].nunique()}")
if show_fires:
    st.markdown(f"**Visible Wildfires**: {len(fires_filtered)}")
if show_landslides:
    st.markdown(f"**Visible Landslides**: {len(landslides_filtered)}")

# --- Build Map ---
m = folium.Map(location=[44.1, -120.5], zoom_start=7, tiles="CartoDB positron")

# Counties
for (subregion, group), df in counties_filtered.groupby(['subregion', 'group']):
    points = df[['lat', 'long']].values.tolist()
    avg_precip = df['AveragePrecip'].mean()
    if avg_precip > 70:
        color = '#3b0f70'
    elif avg_precip > 50:
        color = '#842681'
    elif avg_precip > 35:
        color = '#df65b0'
    elif avg_precip > 20:
        color = '#fbb4b9'
    else:
        color = '#fef0d9'
    folium.Polygon(
        locations=points,
        color='black',
        weight=0.3,
        fill=True,
        fill_opacity=0.7,
        fill_color=color,
        tooltip=f"{subregion.title()} County<br>Avg Precip: {avg_precip:.1f} in"
    ).add_to(m)

# Fires
if show_fires:
    fg = folium.FeatureGroup(name="Wildfires", show=True)
    for _, row in fires_filtered.iterrows():
        popup = f"""<strong>Wildfire</strong><br>Name: {row.get('FireName', 'Unknown')}<br>Burn Index: {row['BurnIndex']}"""
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=3,
            color="orange",
            fill=True,
            fill_opacity=0.6,
            popup=folium.Popup(popup, max_width=300)
        ).add_to(fg)
    fg.add_to(m)

# Landslides
if show_landslides:
    fg = folium.FeatureGroup(name="Landslides", show=True)
    for _, row in landslides_filtered.iterrows():
        cost_str = f"${int(row['REPAIR_COST']):,}"
        popup = f"""<strong>Landslide</strong><br>Name: {row.get('SLIDE_NAME', 'Unknown')}<br>Repair Cost: {cost_str}"""
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.6,
            popup=folium.Popup(popup, max_width=300)
        ).add_to(fg)
    fg.add_to(m)

folium.LayerControl().add_to(m)
st_folium(m, width=1300, height=700)
