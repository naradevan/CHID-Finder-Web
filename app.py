import pandas as pd
from geopy.distance import geodesic
import streamlit as st
import io

st.set_page_config(page_title="CHID Finder v2.0", layout="wide")

def load_csv(uploaded_file):
    """Load CSV with automatic delimiter detection."""
    try:
        text = uploaded_file.getvalue().decode("utf-8")
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(text.split("\n")[0])
        return pd.read_csv(io.StringIO(text), sep=dialect.delimiter)
    except:
        return pd.read_csv(io.StringIO(text))  # Fallback

def find_nearest_chid(hp_row, chid_df):
    """Your existing distance calculation logic."""
    hp_coords = (hp_row[1], hp_row[2])  # Col2=Lat, Col3=Long
    min_dist = float('inf')
    nearest = None
    for _, chid_row in chid_df.iterrows():
        dist = geodesic(hp_coords, (chid_row[1], chid_row[2])).km
        if dist < min_dist:
            min_dist = dist
            nearest = chid_row[0]  # First col = CHID
    return nearest, round(min_dist, 5)

# Web Interface
st.title("CHID Finder v2.0 Web")
st.write("Upload HPID and CHID CSV files (columns: ID, Lat, Long)")

col1, col2 = st.columns(2)
hp_file = col1.file_uploader("HPID CSV", type="csv")
chid_file = col2.file_uploader("CHID CSV", type="csv")

if hp_file and chid_file:
    hp_df = load_csv(hp_file)
    chid_df = load_csv(chid_file)
    
    if len(hp_df.columns) < 3 or len(chid_df.columns) < 3:
        st.error("Error: Files need ≥3 columns (ID, Lat, Long)")
    else:
        results = []
        progress_bar = st.progress(0)
        
        for i, row in hp_df.iterrows():
            nearest, dist = find_nearest_chid(row, chid_df)
            results.append({
                "HP": row[0], 
                "Nearest_CHID": nearest,
                "Distance_km": dist
            })
            progress_bar.progress((i + 1) / len(hp_df))
        
        st.success("Done! Results:")
        st.dataframe(pd.DataFrame(results))
        
        # Download button
        csv = pd.DataFrame(results).to_csv(index=False)
        st.download_button(
            "Download Results",
            data=csv,
            file_name="nearest_chids.csv"
        )