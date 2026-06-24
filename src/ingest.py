"""
Repeatable ingestion pipeline.
Downloads, extracts, and stages Inside Airbnb data for a given city.
"""
import os
import requests
import gzip
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


CITY_CONFIG = {
    "cape_town": {
        "listings": "https://data.insideairbnb.com/south-africa/wc/cape-town/2025-09-28/data/listings.csv.gz",
        "calendar": "https://data.insideairbnb.com/south-africa/wc/cape-town/2025-09-28/data/calendar.csv.gz",
        "reviews": "https://data.insideairbnb.com/south-africa/wc/cape-town/2025-09-28/data/reviews.csv.gz",
        "neighbourhoods": "https://data.insideairbnb.com/south-africa/wc/cape-town/2025-09-28/visualisations/neighbourhoods.csv"
    }
}

BRONZE_DIR = "data/bronze"

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        logging.info(f"Already exists, skipping download: {dest_path}")
        return
    logging.info(f"Downloading {url}")
    
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, stream=True, timeout=60, headers=headers)
    response.raise_for_status()
    
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logging.info(f"Saved to {dest_path}")

def extract_gz(gz_path, out_path):
    if os.path.exists(out_path):
        logging.info(f"Already extracted: {out_path}")
        return
    logging.info(f"Extracting {gz_path}")
    with gzip.open(gz_path, "rb") as f_in:
        with open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    os.remove(gz_path)
    logging.info(f"Cleaned up compressed file: {gz_path}")

def ingest_city(city_key):
    config = CITY_CONFIG.get(city_key)
    if not config:
        logging.error(f"Configuration for {city_key} not found.")
        return
        
    os.makedirs(BRONZE_DIR, exist_ok=True)

    for file_type, url in config.items():
        filename = url.split("/")[-1]
        dest_path = os.path.join(BRONZE_DIR, filename)
        
        try:
            download_file(url, dest_path)
        except Exception as e:
            logging.error(f"Failed to download {file_type}: {e}")
            continue

        # If it's a compressed file, extract it
        if filename.endswith(".gz"):
            extracted_path = dest_path.replace(".gz", "")
            extract_gz(dest_path, extracted_path)

if __name__ == "__main__":
    print(f"{'='*50}\n STARTING DATA INGESTION (BRONZE LAYER)\n{'='*50}")
    ingest_city("cape_town")
    print(f"{'='*50}\n INGESTION COMPLETE\n{'='*50}")