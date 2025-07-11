import pandas as pd
from geopy.distance import geodesic
import streamlit as st
import csv
import io

st.set_page_config(page_title="CHID Finder v2.0 Web", layout="wide")

def load_csv(uploaded_file):
    """Load CSV with automatic delimiter detection."""
    try:
        text = uploaded_file.getvalue().decode("utf-8")
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(text.split("\n")[0])
        return pd.read_csv(io.StringIO(text), sep=dialect.delimiter)
    except:
        return pd.read_csv(io.StringIO(text))  # Fallback

def find_nearest_chid(self, hp_row, chid_df):
    """Finds the nearest CHID for an HP (ensures ALL CHIDs are considered)"""
    hp_coords = (hp_row['HP_LAT'], hp_row['HP_LONG'])
    min_distance = float('inf')
    nearest_chid = None
    nearest_lat = None
    nearest_long = None
    
    # Check EVERY CHID point (no early termination)
    for _, chid_row in chid_df.iterrows():
        chid_coords = (chid_row['CHID_LAT'], chid_row['CHID_LONG'])
        distance = geodesic(hp_coords, chid_coords).kilometers
        
        if distance < min_distance:
            min_distance = distance
            nearest_chid = chid_row['CHID']
            nearest_lat = chid_row['CHID_LAT']
            nearest_long = chid_row['CHID_LONG']
    
    # Guarantee a result (even if distance is large)
    return {
        'CHID': nearest_chid,
        'Distance_km': round(min_distance, 5),
        'CHID_LAT': nearest_lat,
        'CHID_LONG': nearest_long
    }

def process_files(self):
    """Process all HPs against all CHIDs (complete 1:1 mapping)"""
    try:
        hp_df = self.load_and_validate_csv(self.hp_file.get(), 'HP')
        chid_df = self.load_and_validate_csv(self.chid_file.get(), 'CHID')
        
        results = []
        total = len(hp_df)
        
        for i, (_, hp_row) in enumerate(hp_df.iterrows()):
            # Every HP gets processed
            nearest = self.find_nearest_chid(hp_row, chid_df)
            
            results.append({
                'HP': hp_row['HP'],
                'HP_LAT': hp_row['HP_LAT'],
                'HP_LONG': hp_row['HP_LONG'],
                **nearest  # Unpacks all CHID data
            })
            
            # Update progress
            self.progress['value'] = (i + 1) / total * 100
            self.status.set(f"Processing HP {i+1}/{total}")
            self.root.update_idletasks()
        
        # Save ALL results
        output_path = self.hp_file.get().replace('.csv', '_nearest_CHIDs.csv')
        pd.DataFrame(results).to_csv(output_path, index=False)
        
        self.status.set(f"Complete! Saved to {output_path}")
        messagebox.showinfo("Success", f"Matched {len(results)} HPs to CHIDs")
        
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
