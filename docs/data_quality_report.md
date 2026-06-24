# Data Quality Report
**Cape Town Airbnb Dataset — Inside Airbnb Scrape (2025-09-28 / 2025-09-29)**


---

## 1. Executive Summary
This report documents the structural integrity, completeness, and quality issues identified across the four core files comprising the Cape Town Inside Airbnb dataset: `listings.csv`, `calendar.csv`, `reviews.csv`, and `neighbourhoods.csv`. Profiling confirms strong referential integrity (zero orphaned foreign keys across all files) and zero exact duplicate records. However, several material data quality issues were identified that directly affect downstream analysis: a complete absence of daily pricing in the calendar data, extreme price outliers among a small subset of listings, a structural naming convention (Ward-based neighbourhoods) requiring confirmation against the reference file, and a notable population of possible duplicate listings tied to multi-unit properties. Each issue is documented below with its quantified impact and the corresponding handling decision.

## 2. File-Level Summary

| File | Rows | Columns | Memory Footprint | Exact Duplicates | Orphaned Foreign Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `listings.csv` | 26,877 | 79 | 113.33 MB | 0 | N/A (primary entity) |
| `calendar.csv` | 9,810,109 | 7 | 1,461.71 MB | 0 | 0 |
| `reviews.csv` | 664,377 | 6 | 327.62 MB | 0 | 0 |
| `neighbourhoods.csv` | 116 | 2 | <1 MB | Not assessed | N/A |

## 3. Referential Integrity
All foreign key relationships between files were verified by set comparison of listing IDs.

| Relationship | Orphaned Records | Result |
| :--- | :--- | :--- |
| `calendar.listing_id` → `listings.id` | 0 | ✅ Fully intact |
| `reviews.listing_id` → `listings.id` | 0 | ✅ Fully intact |
| Listings with no calendar entries | 0 | ✅ Every listing has a full calendar |
| Listings with zero reviews | 6,124 (22.8% of listings) | Expected — aligns with missing-review-field analysis below |

**Conclusion:** The dataset's relational integrity is sound. Joins between listings, calendar, and reviews can be performed without risk of silent data loss from unmatched keys.

## 4. Completeness Analysis — `listings.csv`
79 columns were profiled for missingness. The following tables group findings by severity and recommended action.

### 4.1 Columns to Drop (Unusable — Near-Total Missingness)
| Column | % Missing | Decision |
| :--- | :--- | :--- |
| `calendar_updated` | 100.00% | Drop — entirely empty |
| `neighbourhood_group_cleansed` | 100.00% | Drop — entirely empty |
| `license` | 99.52% | Drop — effectively unusable |
| `host_neighbourhood` | 99.33% | Drop — effectively unusable |

### 4.2 Columns with Structural Missingness (Explainable, Not Errors)
| Column | % Missing | Likely Cause | Handling |
| :--- | :--- | :--- | :--- |
| `neighborhood_overview`, `neighbourhood` (free-text) | 52.26% | Optional host-written fields | Retain; treat null as "not provided," not imputed |
| `host_about` | 50.23% | Optional host bio field | Retain; treat null as "not provided" |
| `host_location` | 26.31% | Optional host profile field | Retain as-is |
| `host_response_rate`, `host_response_time` | 24.70% | Host has not yet responded to any inquiry | Retain as null — not equivalent to a 0% response rate |
| `review_scores_*` (all sub-dimensions), `reviews_per_month`, `last_review`, `first_review` | 22.79–22.80% | Listing has never received a review | Retain as null — confirmed consistent with the 6,124 zero-review listings identified in Section 3 |
| `host_acceptance_rate` | 14.62% | Host has not yet received a booking request | Retain as null |
| `has_availability` | 5.49% | Listing inactive at scrape time | Retain; cross-reference with `availability_365 = 0` cohort (Section 7) |
| `host_is_superhost` | 4.09% | Insufficient hosting history to qualify | Retain as null, not False |
| `bedrooms` | 2.47% | Property type does not specify (e.g., studio/loft variants) | Retain |

### 4.3 Columns Requiring Cleaning (Format Issues, Not True Missingness)
| Column | % Missing | Issue | Handling |
| :--- | :--- | :--- | :--- |
| `price` | 16.37% | Likely inactive/unlisted-price listings | Exclude from price modeling; retain for supply-side counts |
| `bathrooms` | 16.27% | Superseded by `bathrooms_text` | See Section 5 — drop in favor of authoritative text field |
| `beds` | 15.73% | Not specified by host | Retain as null |
| `description` | 1.14% | Optional field | Retain as-is |
| `bathrooms_text` | 0.88% | Minor gaps | Retain; fallback to `bathrooms` only where text is also null |

### 4.4 Negligible Missingness (No Action Required)
`host_name`, `host_since`, `host_total_listings_count`, `host_thumbnail_url`, `host_has_profile_pic`, `host_identity_verified`, `host_listings_count`, `host_verifications`, `host_picture_url` — each **0.02%** missing (6 rows); `maximum_minimum_nights`, `maximum_maximum_nights`, `minimum_minimum_nights`, `minimum_maximum_nights` — each **0.01%** (2 rows); `name` — **0.00%** (1 row). These affect a negligible number of records and require no special handling beyond standard null tolerance.

