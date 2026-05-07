"""Central runtime configuration for Smart Offer Agent.

All values are read from environment variables (loaded from `.env` by ADK at
`adk web` time, and injected by Agent Engine at deploy time).

Single source of truth — telemetry, tools, tests, and scripts all import from here.
"""

import os

# GCP project. Both `GCP_PROJECT` and the more standard `GOOGLE_CLOUD_PROJECT`
# are honoured; whichever is set wins. No silent fallback — if neither is set,
# code that needs the project (e.g. BigQuery clients, fq()) will fail loudly.
GCP_PROJECT = (
    os.environ.get("GCP_PROJECT")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or ""
)

GCP_REGION = (
    os.environ.get("GCP_REGION")
    or os.environ.get("GOOGLE_CLOUD_LOCATION")
    or "us-central1"
)

# BigQuery dataset that holds the three tables (market_benchmarks, internal_peers,
# salary_bands). Project-internal naming, but kept env-driven so non-prod
# datasets can be addressed without code changes.
BQ_DATASET = os.environ.get("BQ_DATASET", "smart_offer_ds")


def fq(table: str) -> str:
    """Fully-qualified BigQuery table reference: `project.dataset.table`."""
    return f"`{GCP_PROJECT}.{BQ_DATASET}.{table}`"
