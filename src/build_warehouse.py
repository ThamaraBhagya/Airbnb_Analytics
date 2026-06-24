"""
Builds the analytical DuckDB warehouse from the Gold and Silver layers.
Implements a Star Schema model.
"""
import duckdb
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def build_warehouse():
    os.makedirs("data/warehouse", exist_ok=True)
    db_path = "data/warehouse/airbnb.duckdb"
    con = duckdb.connect(db_path)

    logging.info("Loading Parquet files into memory...")
    # Load Gold for the Dimension, Silver for the granular Facts
    listings = pd.read_parquet("data/gold/listing_master.parquet")
    calendar = pd.read_parquet("data/silver/calendar_clean.parquet") 
    reviews = pd.read_parquet("data/silver/reviews_clean.parquet")

    logging.info("Building Dimension & Fact Tables in DuckDB...")
    #  Dimension Table 
    con.execute("CREATE OR REPLACE TABLE dim_listing AS SELECT * FROM listings")
    
    # Fact Tables 
    con.execute("CREATE OR REPLACE TABLE fact_calendar AS SELECT * FROM calendar")
    con.execute("CREATE OR REPLACE TABLE fact_review AS SELECT * FROM reviews")

    #  Date Dimension (Created dynamically from the calendar dates)
    con.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        SELECT DISTINCT
            date,
            dayofweek(date) AS day_of_week,
            CASE WHEN dayofweek(date) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
            month(date) AS month,
            year(date) AS year
        FROM fact_calendar
    """)

    
    date_type = con.execute("SELECT typeof(date) FROM dim_date LIMIT 1").fetchone()[0]
    logging.info(f"Verification: dim_date 'date' column parsed as: {date_type} (Expected: DATE)")

    logging.info(f"✅ DuckDB Star Schema warehouse successfully built at {db_path}")
    con.close()

if __name__ == "__main__":
    build_warehouse()