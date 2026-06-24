"""
Cleaning and standardization pipeline.
Bronze (raw) -> Silver (cleaned, validated, type-cast).
"""
import pandas as pd
import numpy as np
import json
import ast
import re
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRAPE_DATE = pd.Timestamp("2025-09-28")



def clean_price_column(series):
    return pd.to_numeric(
        series.astype(str).str.replace(r"[\$,]", "", regex=True),
        errors="coerce"
    )

def extract_bathrooms(row):
    text = row['bathrooms_text']
    if pd.isnull(text):
        return row['bathrooms']
    match = re.search(r"(\d+\.?\d*)", str(text))
    return float(match.group(1)) if match else None

def parse_amenities(val):
    if pd.isnull(val): return []
    try: return json.loads(val)
    except Exception: return []

def parse_verifications(val):
    if pd.isnull(val): return []
    try: return ast.literal_eval(val)
    except Exception: return []

def normalize_property_type(df, min_freq_pct=1.0):
    """Collapse rare property_type categories (<1% frequency) into 'Other'."""
    freq = df['property_type'].value_counts(normalize=True) * 100
    rare_categories = freq[freq < min_freq_pct].index
    df['property_type_grouped'] = df['property_type'].apply(
        lambda x: 'Other' if x in rare_categories else x
    )
    logging.info(f"property_type normalized: {df['property_type_grouped'].nunique()} final categories")
    return df

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))

def detect_fuzzy_duplicates(df, distance_threshold_km=0.05):
    """Same host, listings within ~50m of each other."""
    potential_dupes = []
    for host_id, group in df.groupby('host_id'):
        if len(group) < 2: continue
        coords = group[['latitude', 'longitude']].values
        ids = group['id'].values
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                dist = haversine_km(*coords[i], *coords[j])
                if dist < distance_threshold_km:
                    potential_dupes.append((ids[i], ids[j]))
    return potential_dupes


# Main cleaning functions


def clean_listings(df):
    logging.info(f" Starting listings cleaning: {len(df)} rows")

    # Price Cleaning & Filtering Nulls 
    df['price_clean'] = clean_price_column(df['price'])
    before = len(df)
    df = df.dropna(subset=['price_clean']) 
    df = df[df['price_clean'] >= 0] 
    logging.info(f"Dropped {before - len(df)} rows due to missing/invalid price")

    # Outlier Capping (Retain but cap at 99th percentile)
    price_cap = df['price_clean'].quantile(0.99)
    df['price_capped'] = df['price_clean'].clip(upper=price_cap)
    df['is_price_outlier'] = df['price_clean'] > price_cap
    logging.info(f"Price capped at: {price_cap:.2f} ZAR")

    #  Fuzzy Duplicate Flagging
    fuzzy_dupes = detect_fuzzy_duplicates(df)
    if fuzzy_dupes:
        flagged_ids = set([pair[0] for pair in fuzzy_dupes] + [pair[1] for pair in fuzzy_dupes])
        df['is_possible_duplicate'] = df['id'].isin(flagged_ids)
    else:
        df['is_possible_duplicate'] = False

    #  Dates & Bathrooms
    for col in ['host_since', 'last_review', 'first_review']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['bathrooms_final'] = df.apply(extract_bathrooms, axis=1)

    #  Percents & Booleans
    df['host_response_rate'] = pd.to_numeric(df['host_response_rate'].astype(str).str.replace('%', '', regex=False), errors='coerce')
    df['host_acceptance_rate'] = pd.to_numeric(df['host_acceptance_rate'].astype(str).str.replace('%', '', regex=False), errors='coerce')
    bool_map = {'t': True, 'f': False}
    for col in ['host_is_superhost', 'host_has_profile_pic', 'host_identity_verified', 'instant_bookable']:
        df[col] = df[col].map(bool_map)

    #. Nested Fields & Property Types
    df['amenities_list'] = df['amenities'].apply(parse_amenities)
    df['amenities_count'] = df['amenities_list'].apply(len)
    df['host_verifications_list'] = df['host_verifications'].apply(parse_verifications)
    df = normalize_property_type(df)

    # Segment Ghost Listings & Standardize Geographic Fields
    df['is_long_term_only'] = df['minimum_nights'] > 365
    df['latitude'] = df['latitude'].round(5)
    df['longitude'] = df['longitude'].round(5)
    
    #  Standardize text casing and ensure a City column exists for multi-city scaling
    if 'neighbourhood_cleansed' in df.columns:
        df['neighbourhood_cleansed'] = df['neighbourhood_cleansed'].astype(str).str.title().str.strip()
    df['city'] = "Cape Town"

    #  Drop Unusable Columns
    cols_to_drop = ['calendar_updated', 'neighbourhood_group_cleansed', 'license', 'host_neighbourhood', 'bathrooms', 'amenities', 'host_verifications']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    logging.info(f"listings_clean ready. Final shape: {df.shape}")
    return df

def clean_calendar(df):
    logging.info(f" Starting calendar cleaning: {len(df)} rows")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['available_bool'] = df['available'].map({'t': True, 'f': False})

    # Drop empty price columns
    df = df.drop(columns=['price', 'adjusted_price'], errors='ignore')

    # Drop logically invalid rows
    before = len(df)
    df = df[~(df['minimum_nights'] > df['maximum_nights'])]
    logging.info(f" calendar_clean ready. Dropped {before - len(df)} logically invalid rows.")
    return df

def clean_reviews(df):
    logging.info(f" Starting reviews cleaning: {len(df)} rows")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['comments'] = df['comments'].fillna("")
    df['is_low_quality'] = df['comments'].str.len() < 5
    
    
    before = len(df)
    df = df[~df['is_low_quality']]
    logging.info(f" reviews_clean ready. Dropped {before - len(df)} spam/short comments.")
    return df

if __name__ == "__main__":
    print(f"{'='*50}\n STARTING SILVER LAYER TRANSFORMATION\n{'='*50}")
    
    listings = pd.read_csv("data/bronze/listings.csv", low_memory=False)
    calendar = pd.read_csv("data/bronze/calendar.csv", low_memory=False)
    reviews = pd.read_csv("data/bronze/reviews.csv", low_memory=False)

    listings_clean = clean_listings(listings)
    calendar_clean = clean_calendar(calendar)
    reviews_clean = clean_reviews(reviews)

    os.makedirs("data/silver", exist_ok=True)

    listings_clean.to_parquet("data/silver/listings_clean.parquet", index=False)
    calendar_clean.to_parquet("data/silver/calendar_clean.parquet", index=False)
    reviews_clean.to_parquet("data/silver/reviews_clean.parquet", index=False)

    logging.info(f"{'='*50}\nDATA CLEANING COMPLETE! Files saved to data/silver/\n{'='*50}")