## 5. bathrooms vs. bathrooms_text — Authoritative Source Determination
| Field | % Missing |
| :--- | :--- |
| `bathrooms` (numeric) | 16.27% (4,372 rows) |
| `bathrooms_text` (string) | 0.88% (236 rows) |

Of the 4,372 rows missing `bathrooms`, 4,150 (**94.9%**) have a valid, populated `bathrooms_text` value (e.g., "1 bath," "1.5 baths," "2 baths").
* **Decision:** `bathrooms_text` is the authoritative source. Numeric bathroom counts will be extracted from `bathrooms_text` via regex pattern matching. The native `bathrooms` column will be dropped after extraction to avoid redundancy and inconsistency.

## 6. Currency and Price Field Standardization
Raw price values are stored as formatted strings (e.g., `$2,315.00`, `$51,429.00`), requiring removal of the `$` symbol and thousands-separator commas before numeric casting.
* **Currency assumption:** Although the field uses a `$`-style symbol, this is assumed to represent South African Rand (ZAR) — the local currency for a Cape Town listing — not USD. Inside Airbnb does not include a separate ISO currency code field; the `$` is a generic formatting artifact of the export, not a currency indicator. All monetary figures in this analysis should be interpreted as ZAR.

## 7. Outlier Analysis

### 7.1 Price Outliers
| Statistic | Value (ZAR) |
| :--- | :--- |
| Count (non-null) | 22,476 |
| Mean | 3,280.99 |
| Std. Dev. | 9,048.34 |
| Min | 161.00 |
| 25th percentile | 950.00 |
| Median | 1,526.00 |
| 75th percentile | 2,975.25 |
| Max | 714,885.00 |

The top 10 highest-priced listings range from **162,471 ZAR** to **714,885 ZAR** per night — between 100x and 470x the dataset median. These were cross-checked against `minimum_nights` to test whether they represented long-term rental rates mistakenly entered as nightly prices; this hypothesis was rejected, as the corresponding `minimum_nights` values were low (1–3 nights), not consistent with long-stay pricing patterns.
* **Decision:** These listings are treated as genuine extreme outliers — likely ultra-luxury properties or host data-entry errors that cannot be definitively distinguished from the data alone. They will be capped at the 99th percentile for visualization and regression modeling purposes, flagged via an `is_price_outlier` indicator, and retained unmodified in the raw and Silver-layer datasets for full transparency.

### 7.2 Minimum Nights Outliers
8 listings carry a `minimum_nights` value exceeding 365 (range: 483–999 nights), indicating long-term-rental-only listings rather than short-stay supply. Notably, several of these listings also have a null price value, consistent with the broader pattern of price missingness correlating with non-standard or inactive listings.
* **Decision:** These listings will be flagged via an `is_long_term_only` indicator and segmented out of short-stay-focused analyses (pricing distributions, occupancy, demand modeling) rather than deleted.

### 7.3 Availability Outliers
| Statistic | Value (days) |
| :--- | :--- |
| Count | 26,877 |
| Mean | 204.59 |
| Std. Dev. | 124.56 |
| Min | 0 |
| 25th percentile | 90 |
| Median | 236 |
| 75th percentile | 316 |
| Max | 365 |

* 3,209 listings (**11.9%**) show `availability_365 = 0`, indicating no bookable days in the forward-looking year — consistent with the working assumption that these represent inactive or fully host-blocked supply, not properties booked solid for 365 consecutive days.
* 1,032 listings (**3.8%**) show `availability_365 = 365`, indicating no host-imposed blocks at all — newly listed or rarely-managed properties.

### 7.4 Review Count Outliers
| Statistic | Value |
| :--- | :--- |
| Count | 26,877 |
| Mean | 24.72 |
| Std. Dev. | 48.54 |
| Min | 0 |
| 25th percentile | 1 |
| Median | 6 |
| 75th percentile | 26 |
| Max | 843 |

The most-reviewed listing has accumulated 843 reviews — well above the 75th-percentile threshold of 26 — but is not a data quality concern; high-volume reviews are consistent with long-tenured, high-turnover listings (e.g. budget private rooms with frequent short stays) rather than a scraping artifact. No corrective action required; retained as a legitimate high-demand signal.

### 7.5 Calendar-Level Inconsistencies
3 rows in `calendar.csv` show `minimum_nights` > `maximum_nights` (e.g., minimum of 2 nights against a maximum of 1 night) — a logically invalid combination. All 3 rows also carry null `price` and `adjusted_price` values, consistent with the broader calendar pricing gap described in Section 8.
* **Decision:** These 3 rows (out of 9,810,109 — a negligible **0.00003%**) will be dropped during cleaning as a documented anomaly.

