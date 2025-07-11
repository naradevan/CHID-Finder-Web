# CHID Finder

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chid-finder-naradevan.streamlit.app/)

A geospatial matching tool that assigns each HPID point to its nearest CHID location using precise distance calculations. All HPIDs are assigned exactly once, while CHIDs may be reused across multiple assignments. Distance is not a limiting factor — even the farthest CHID must be considered

## ✨ Features

- **Precise Geospatial Matching** - Uses geodesic calculations for accurate results
- **CSV File Processing** - Works with standard HPID and CHID coordinate files
- **Fast Processing** - Optimized algorithm for quick matching
- **Results Export** - Download matched pairs as CSV with distance data

## 🚀 How to Use

1. **Prepare your files**:
   - `HPID.csv` with columns: `HP, HP_LAT, HP_LONG`
   - `CHID.csv` with columns: `CHID, CHID_LAT, CHID_LONG`

2. **Run the app** and upload both files

3. **Click "Execute"** to process the matching

4. **Download results** as a CSV file

## 📝 File Format Examples

## HPID.csv Example:
```csv
HP,HP_LAT,HP_LONG
A001,-6.12345,106.12345
A002,-6.23456,106.23456
```

## CHID.csv Example:
```csv
CHID,CHID_LAT,CHID_LONG
C101,-6.11111,106.11111
C102,-6.22222,106.22222
```

## Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/naradevan/chid-finder.git
   cd chid-finder
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Requirements
1. Python 3.8+
2. Streamlit
3. Pandas
4. Geopy

Author
👤 Naradevan
https://www.linkedin.com/in/xsanosaurus/

## Terms of Use
- � **Non-Commercial**: Free to use with attribution
- 💼 **Commercial**: Requires written permission
- ⚠️ **No Warranty**: Use at your own risk

© 2025 Naradevan - All rights reserved
