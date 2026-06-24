import pandas as pd

# List of your raw files
files_to_sample = [
    "data/bronze/listings.csv",
    "data/bronze/calendar.csv",
    "data/bronze/reviews.csv",
    "data/bronze/neighbourhoods.csv"
]

print(" EXTRACTING AUTHENTIC SAMPLE VALUES...\n")

for file_path in files_to_sample:
    print(f"\n{'='*60}")
    print(f"📄 FILE: {file_path}")
    print(f"{'='*60}")
    
    try:
        
        df = pd.read_csv(file_path, low_memory=False, nrows=1)
        
        
        for col in df.columns:
            sample_value = df[col].iloc[0]
            print(f"{col}: {sample_value}")
            
    except FileNotFoundError:
        print(f"❌ Could not find {file_path}. Check your path!")