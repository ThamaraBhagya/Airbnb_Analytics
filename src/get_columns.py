import pandas as pd
import os


RAW_DATA_DIR = "data/bronze/"
FILES_TO_CHECK = [
    "listings.csv", 
    "calendar.csv", 
    "reviews.csv",
    "neighbourhoods.csv"
]

print("EXTRACTING COLUMN NAMES...\n")

for file_name in FILES_TO_CHECK:
    file_path = os.path.join(RAW_DATA_DIR, file_name)
    
    if os.path.exists(file_path):
        
        df_header = pd.read_csv(file_path, nrows=0, low_memory=False)
        columns = df_header.columns.tolist()
        
        print(f" {file_name} ({len(columns)} columns):")
        print(columns)
        print("-" * 80)
    else:
        print(f" File {file_name} not found in {RAW_DATA_DIR}")