# Section 02: Dataset Familiarization & Schema Definition

## 1. Business Domain Context
* **Listing:** The core asset within the Airbnb ecosystem. It represents a specific physical unit, ranging from a shared room to an entire home, available for short-term rental. The listing's attributes—such as location, property type, and amenities—are the primary drivers of its nightly price and booking demand.
* **Host:** The supply-side actor responsible for managing the listing and interacting with guests. A host can be an individual renting out a spare bedroom, or a commercial property manager operating dozens of full-time rental units. Their behavior, responsiveness, and pricing strategies directly impact the market dynamics of their neighborhood.
* **Review:** A lagging, qualitative signal of a completed stay and overall guest satisfaction. Because Airbnb does not publicly release exact booking volumes, review counts serve as the most reliable proxy for historical demand. Analyzing review frequency helps differentiate between actively booked properties and stagnant supply.
* **Calendar:** A forward-looking, 365-day time-series signal dictating the listing's future availability and minimum stay requirements. It acts as the definitive schedule for a property's potential occupancy. While typically used for dynamic pricing analysis, our specific dataset relies on the calendar primarily to forecast maximum available nights and detect host blocking behaviors.
* **Neighbourhood:** The geographic and spatial grouping (Wards) that heavily influences pricing gradients and demand clustering.

## 2. Dataset Limitations
Based on the Inside Airbnb methodology and our raw data profiling, the following systemic limitations have been identified:
* **Missing Calendar Prices:** The `price` and `adjusted_price` columns in `calendar.csv` are 100% null for this Cape Town scrape (confirmed not to be a parsing artifact). No alternative daily-price field exists in this dataset. 
* **Impact on Analysis:** Because of the missing calendar prices, daily/seasonal price variation (Section 4.3) cannot be analyzed. Furthermore, the weekend vs. weekday pricing hypothesis (H5) cannot be tested with this dataset and is explicitly flagged as "not testable."
* **Proprietary Booking Blindspot:** Actual booking data is proprietary. Review counts are used as a proxy for demand.
* **Privacy Jittering:** Geographic coordinates (latitude/longitude) are randomly anonymized by up to 150 meters by Airbnb. Neighbourhood-level aggregation is accurate, but precise address pinpointing is impossible.
* **Availability Ambiguity:** A calendar date marked as "unavailable" (`f`) could mean the listing is booked by a guest, or manually blocked by the host. 

## 3. Engineering Assumptions & Decision Log
Before proceeding to data cleaning and modeling, I established the following structural assumptions and outlier handling policies:
* **Currency:** Although the `price` field uses a `$` symbol, this is assumed to represent South African Rand (ZAR), the local currency for Cape Town, not USD. Inside Airbnb does not include a separate currency field; the `$` is a formatting artifact. All monetary figures in this report should be read as ZAR.
* **Nightly Revenue Calculation (Upward Bias):** For occupancy and revenue estimation (Section 3.3), the base price from `listings.csv` will be used as a static daily rate. I explicitly note that this likely overstates revenue estimates (an upward bias), since it cannot capture any seasonal discounting or surge pricing the host may apply in practice.
* **Price Outliers:** Approximately 10 listings show nightly prices exceeding R150,000, with low `minimum_nights` requirements. These are treated as extreme outliers—likely ultra-luxury listings or data entry anomalies. **Decision:** They will be excluded from price-distribution visualizations and regression modeling (using a 99th percentile cap) to prevent skew, but retained in the raw dataset for transparency.
* **Zero Availability:** Rows where `availability_365 = 0` are treated as inactive listings or properties where the host has manually blocked the entire calendar, rather than properties that are 100% booked by guests for the entire year.
* **Missing Reviews:** Listings with a null `last_review` date (22.79% of listings) are treated as "never booked/reviewed", rather than missing data requiring imputation.
* **Undocumented Columns:** The dataset contains `estimated_occupancy_l365d` and `estimated_revenue_l365d`, which do not appear in the official Inside Airbnb Data Dictionary. **Decision:** These are assumed to be pre-calculated estimates. To ensure analytical integrity, I will not rely on these fields and will compute my own deterministic revenue metrics using calendar availability and review counts. 


## 4. Entity Relationships & Keys
The dataset follows a standard relational Star Schema model:
* `listings.id` (PK) ↔ `reviews.listing_id` (FK): **One-to-Many** relationship (0 orphan IDs found).
* `listings.id` (PK) ↔ `calendar.listing_id` (FK): **One-to-Many** relationship (0 orphan IDs found).
* `listings.host_id`: Represents a logical entity grouping multiple listings owned by commercial operators.
* `listings.neighbourhood_cleansed` ↔ `neighbourhoods.csv` (`neighbourhood`): **Lookup join key**.

## 5. File Schemas & Data Dictionary

### 5.1 `listings.csv` (Master Dimension Table)
* **Shape:** 26,877 Rows | 79 Columns
* **Grain:** One row per unique Airbnb listing in Cape Town.
* **Note on Curated Schema:** For clarity, this schema documents the ~30 critical columns utilized for analytics and modeling. Administrative URLs and granular sub-metrics have been omitted.

