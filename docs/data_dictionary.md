# Data Dictionary & Modeling Caveats

## 1. Engineering & Modeling Trade-offs
A moderately denormalized star schema was used over a fully normalized snowflake schema, since this is a single-city, single-snapshot analytical dataset rather than a transactional system. DuckDB was chosen over SQLite/PostgreSQL because it requires no server process, reads Parquet/CSV natively, and is purpose-built for analytical queries — well suited to a one-week assignment with no concurrent-write requirements. Slowly changing dimensions were not implemented, since this is a single point-in-time scrape with no historical versioning need. Storage follows a Bronze/Silver/Gold (medallion) layout, with Parquet used at the Silver and Gold layers specifically to preserve datetime and boolean dtypes across pipeline stages, avoiding the type-loss that plain CSV round-tripping would introduce.

---

## 2. Gold Layer Data Dictionary
| Column | Meaning | Caveat |
|---|---|---|
| `estimated_annual_revenue_approx` | price_capped × days_unavailable | Approximation using static listing price, since calendar.csv price is 100% null in this scrape. Likely overstates true revenue (no seasonal/surge pricing captured). Flagged by `is_revenue_estimate_approximate = True`. |
| `occupancy_rate_upper_bound` | days_unavailable / total_days | Upper-bound proxy only. "Unavailable" days conflate actual guest bookings with manual host blocks — cannot be separated in this dataset. Flagged by `occupancy_includes_host_blocks = True`. |
| `price_per_bedroom` | price_capped / bedrooms | Studios (bedrooms = 0) treated as 1-bedroom equivalent to avoid division by zero. |
| `is_price_outlier` | price_clean > 99th percentile | Listings above this threshold excluded from price visualizations/regression, retained in raw data. |
| `is_possible_duplicate` | Same host, listings <50m apart | Flagged, not removed — may represent legitimate multi-unit properties. |