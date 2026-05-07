#!/usr/bin/env python3
"""Load mock seed data into BigQuery tables for the Smart Offer Modeler."""
import os
import pathlib
import sys
from google.cloud import bigquery

# Reuse the same env-driven config as the agent so this script always targets
# whatever GCP project the rest of the system is pointed at.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from smart_offer_agent.config import GCP_PROJECT as PROJECT, BQ_DATASET as DATASET

SEED_DIR = pathlib.Path(__file__).parent.parent / "data" / "seed"

TABLES = {
    "market_benchmarks": SEED_DIR / "market_benchmarks.csv",
    "internal_peers": SEED_DIR / "internal_peers.csv",
    "salary_bands": SEED_DIR / "salary_bands.csv",
}

client = bigquery.Client(project=PROJECT)

for table_name, csv_path in TABLES.items():
    table_ref = f"{PROJECT}.{DATASET}.{table_name}"
    print(f"Loading {csv_path.name} → {table_ref} ...")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=False,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(csv_path, "rb") as f:
        job = client.load_table_from_file(f, table_ref, job_config=job_config)

    job.result()
    table = client.get_table(table_ref)
    print(f"  Loaded {table.num_rows} rows.")

print("\nSeed complete.")
