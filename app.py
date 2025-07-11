import pandas as pd
from geopy.distance import geodesic
import streamlit as st
from io import StringIO

# App Config
st.set_page_config(page_title="CHID Finder", layout="wide")

# Custom Dark Mode CSS
st.markdown("""
<style>
    .stApp { background-color: #121212; }
    .title { 
        font-size: 5rem; 
        font-weight: bold;
        color: white;
        margin-bottom: 0.05rem;
    }
    .author { 
        font-size: 2rem;
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
</style>
""", unsafe_allow_html=True)

# Header with improved spacing
st.markdown('<div class="title">CHID Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="author">by <a href="https://linkedin.com/in/xsanosaurus" target="_blank">Naradevan</a></div>',
    unsafe_allow_html=True
)

# [Keep all your existing file processing functions here]
# [Keep your existing file upload and processing logic here]
# [Keep your existing results display logic here]

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
