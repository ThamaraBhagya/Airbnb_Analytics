--  Top 10 neighbourhoods by median price
SELECT DISTINCT neighbourhood_cleansed, median_price, listing_count
FROM dim_listing
ORDER BY median_price DESC
LIMIT 10;

--  Occupancy upper-bound by room type
SELECT room_type,
       AVG(occupancy_rate_upper_bound) AS avg_occupancy_upper_bound
FROM dim_listing
GROUP BY room_type
ORDER BY avg_occupancy_upper_bound DESC;

--  Superhost vs non-superhost average rating
SELECT host_is_superhost,
       AVG(review_scores_rating) AS avg_rating,
       COUNT(*) AS listing_count
FROM dim_listing
GROUP BY host_is_superhost;

--  Weekend vs weekday availability (NOT price — price unavailable, documented limitation)
SELECT d.is_weekend,
       AVG(CASE WHEN f.available_bool THEN 1.0 ELSE 0.0 END) AS avg_availability_rate
FROM fact_calendar f
JOIN dim_date d ON f.date = d.date
GROUP BY d.is_weekend;