## 8. Critical Limitation: Calendar Pricing Unavailable
Both `price` and `adjusted_price` in `calendar.csv` are 100% null across all 9,810,109 rows. This was confirmed not to be a parsing artifact by direct inspection of raw file contents.
**Impact:**
* No alternative daily-price field exists anywhere in the dataset.
* Seasonal and day-of-week price variation cannot be analyzed — this is an explicit scope limitation, not an approximation.
* The weekend-vs-weekday pricing hypothesis cannot be statistically tested with this dataset and will be reported as "not testable," with this limitation stated plainly, rather than substituting constant values to force a test.
* For occupancy and revenue estimation, the static base price from `listings.csv` will be used as a proxy daily rate. This is explicitly flagged in the resulting fields (`is_revenue_estimate_approximate = True`) and documented as carrying an upward bias, since it cannot reflect any seasonal discounting or dynamic pricing the host may apply in practice.

## 9. Duplicate Detection

### 9.1 Deterministic (Exact) Duplicates
* **Full-row duplicates:** 0
* **Duplicate primary keys (`listings.id`, `reviews.id`):** 0
* **Duplicate composite keys (`calendar.listing_id` + `calendar.date`):** 0
* **Conclusion:** Referential integrity is flawless (0 orphan keys).

### 9.2 Fuzzy (Geospatial) Duplicates
Initial distance-based fuzzy matching (<50m, same host) flagged 11,956 candidate pairs. However, deep-dive diagnostics revealed this high volume is a mathematical artifact of combinatorial pairing. Only 5,696 unique listings (~21% of Cape Town's supply) are actually involved. This concentration is heavily skewed toward commercial operators; the top 5 "Mega Hosts" alone account for over 40% of all generated pairs. 

* **Implication:** Because Airbnb privacy-jitters coordinates, these are not true duplicate data entries. They represent legitimate multi-unit buildings (e.g., boutique hotels, apartment blocks, or guesthouses) managed by professional hosts. They will be flagged as `is_possible_duplicate` in the pipeline for transparency, but safely retained for modeling.

## 10. Neighbourhood Reference Matching
`neighbourhoods.csv` contains 116 rows with two columns: `neighbourhood_group` (100% null, unused) and `neighbourhood` (Ward-based naming, e.g., "Ward 1," "Ward 10").
An initial automated matching pass incorrectly reported 0 matches between `listings.neighbourhood_cleansed` (87 unique Ward values) and `neighbourhoods.csv`. Manual inspection of raw string representations confirmed both files use an identical "Ward N" format with no whitespace, casing, or encoding discrepancies (e.g., 'Ward 23' in both sources).
* **Conclusion:** The original 0-match result was caused by a logic error in the automated comparison script, not a genuine data quality issue. The neighbourhood join key is reliable and requires no remediation.

## 11. Nested / Stringified Field Formats
| Field | Format | Parsing Method | Notes |
| :--- | :--- | :--- | :--- |
| `amenities` | Valid JSON array | `json.loads()` | 68 items in sampled row; 1,563 distinct amenity values found across a 2,000-row sample — high cardinality, suitable for binary flagging of common amenities rather than full one-hot encoding |
| `host_verifications` | Python list literal (not valid JSON) | `ast.literal_eval()` | 3 items in sampled row (e.g., `['email', 'phone', 'work_email']`) |

## 12. reviews.csv — Supplementary Findings
| Metric | Value |
| :--- | :--- |
| Distinct listings with ≥1 review | 20,753 |
| Distinct reviewers | 452,588 |
| Null comments | 137 (0.02%) |
| Comments under 5 characters (likely low-quality/spam) | 2,857 (0.43%) |
| Review date range | 2010-06-15 to 2025-09-28 |
| Host tenure range (`host_since`) | 2009-07-11 to 2025-09-26 |
| Calendar date range | 2025-09-28 to 2026-09-28 (365-day span, confirmed forward-looking) |

*Note: No unparseable dates were found in `host_since`, `reviews.date`, or `calendar.date`.*

## 13. Summary of Engineering Decisions
| Issue | Decision | Rationale |
| :--- | :--- | :--- |
| Unusable columns (100%/99%+ missing) | Drop `calendar_updated`, `neighbourhood_group_cleansed`, `license`, `host_neighbourhood` | No analytical value at this missingness level |
| `bathrooms` vs `bathrooms_text` | Use `bathrooms_text` as authoritative; extract numeric via regex | 94.9% of nulls in `bathrooms` are recoverable from `bathrooms_text` |
| Currency ambiguity | Assume ZAR, document explicitly | Inside Airbnb provides no ISO currency field; ZAR is the only plausible local currency |
| Extreme price outliers | Cap at 99th percentile for modeling; flag, don't delete | Preserves transparency while preventing distributional skew |
| Long-term-only listings (`minimum_nights` > 365) | Flag and segment, don't delete | Distinct supply type, not short-stay comparable |
| Calendar price 100% null | Document as a hard limitation; use static listing price as a flagged, upward-biased proxy | No alternative source exists; honesty over false precision |
| 3 invalid calendar rows (min > max nights) | Drop | Negligible volume, logically invalid |
| Fuzzy duplicate listings | Flag via indicator, don't delete | Risk of discarding legitimate multi-unit supply outweighs benefit of removal |
| Neighbourhood matching | No action needed | Confirmed false alarm from a script logic error, not a data issue |