| Column | Type | Sample Value | Engineering Notes, Ranges & Definitions |
| :--- | :--- | :--- | :--- |
| `id` | int64 | `15007` | Primary key. 0 duplicates found. |
| `scrape_id` | int64 | `20250928034929` | Scrape batch identifier. |
| `last_scraped` | date | `2025-09-28` | Date this listing was scraped. |
| `description` | string | `Welcome to our self-catering...` | Unstructured text. 1.14% missing. |
| `host_id` | int64 | `59072` | Foreign key referencing the host. |
| `host_since` | date | `2009-12-01` | Range spans 2009 to 2025. |
| `host_response_time` | string | `within a few hours` | 4 unique categories. 24.70% missing. |
| `host_response_rate` | string | `100%` | Range: 0-100%. Needs `%` stripped. 24.70% missing. |
| `host_is_superhost` | string | `f` | Boolean flag (`t`/`f`). 4.09% missing. |
| `host_verifications` | string | `['email', 'phone', 'work_email']` | Python list representation. Parses via `ast.literal_eval()`. |
| `neighbourhood_cleansed`| string | `Ward 23` | **Dictionary:** Geocoded using lat/long against public shapefiles. The true spatial join key. |
| `neighbourhood_group_cleansed`| float64 | `NaN` | **Candidate to drop:** 100% missing. |
| `latitude` / `longitude`| float64 | `-33.80001`, `18.46063` | WGS84 coordinates. Jittered by Airbnb for privacy. |
| `room_type` | string | `Entire home/apt` | 4 categories: Entire home/apt, Private room, Shared room, Hotel room. |
| `accommodates` | int64 | `6` | Maximum guest capacity. Range: 1 to 16+. |
| `bathrooms` | float64 | `3.0` | **Do not use:** 16.27% missing across dataset. |
| `bathrooms_text` | string | `3 baths` | **Authoritative source:** 0.88% missing. Extract numeric via regex. |
| `amenities` | string | `["Bathtub", "Fire extinguisher"...]`| Valid JSON array. Parses successfully with `json.loads()`. |
| `price` | string | `$2,315.00` | **Needs cleaning:** Strip `$`, `,`. Currency is ZAR. Range spans ~161 ZAR to >700,000 ZAR (Outliers present). |
| `minimum_nights` | int64 | `2` | Range: 1 to 999. Contains ghost listing outliers > 365 days. |
| `minimum_minimum_nights`| float64 | `2.0` | **Dictionary:** Smallest minimum_night value from calendar looking 365 days forward. |
| `minimum_nights_avg_ntm`| float64 | `2.0` | **Dictionary:** Average minimum_night value from calendar looking 365 days forward. |
| `availability_365` | int64 | `230` | **Dictionary:** Days available in the next 365 days. Range: 0 to 365. |
| `number_of_reviews` | int64 | `47` | Total lifetime reviews. Proxy for booking volume. |
| `number_of_reviews_ltm` | int64 | `1` | **Dictionary:** Reviews in the Last 12 Months. |
| `number_of_reviews_l30d`| int64 | `0` | **Dictionary:** Reviews in the Last 30 Days. |
| `review_scores_rating` | float64 | `4.81` | Range: 0.0 to 5.0. 22.79% missing (unreviewed properties). |
| `license` | string | `NaN` | **Candidate to drop:** 99.52% missing. |
| `calculated_host_listings_count`| int64 | `1` | Total listings owned by this host in the city. |
| `calculated_host_listings_count_entire_homes`| int64 | `1` | **Dictionary:** Number of Entire home/apt listings the host has in the region. |

### 5.2 `calendar.csv` (Time-Series Fact Table)
* **Shape:** 9,810,109 Rows | 7 Columns
* **Grain:** One row per listing per day (365 days forward looking).

| Column | Type | Sample Value | Engineering Notes & Dictionary Definitions |
| :--- | :--- | :--- | :--- |
| `listing_id` | int64 | `5295177` | Foreign key referencing `listings.id`. 0 orphans confirmed. |
| `date` | date | `2025-09-29` | Spans exactly 365 days (2025-09-28 to 2026-09-28). |
| `available` | string | `f` | `t` = available (5.5M rows), `f` = booked/blocked (4.3M rows). |
| `price` | float64 | `NaN` | **100% missing.** Verified in raw text. |
| `adjusted_price` | float64 | `NaN` | **100% missing.** Verified in raw text. |
| `minimum_nights` | float64 | `1.0` | Minimum stay required for this specific date. |
| `maximum_nights` | float64 | `365.0`| Maximum stay allowed for this specific date. |

### 5.3 `reviews.csv` (Transactional Fact Table)
* **Shape:** 664,377 Rows | 6 Columns
* **Grain:** One row per individual review submitted.

| Column | Type | Sample Value | Engineering Notes & Dictionary Definitions |
| :--- | :--- | :--- | :--- |
| `listing_id` | int64 | `15007` | Foreign key referencing `listings.id`. 20,753 unique listings reviewed. |
| `id` | int64 | `9223897` | Primary key for the review. 0 duplicates. |
| `date` | date | `2013-12-15` | Date spans 2010 to 2025. |
| `reviewer_id` | int64 | `7175290` | 452,588 distinct reviewers. |
| `reviewer_name` | string | `Morne` | 1 missing value. |
| `comments` | string | `We spent a fantastic two week...` | Unstructured text. 137 missing. 2,857 under 5 chars (potential spam). |

### 5.4 `neighbourhoods.csv` (Dimension Lookup)
* **Shape:** 116 Rows | 2 Columns
* **Grain:** One row per distinct neighborhood ward.

| Column | Type | Sample Value | Engineering Notes & Dictionary Definitions |
| :--- | :--- | :--- | :--- |
| `neighbourhood_group` | float64 | `NaN` | 100% missing. Will not be used. |
| `neighbourhood` | string | `Ward 1` | Clean match for `listings.neighbourhood_cleansed`. |