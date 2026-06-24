"""
Orchestrates the full Bronze -> Silver -> Gold -> Warehouse pipeline.
"""
import logging
import sys
import subprocess
import time


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pipeline.log"), logging.StreamHandler()]
)

def run_step(script_path, step_name, max_retries=2):
    for attempt in range(1, max_retries + 1):
        logging.info(f"--- Running step: {step_name} (Attempt {attempt}/{max_retries}) ---")
        
        step_start = time.time()
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        step_duration = time.time() - step_start
        
        if result.returncode == 0:
            logging.info(f"---  {step_name} completed successfully in {step_duration:.2f}s ---")
            return True
        else:
            logging.error(f" {step_name} failed on attempt {attempt}:\n{result.stderr}")
            if attempt == max_retries:
                logging.critical(f" {step_name} failed after {max_retries} attempts. Aborting pipeline.")
                return False

def run_pipeline():
    total_start_time = time.time()
    logging.info("="*50)
    logging.info(" STARTING MEDALLION DATA PIPELINE")
    logging.info("="*50)
    
    steps = [
        ("src/ingest.py", "Ingestion (Bronze)"),
        ("src/clean.py", "Cleaning (Silver)"),
        ("src/enrich.py", "Enrichment (Gold)"),
        ("src/build_warehouse.py", "Warehouse Build"),
    ]
    
    for script_path, step_name in steps:
        success = run_step(script_path, step_name)
        if not success:
            return False
            
    total_duration = time.time() - total_start_time
    logging.info("="*50)
    logging.info(f"🎉 FULL PIPELINE COMPLETED SUCCESSFULLY IN {total_duration:.2f}s")
    logging.info("="*50)
    return True

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)