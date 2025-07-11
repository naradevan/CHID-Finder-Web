import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'  # Disable Tkinter warnings
import pandas as pd
from geopy.distance import geodesic
import streamlit as st
import os
import csv
from io import StringIO


st.set_page_config(page_title="CHID Finder", layout="wide")

# Dark/light mode toggle
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Custom CSS for styling
st.markdown(f"""
    <style>
    /* Main title */
    .title {{
        font-size: 2rem;
        font-weight: bold;
        color: {'#ffffff' if st.session_state.dark_mode else '#2c3e50'};
        margin-bottom: 1rem;
    }}
    
    .author {{
        font-size: 1rem;
        color: {'#bbbbbb' if st.session_state.dark_mode else '#555555'};
        margin-bottom: 1.5rem;
    }}
    
    .author a {{
        color: {'#4dabf7' if st.session_state.dark_mode else '#1a73e8'};
        text-decoration: none;
    }}
    
    .author a:hover {{
        text-decoration: underline;
    }}

    /* Success and error boxes */
    .success-box {{
        background-color: {'#2d3b2d' if st.session_state.dark_mode else '#e8f5e9'};
        color: {'#e0e0e0' if st.session_state.dark_mode else '#2c3e50'};
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 5px solid #4CAF50;
    }}
    
    .success-box h4 {{
        color: {'#a5d6a7' if st.session_state.dark_mode else '#1e5631'};
        margin-top: 0;
    }}
    
    .success-box p {{
        color: {'#e0e0e0' if st.session_state.dark_mode else '#2c3e50'};
        margin-bottom: 0.5rem;
    }}
    
    .error-box {{
        background-color: {'#422b2b' if st.session_state.dark_mode else '#ffebee'};
        color: {'#e0e0e0' if st.session_state.dark_mode else '#2c3e50'};
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 5px solid #f44336;
    }}
    
    /* Main content background */
    .stApp {{
        background-color: {'#121212' if st.session_state.dark_mode else '#ffffff'} !important;
    }}
    
    /* Text elements */
    .stMarkdown, .stText, .stDataFrame {{
        color: {'#e0e0e0' if st.session_state.dark_mode else '#000000'} !important;
    }}
    
    /* File uploader */
    .stFileUploader > div {{
        background-color: {'#1e1e1e' if st.session_state.dark_mode else '#f0f2f6'} !important;
        border-color: {'#444' if st.session_state.dark_mode else '#ccc'} !important;
    }}
    
    /* Download button */
    .stDownloadButton button {{
        background-color: #4CAF50 !important;
        color: white !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
        border-radius: 5px !important;
        border: none !important;
        font-size: 1rem !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        margin-top: 1rem;
    }}
    
    .stDownloadButton button:hover {{
        background-color: #45a049 !important;
        transform: scale(1.02) !important;
    }}
    
    /* Remove any residual progress bar elements */
    .stProgress > div > div > div {{
        display: none !important;
    }}
    
    /* Toggle button */
    .toggle-container {{
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 999;
    }}
    </style>
""", unsafe_allow_html=True)

# Dark/light mode toggle button
col1, col2 = st.columns([1, 1])
with col2:
    if st.button("🌙 Dark" if not st.session_state.dark_mode else "☀️ Light"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Main app header
st.markdown('<div class="title">CHID Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="author">by <a href="https://www.linkedin.com/in/xsanosaurus/" target="_blank">Naradevan</a></div>', 
    unsafe_allow_html=True
)

# Rest of your existing functions (detect_separator, load_and_validate_csv, process_files) remain the same
# ... [Keep all your existing functions exactly as they are] ...

# File upload section
st.markdown("### Upload your files")
col1, col2 = st.columns(2)

with col1:
    hp_file = st.file_uploader("Select HPID.csv", type=['csv'], key='hp_uploader')

with col2:
    chid_file = st.file_uploader("Select CHID.csv", type=['csv'], key='chid_uploader')

# Process button
if st.button("Execute", disabled=(not hp_file or not chid_file)):
    st.session_state.clear()  # Clear previous results
    st.session_state.dark_mode = st.session_state.get('dark_mode', False)  # Preserve dark mode
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
                   '</div>', unsafe_allow_html=True)
        
        # Only show download section if not already downloaded
        if 'file_downloaded' not in st.session_state:
            csv = st.session_state['result_df'].to_csv(index=False).encode('utf-8')
            
            st.markdown("### Download Results")
            if st.download_button(
                label="DOWNLOAD RESULT",
                data=csv,
                file_name='HPID_with_CHID_assignments.csv',
                mime='text/csv',
                key='primary-download'
            ):
                # Set flag when download is clicked
                st.session_state['file_downloaded'] = True
                st.rerun()  # Rerun to update the UI
        else:
            # Show a success message instead of the button
            st.markdown("""
            <div class="success-box">
                <h4>✅ Download Complete!</h4>
                <p>File "HPID_with_CHID_assignments.csv" has been saved to your downloads folder.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show a preview of the results
        st.markdown("### Results Preview")
        st.dataframe(st.session_state['result_df'].head())
    else:
        st.markdown(f'<div class="error-box">'
                    '<h4>❌ Error Occurred!</h4>'
                    f'<p>{st.session_state["processing_error"]}</p>'
                    '</div>', unsafe_allow_html=True)
