import duckdb
import pandas as pd

def run_analysis():
    print("RUNNING SQL ANALYTICS AGAINST DUCKDB WAREHOUSE\n")
    con = duckdb.connect("data/warehouse/airbnb.duckdb")
    
    with open("sql/analysis_queries.sql") as f:
        queries = f.read().split(";")
        
    for i, q in enumerate(queries):
        if q.strip():
            print(f"--- Query {i+1} Results ---")
            # Execute and display as a clean pandas dataframe
            display_df = con.execute(q).df()
            print(display_df.to_string())
            print("\n")
            
    con.close()

if __name__ == "__main__":
    run_analysis()