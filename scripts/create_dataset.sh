#!/usr/bin/env bash
set -euo pipefail

# Load .env from the agent module so we share config with the Python code.
ENV_FILE="$(dirname "$0")/../smart_offer_agent/.env"
[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

PROJECT="${GCP_PROJECT:-${GOOGLE_CLOUD_PROJECT:-}}"
DATASET="${BQ_DATASET:-smart_offer_ds}"
SCHEMA_DIR="$(dirname "$0")/../data/schemas"

echo "Creating BigQuery dataset ${PROJECT}:${DATASET} ..."
bq mk --dataset \
  --location=US \
  --project_id="${PROJECT}" \
  "${PROJECT}:${DATASET}" 2>/dev/null || echo "Dataset already exists, skipping."

echo "Creating table: market_benchmarks ..."
bq mk --table \
  --project_id="${PROJECT}" \
  "${PROJECT}:${DATASET}.market_benchmarks" \
  "${SCHEMA_DIR}/market_benchmarks.json"

echo "Creating table: internal_peers ..."
bq mk --table \
  --project_id="${PROJECT}" \
  "${PROJECT}:${DATASET}.internal_peers" \
  "${SCHEMA_DIR}/internal_peers.json"

echo "Creating table: salary_bands ..."
bq mk --table \
  --project_id="${PROJECT}" \
  "${PROJECT}:${DATASET}.salary_bands" \
  "${SCHEMA_DIR}/salary_bands.json"

echo "Done. Tables created in ${PROJECT}:${DATASET}"
