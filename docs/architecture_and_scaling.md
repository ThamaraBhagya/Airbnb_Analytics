# Pipeline Architecture & Scaling Strategy


This document addresses the pipeline design, automation, and cloud-scaling requirements outlined in Sections 3.5 and 3.6 of the assignment rubric.

---

## 1. Pipeline Design & Automation (Section 3.5)

### 1.1 Configurable Pipeline
The ingestion pipeline (`src/ingest.py`) was designed with a dictionary-based configuration (`CITY_CONFIG`). Scaling this to a new city requires exactly one code change: appending the new city's URLs to the dictionary and updating the orchestrator's target variable. The downstream cleaning and enrichment scripts are city-agnostic and rely strictly on column schemas, not geographic values.

### 1.2 Incremental Processing Strategy
Currently, the pipeline executes a full-batch overwrite (Bronze -> Silver -> Gold). To transition this to an incremental (delta) processing model:
* **Watermarking:** A database table would store the `last_scraped` date of the most recently processed batch.
* **Upserts (Merge):** New data arriving in the Bronze layer would be compared against this watermark. Only rows with a newer `last_scraped` timestamp would be cleaned. Instead of a `CREATE OR REPLACE TABLE`, these rows would be merged into the Gold layer (`listing_master`) using an `UPSERT` operation keyed on `listing.id`.
* **Append-Only Facts:** The `calendar` and `reviews` datasets are append-only time series. New records would simply be appended to existing historical partitions without recalculating the past.

### 1.3 Metadata Management Layer
To track pipeline health and data freshness, a dedicated `pipeline_runs` metadata table (e.g., hosted in PostgreSQL or DuckDB) would be implemented. 
* It would track: `run_id`, `city`, `start_time`, `end_time`, `status`, `rows_ingested`, and `rows_cleaned`.
* This table would be updated automatically by the `pipeline.py` orchestrator at the start and conclusion of each run, enabling full auditability and SLA monitoring.

### 1.4 Data Lineage Trace
The transformations follow a strict Medallion flow from source to sink:
1. **Bronze (Raw):** `listings.csv`, `calendar.csv`, `reviews.csv` downloaded directly from Inside Airbnb.
2. **Silver (Cleaned):** * `listings` cleaned via `clean_listings()`: Price parsing, bathroom text extraction, outlier capping (99th percentile), and column dropping.
    * Output saved as Parquet to preserve schema and datetime types.
3. **Gold (Enriched):** * `calendar` and `reviews` aggregated to the `listing_id` level.
    * Joined onto `listings` to calculate business logic (e.g., `estimated_annual_revenue_approx`).
    * Output saved as `listing_master.parquet` and `neighbourhood_aggregates.parquet`.
4. **Warehouse (Serving):** Parquet files loaded as `dim_listing`, `fact_calendar`, and `fact_review` into DuckDB for final analytical querying.

---

## 2. Advanced & Cloud-Native Topics (Section 3.6)

### 2.1 Scaling to 50+ Cities (Architecture & Concurrency)
To scale this pipeline from a single local execution to 50+ global cities, the architecture must transition from sequential processing to distributed, cloud-native execution:
* **Parallelization:** The pipeline orchestrator (e.g., Apache Airflow or AWS Step Functions) would dynamically fan-out ingestion tasks to a scalable worker pool (e.g., AWS ECS or AWS Lambda). Each city would process concurrently in its own containerized environment.
* **Storage Partitioning:** The massive `calendar` and `reviews` datasets would no longer be stored as flat files. The S3 data lake would utilize a Hive-style partitioning strategy (e.g., `s3://airbnb-datalake/silver/calendar/city={city_name}/year={yyyy}/month={mm}/`).
* **Columnar Efficiency:** Storing the data in Parquet (already implemented in this project) becomes mandatory at scale to enable predicate pushdown, allowing analytical engines like Amazon Athena or BigQuery to scan only the necessary columns and partitions, drastically reducing compute costs.

### 2.2 Change Data Capture (CDC) for Flat Files
Traditional CDC tools (like Debezium) rely on reading database transaction logs. Because Inside Airbnb data is delivered as flat CSV scrapes, true database CDC is impossible. 
* **The Pragmatic Alternative:** We substitute CDC by comparing the `last_scraped` timestamp (or computing an MD5 hash of the row payload) against the existing Gold layer. Only records where the hash has changed or the scrape date is newer are passed downstream for processing. 

### 2.3 Production Readiness & SLA Monitoring
A pipeline is only production-ready if failures are caught before business users see them:
* **Alerting:** Using the metadata management table described above, alerting (via Slack/PagerDuty integration) would be triggered if a validation failure threshold is breached (e.g., if >5% of prices are null in a new batch).
* **SLA Tracking:** The core Service Level Agreement (SLA) for this dataset would be set to: *"Analytical data must be no older than 7 days."* A daily monitoring script would check the maximum `last_scraped` date in the Gold layer and trigger an alert if the SLA is at risk.

### 2.4 Future Improvements
Given more time and a broader scope, the following enterprise tooling would be integrated:
* **Docker:** Containerizing the pipeline (`Dockerfile` and `docker-compose.yml`) to ensure environment consistency between local development and cloud deployment.
* **dbt (Data Build Tool):** Moving the Silver-to-Gold SQL joins and transformations out of Pandas and into `dbt` to leverage automated testing, documentation, and version-controlled SQL models.
* **Great Expectations:** Implementing data quality checks as explicit code contracts (e.g., `expect_column_values_to_not_be_null('price_clean')`) before data is allowed to pass from Bronze into Silver.