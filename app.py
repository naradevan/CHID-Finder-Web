import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'  # Disable Tkinter warnings
import pandas as pd
from geopy.distance import geodesic
import streamlit as st
import csv
from io import StringIO

st.set_page_config(page_title="CHID Finder", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .stApp { background-color: #121212; }
    .title { 
        font-size: 3.5rem; 
        font-weight: bold;
        color: white;
        margin-bottom: 0.5rem;
    }
    .author { 
        font-size: 1.1rem;
        color: #bbbbbb;
        margin-bottom: 2rem;
    }
    .author a {
        color: #4dabf7;
        text-decoration: none;
        transition: all 0.2s;
    }
    .author a:hover {
        color: #6bc1ff;
        text-decoration: underline;
    }
    .stMarkdown, .stText, .stDataFrame {
        color: #e0e0e0 !important;
    }
    .stFileUploader > div {
        background-color: #1e1e1e !important;
        border: 1px solid #444 !important;
    }
    .success-box {
        background-color: #2d3b2d;
        border-left: 5px solid #4CAF50;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #3b2d2d;
        border-left: 5px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header with improved spacing
st.markdown('<div class="title">CHID Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="author">by <a href="https://linkedin.com/in/xsanosaurus" target="_blank">Naradevan</a></div>',
    unsafe_allow_html=True
)

def detect_separator(file_path):
    try:
        with open(file_path, 'r') as f:
            dialect = csv.Sniffer().sniff(f.read(1024))
            return dialect.delimiter
    except:
        return ','

def load_and_validate_csv(file, expected_type):
    try:
        if isinstance(file, str):
            # File path provided
            separator = detect_separator(file)
            df = pd.read_csv(file, sep=separator)
        else:
            # Uploaded file object
            file.seek(0)
            content = file.read().decode('utf-8')
            try:
                dialect = csv.Sniffer().sniff(content.split('\n')[0])
                separator = dialect.delimiter
            except:
                separator = ','
            df = pd.read_csv(StringIO(content), sep=separator)
        
        # Clean data - remove empty rows and rows with missing coordinates
        df = df.dropna(how='all')
        
        if len(df.columns) < 3:
            raise ValueError(f"Need at least 3 columns, found {len(df.columns)}")
        
        if expected_type == 'HP':
            col_names = ['HP', 'HP_LAT', 'HP_LONG']
        else:
            col_names = ['CHID', 'CHID_LAT', 'CHID_LONG']
        
        df.columns = col_names + list(df.columns[3:])
        
        # Convert coordinates to numeric and drop invalid rows
        df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors='coerce')
        df[df.columns[2]] = pd.to_numeric(df[df.columns[2]], errors='coerce')
        df = df.dropna(subset=df.columns[1:3], how='any')
        
        if df.empty:
            raise ValueError(f"No valid rows found in {expected_type} file after cleaning")
        
        file_info = (
            f"Mapping columns in {file.name if hasattr(file, 'name') else file}:\n"
            f"1: {df.columns[0]} (ID)\n"
            f"2: {df.columns[1]} (LAT)\n"
            f"3: {df.columns[2]} (LONG)\n"
            f"Valid rows: {len(df)}"
        )
        
        return df.iloc[:, :3], file_info
    
    except Exception as e:
        raise ValueError(f"Error processing {expected_type} file: {str(e)}")

def process_files(hp_file, chid_file):
    try:
        # Clear previous results
        st.session_state.clear()
        
        # Load and validate files
        hp_df, hp_info = load_and_validate_csv(hp_file, 'HP')
        chid_df, chid_info = load_and_validate_csv(chid_file, 'CHID')
        
        st.session_state['file_info'] = f"{hp_info}\n\n{chid_info}"
        
        if hp_df.empty or chid_df.empty:
            raise ValueError("One or both files are empty after validation!")
        
        # Create progress bar and status text
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create a copy of HPs that we'll remove from as they get assigned
        available_hps = hp_df.copy()
        results = []
        total_chids = len(chid_df)  # Total CHIDs to process
        
        # First pass: Assign each CHID to its nearest available HP
        for i, (_, chid_row) in enumerate(chid_df.iterrows()):
            chid_coords = (chid_row['CHID_LAT'], chid_row['CHID_LONG'])
            min_distance = float('inf')
            nearest_hp = None
            hp_data = None
            
            # Find nearest available HP
            for _, hp_row in available_hps.iterrows():
                hp_coords = (hp_row['HP_LAT'], hp_row['HP_LONG'])
                try:
                    distance = geodesic(hp_coords, chid_coords).kilometers
                    if distance < min_distance:
                        min_distance = distance
                        nearest_hp = hp_row['HP']
                        hp_data = hp_row
                except:
                    continue
            
            if nearest_hp:
                results.append({
                    'HP': nearest_hp,
                    'HP_LAT': hp_data['HP_LAT'],
                    'HP_LONG': hp_data['HP_LONG'],
                    'Nearest_CHID': chid_row['CHID'],
                    'CHID_LAT': chid_row['CHID_LAT'],
                    'CHID_LONG': chid_row['CHID_LONG'],
                    'Distance_km': round(min_distance, 5)
                })
                
                # Remove this HP from available HPs so it can't be assigned again
                available_hps = available_hps[available_hps['HP'] != nearest_hp]
            
            # Update progress
            progress = (i + 1) / total_chids
            progress_bar.progress(progress)
            status_text.text(f"Processing CHID {i+1}/{total_chids}...")
        
        # Second pass: Assign remaining HPs to their nearest CHIDs (including already used ones)
        if not available_hps.empty:
            status_text.text(f"Assigning {len(available_hps)} remaining HPs...")
            
            for _, hp_row in available_hps.iterrows():
                hp_coords = (hp_row['HP_LAT'], hp_row['HP_LONG'])
                min_distance = float('inf')
                nearest_chid = None
                chid_data = None
                
                # Find nearest CHID (can be already used)
                for _, chid_row in chid_df.iterrows():
                    chid_coords = (chid_row['CHID_LAT'], chid_row['CHID_LONG'])
                    try:
                        distance = geodesic(hp_coords, chid_coords).kilometers
                        if distance < min_distance:
                            min_distance = distance
                            nearest_chid = chid_row['CHID']
                            chid_data = chid_row
                    except:
                        continue
                
                if nearest_chid:
                    results.append({
                        'HP': hp_row['HP'],
                        'HP_LAT': hp_row['HP_LAT'],
                        'HP_LONG': hp_row['HP_LONG'],
                        'Nearest_CHID': nearest_chid,
                        'CHID_LAT': chid_data['CHID_LAT'],
                        'CHID_LONG': chid_data['CHID_LONG'],
                        'Distance_km': round(min_distance, 5)
                    })
        
        # Create result DataFrame
        result_df = pd.DataFrame(results)
        
        # Count unique CHIDs used
        unique_chids_used = result_df['Nearest_CHID'].nunique()
        
        # Clean up progress elements
        progress_bar.empty()
        status_text.empty()
        
        st.session_state['result_df'] = result_df
        st.session_state['unique_chids_used'] = unique_chids_used
        st.session_state['total_chids'] = len(chid_df)
        st.session_state['total_hps'] = len(hp_df)
        st.session_state['processing_complete'] = True
    
    except Exception as e:
        st.session_state['processing_error'] = str(e)
        st.session_state['processing_complete'] = False

# File upload section
st.markdown("### Upload your files")
col1, col2 = st.columns(2)

with col1:
    hp_file = st.file_uploader("Select HPID.csv", type=['csv'], key='hp_uploader')

with col2:
    chid_file = st.file_uploader("Select CHID.csv", type=['csv'], key='chid_uploader')

# Process button
if st.button("Execute", disabled=(not hp_file or not chid_file)):
    process_files(hp_file, chid_file)

# Display file info if available
if 'file_info' in st.session_state:
    st.text(st.session_state['file_info'])

# Display results or errors
if 'processing_complete' in st.session_state:
    if st.session_state['processing_complete']:
        st.markdown('<div class="success-box">'
                   '<h4>✅ Processing Completed Successfully!</h4>'
                   f'<p>Assigned {len(st.session_state["result_df"])} HP-CHID pairs.</p>'
                   f'<p>Used {st.session_state["unique_chids_used"]} out of {st.session_state["total_chids"]} CHIDs.</p>'
                   f'<p>Total HPs processed: {st.session_state["total_hps"]}</p>'
                   '</div>', unsafe_allow_html=True)
        
        # Download section
        csv = st.session_state['result_df'].to_csv(index=False).encode('utf-8')
        
        st.markdown("### Download Results")
        st.download_button(
            label="DOWNLOAD RESULT",
            data=csv,
            file_name='HPID_with_CHID_assignments.csv',
            mime='text/csv',
            key='primary-download'
        )
        
        # Show a preview of the results
        st.markdown("### Results Preview")
        st.dataframe(st.session_state['result_df'].head())
    else:
        st.markdown(f'<div class="error-box">'
                    '<h4>❌ Error Occurred!</h4>'
                    f'<p>{st.session_state["processing_error"]}</p>'
                    '</div>', unsafe_allow_html=True)
