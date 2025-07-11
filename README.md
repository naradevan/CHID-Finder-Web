# CHID Finder

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app/)

A geospatial matching tool that automatically assigns the nearest CHID locations to HPID points.

## Features

- 🗺️ Geospatial Matching: Uses precise geodesic calculations
- 📁 CSV Processing: Handles HPID and CHID coordinate files
- ⚡ Fast Processing: Optimized for quick matching
- 📊 Results Export: Download ready-to-use CSV files

## How It Works

1. Upload HPID.csv (columns: HP, HP_LAT, HP_LONG)
2. Upload CHID.csv (columns: CHID, CHID_LAT, CHID_LONG)
3. Click "Execute"
4. Download results CSV

## File Format Example

HPID.csv:
HP,HP_LAT,HP_LONG
A001,-6.12345,106.12345

CHID.csv:
CHID,CHID_LAT,CHID_LONG
C101,-6.11111,106.11111

## Installation

```bash
git clone https://github.com/yourusername/chid-finder.git
cd chid-finder
pip install -r requirements.txt
streamlit run app.py
