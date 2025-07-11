import pandas as pd
from geopy.distance import geodesic
from tkinter import Tk, Label, Button, filedialog, messagebox, ttk, StringVar
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import sys
import os
import csv

# Add to top of nearest_chid_finder.py
if getattr(sys, 'frozen', False):
    os.environ['GEOPY_CACHE_DIR'] = os.path.join(sys._MEIPASS, 'geopy')

class NearestCHIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nearest CHID Finder")
        self.root.geometry("500x300")
        
        # Variables
        self.hp_file = StringVar()
        self.chid_file = StringVar()
        self.status = StringVar(value="Ready")
        
        # GUI Elements
        Label(root, text="Drag and drop files or browse manually:").pack(pady=10)
        
        # Drag and Drop Area
        self.drop_label = Label(root, text="Drop HPID.csv and CHID.csv here", relief="groove", width=50, height=5)
        self.drop_label.pack(pady=10)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # File Selection Buttons
        Button(root, text="Select HPID.csv", command=lambda: self.browse_file('HPID')).pack(pady=5)
        Button(root, text="Select CHID.csv", command=lambda: self.browse_file('CHID')).pack(pady=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)
        
        # Execute Button
        Button(root, text="Execute", command=self.start_processing).pack(pady=10)
        
        # Status Label
        self.status_label = Label(root, textvariable=self.status)
        self.status_label.pack(pady=5)
    
    def browse_file(self, file_type):
        """Manual file selection."""
        file = filedialog.askopenfilename(title=f"Select {file_type}.csv", filetypes=[("CSV Files", "*.csv")])
        if file:
            if file_type == 'HPID':
                self.hp_file.set(file)
            else:
                self.chid_file.set(file)
            self.update_drop_label()
    
    def on_drop(self, event):
        """Handle drag-and-drop."""
        files = event.data.split()
        if len(files) == 2:
            for f in files:
                f = f.strip('{}')
                if 'HPID' in f:
                    self.hp_file.set(f)
                elif 'CHID' in f:
                    self.chid_file.set(f)
            self.update_drop_label()
        else:
            messagebox.showerror("Error", "Please drop exactly 2 files (HPID and CHID CSVs).")
    
    def update_drop_label(self):
        """Update the drop area label with selected files."""
        hp = "No file selected" if not self.hp_file.get() else self.hp_file.get().split('/')[-1]
        chid = "No file selected" if not self.chid_file.get() else self.chid_file.get().split('/')[-1]
        self.drop_label.config(text=f"HPID: {hp}\nCHID: {chid}")
    
    def start_processing(self):
        """Start processing in a separate thread to keep GUI responsive."""
        if not self.hp_file.get() or not self.chid_file.get():
            messagebox.showerror("Error", "Please select both files first!")
            return
        
        self.status.set("Processing...")
        self.progress['value'] = 0
        threading.Thread(target=self.process_files, daemon=True).start()
    
    def detect_separator(self, file_path):
        """Detect the CSV separator by sampling the first few lines."""
        try:
            with open(file_path, 'r') as f:
                dialect = csv.Sniffer().sniff(f.read(1024))
                return dialect.delimiter
        except:
            # Fallback to comma if detection fails
            return ','
    
    def load_and_validate_csv(self, file_path, expected_type):
        """Load CSV using column positions only (1st=ID, 2nd=Lat, 3rd=Long)"""
        try:
            separator = self.detect_separator(file_path)
            df = pd.read_csv(file_path, sep=separator)
            
            # Require at least 3 columns
            if len(df.columns) < 3:
                raise ValueError(f"Need at least 3 columns in {file_path}, found {len(df.columns)}")
            
            # Map columns by position regardless of headers
            mapping = {
                'HP': {0: 'HP', 1: 'HP_LAT', 2: 'HP_LONG'},
                'CHID': {0: 'CHID', 1: 'CHID_LAT', 2: 'CHID_LONG'}
            }[expected_type]
            
            # Show mapping to user
            self.status.set(
                f"Mapping columns in {file_path.split('/')[-1]}:\n"
                f"1: {df.columns[0]} → {mapping[0]}\n"
                f"2: {df.columns[1]} → {mapping[1]}\n"
                f"3: {df.columns[2]} → {mapping[2]}"
            )
            
            # Rename columns
            df = df.rename(columns={
                df.columns[0]: mapping[0],
                df.columns[1]: mapping[1], 
                df.columns[2]: mapping[2]
            })
            
            # Keep only first 3 columns in case there are extras
            return df.iloc[:, :3]
        
        except Exception as e:
            raise ValueError(f"Error processing {file_path}: {str(e)}")

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
        return nearest_chid, min_distance, nearest_lat, nearest_long

    def process_files(self):
        """Process all HPs against all CHIDs (complete 1:1 mapping)"""
        try:
            hp_df = self.load_and_validate_csv(self.hp_file.get(), 'HP')
            chid_df = self.load_and_validate_csv(self.chid_file.get(), 'CHID')
            
            total = len(hp_df)
            results = []
            
            for i, (_, hp_row) in enumerate(hp_df.iterrows()):
                # Every HP gets processed with all CHIDs
                nearest_chid, distance, chid_lat, chid_long = self.find_nearest_chid(hp_row, chid_df)
                
                results.append({
                    'HP': hp_row['HP'],
                    'HP_LAT': hp_row['HP_LAT'],
                    'HP_LONG': hp_row['HP_LONG'],
                    'Nearest_CHID': nearest_chid,
                    'CHID_LAT': chid_lat,
                    'CHID_LONG': chid_long,
                    'Distance_km': round(distance, 5)
                })
                
                # Update progress
                progress = (i + 1) / total * 100
                self.progress['value'] = progress
                self.status.set(f"Processing {i + 1}/{total}...")
                self.root.update_idletasks()
            
            # Save results
            output_path = self.hp_file.get().replace('.csv', '_with_nearest_CHID.csv')
            pd.DataFrame(results).to_csv(output_path, index=False)
            
            self.status.set(f"Done! Saved to:\n{output_path}")
            messagebox.showinfo("Success", "Processing completed successfully!")
        
        except Exception as e:
            self.status.set("Error occurred!")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

# Run the application
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NearestCHIDApp(root)
    root.mainloop()
