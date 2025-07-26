# Oregon Hazards Dashboard

An interactive Streamlit app for visualizing geospatial hazard data in Oregon, including wildfires, landslides, and average annual precipitation. The dashboard lets users explore risk indicators and filter by precipitation, burn index, and landslide repair cost.

**Live app:** [oregon-hazards-dashboard.streamlit.app](https://oregon-hazards-dashboard.streamlit.app)

---

## Features

- Interactive filters for:
  - Precipitation range (inches)
  - Wildfire burn index
  - Landslide repair cost ($)
- Toggle layers for wildfires and landslides
- Choropleth shading for average precipitation by county
- Fully interactive Folium map embedded in Streamlit

---

## Tech Stack

- [Streamlit](https://streamlit.io/)
- [Folium](https://python-visualization.github.io/folium/)
- [GeoPandas](https://geopandas.org/)
- Google Drive file integration
- [Pandas](https://pandas.pydata.org/)

---

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```
streamlit run app.py
```
