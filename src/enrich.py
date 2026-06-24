"""
Enrichment and joining pipeline.
Silver (cleaned) -> Gold (joined, aggregated, business-ready).
"""
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRAPE_DATE = pd.Timestamp("2025-09-28")

def build_review_summary(reviews_df):
    summary = reviews_df.groupby('listing_id').agg(
        review_count_computed=('id', 'count'),
        first_review_date=('date', 'min'),
        last_review_date=('date', 'max'),
        low_quality_review_count=('is_low_quality', 'sum')
    ).reset_index()
    return summary

def build_calendar_summary(calendar_df):
    """
    NOTE: 'occupancy_rate' here measures 1 - (% days marked available).
    This is an UPPER-BOUND proxy for true occupancy, since 'unavailable'
    conflates actual guest bookings with manual host-blocked dates.
    """
    summary = calendar_df.groupby('listing_id').agg(
        days_available=('available_bool', 'sum'),
        total_days=('available_bool', 'count')
    ).reset_index()
    
    
    summary['days_unavailable'] = summary['total_days'] - summary['days_available']
    summary['occupancy_rate_upper_bound'] = summary['days_unavailable'] / summary['total_days']
    return summary

def build_neighbourhood_aggregates(listings_df):
    agg = listings_df.groupby('neighbourhood_cleansed').agg(
        median_price=('price_capped', 'median'),
        listing_count=('id', 'count'),
        avg_rating=('review_scores_rating', 'mean')
    ).reset_index()
    agg['listing_density_rank'] = agg['listing_count'].rank(ascending=False)
    return agg

def derive_calculated_fields(df):
    
    df['host_tenure_years'] = (SCRAPE_DATE - df['host_since']).dt.days / 365.25
    df['review_frequency_per_year'] = df['number_of_reviews'] / df['host_tenure_years'].clip(lower=0.1)

    df['price_per_bedroom'] = df['price_capped'] / df['bedrooms'].replace(0, 1)

    return df

def build_master_table(listings_df, review_summary, calendar_summary, nbhd_agg):
    logging.info("Merging Review Summary...")
    master = listings_df.merge(review_summary, left_on='id', right_on='listing_id', how='left')
    if 'listing_id' in master.columns: master = master.drop(columns=['listing_id'])
    
    logging.info("Merging Calendar Summary...")
    master = master.merge(calendar_summary, left_on='id', right_on='listing_id', how='left')
    if 'listing_id' in master.columns: master = master.drop(columns=['listing_id'])

    logging.info("Merging Neighbourhood Aggregates...")
    master = master.merge(
        nbhd_agg[['neighbourhood_cleansed', 'median_price', 'listing_count']],
        on='neighbourhood_cleansed', how='left', suffixes=('', '_nbhd')
    )

    
    master['estimated_annual_revenue_approx'] = master['price_capped'] * master['days_unavailable']
    
    
    master['is_revenue_estimate_approximate'] = True
    master['occupancy_includes_host_blocks'] = True 

    logging.info("Deriving calculated fields...")
    master = derive_calculated_fields(master)
    return master

if __name__ == "__main__":
    print(f"{'='*50}\n STARTING GOLD LAYER ENRICHMENT\n{'='*50}")
    
    listings = pd.read_parquet("data/silver/listings_clean.parquet")
    calendar = pd.read_parquet("data/silver/calendar_clean.parquet")
    reviews = pd.read_parquet("data/silver/reviews_clean.parquet")

    review_summary = build_review_summary(reviews)
    calendar_summary = build_calendar_summary(calendar)
    nbhd_agg = build_neighbourhood_aggregates(listings)

    master = build_master_table(listings, review_summary, calendar_summary, nbhd_agg)

    os.makedirs("data/gold", exist_ok=True)
    master.to_parquet("data/gold/listing_master.parquet", index=False)
    nbhd_agg.to_parquet("data/gold/neighbourhood_aggregates.parquet", index=False)

    logging.info(f"{'='*50}\nDATA ENRICHMENT COMPLETE! Files saved to data/gold/\n{'='*50}")