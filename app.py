import pandas as pd
from geopy.distance import geodesic
import streamlit as st
import csv
import io

st.set_page_config(page_title="CHID Finder v2.0 Web", layout="wide")

def load_csv(uploaded_file, expected_type):
    """Auto-detect columns like your desktop version (position-based)"""
    try:
        # Read file with auto delimiter detection
        text = uploaded_file.getvalue().decode("utf-8")
        dialect = csv.Sniffer().sniff(text.split("\n")[0])
        df = pd.read_csv(io.StringIO(text), sep=dialect.delimiter)
        
        # Require at least 3 columns
        if len(df.columns) < 3:
            raise ValueError("File must have ≥3 columns (ID, Lat, Long)")
        
        # Auto-map columns by position
        col_map = {
            'HP': {0: 'HP', 1: 'HP_LAT', 2: 'HP_LONG'},
            'CHID': {0: 'CHID', 1: 'CHID_LAT', 2: 'CHID_LONG'}
        }[expected_type]
        
        # Show mapping in the interface
        st.info(f"Detected columns in {uploaded_file.name}:\n" +
                f"1. {df.columns[0]} → {col_map[0]}\n" +
                f"2. {df.columns[1]} → {col_map[1]}\n" +
                f"3. {df.columns[2]} → {col_map[2]}")
        
        # Rename columns
        return df.rename(columns={
            df.columns[0]: col_map[0],
            df.columns[1]: col_map[1],
            df.columns[2]: col_map[2]
        }).iloc[:, :3]  # Keep only first 3 columns
        
    except Exception as e:
        st.error(f"⚠️ Error loading {uploaded_file.name}: {str(e)}")
        return None

# Web Interface
st.title("CHID Finder v2.0 Web")
st.markdown("""
Upload your CSV files with **any column names**.  
The first 3 columns will be used as:  
`ID`, `Latitude`, `Longitude`  
""")

hp_file = st.file_uploader("Upload HPID CSV", type="csv")
chid_file = st.file_uploader("Upload CHID CSV", type="csv")

if hp_file and chid_file:
    with st.spinner("Processing files..."):
        hp_df = load_csv(hp_file, 'HP')
        chid_df = load_csv(chid_file, 'CHID')
        
        if hp_df is None or chid_df is None:
            st.stop()
        
        # Process data (same logic as desktop)
        results = []
        progress_bar = st.progress(0)
        
        for i, hp_row in hp_df.iterrows():
            hp_coords = (hp_row['HP_LAT'], hp_row['HP_LONG'])
            min_dist = float('inf')
            nearest = None
            
            for _, chid_row in chid_df.iterrows():
                dist = geodesic(hp_coords, (chid_row['CHID_LAT'], chid_row['CHID_LONG'])).km
                if dist < min_dist:
                    min_dist = dist
                    nearest = chid_row['CHID']
            
            results.append({
                "HP_ID": hp_row['HP'],
                "Nearest_CHID": nearest,
                "Distance_km": round(min_dist, 5),
                "CHID_Latitude": chid_row['CHID_LAT'],
                "CHID_Longitude": chid_row['CHID_LONG']
            })
            progress_bar.progress((i + 1) / len(hp_df))
        
        # Display results
        st.success(f"✅ Processed {len(results)} points!")
        st.dataframe(pd.DataFrame(results))
        
        # Download button
        csv = pd.DataFrame(results).to_csv(index=False)
        st.download_button(
            "Download Full Results (CSV)",
            data=csv,
            file_name="nearest_chids_results.csv",
            mime="text/csv"
        )
