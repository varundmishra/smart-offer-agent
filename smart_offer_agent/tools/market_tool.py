from google.cloud import bigquery

from smart_offer_agent.config import GCP_PROJECT, fq

_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=GCP_PROJECT)
    return _client


def get_market_benchmarks(role_title: str, location_metro: str) -> dict:
    """
    Retrieve external market salary benchmarks for a given role and location.

    Call this FIRST when modeling an offer to understand the external competitive landscape.

    Args:
        role_title: The job title to benchmark (e.g. "Senior Software Engineer").
        location_metro: The metro area (e.g. "San Francisco CA").

    Returns:
        dict with p25_base, p50_base, p75_base, p90_base, p50_total_cash,
        p75_total_cash, source, effective_date. Returns empty dict if no data found.
    """
    query = f"""
        SELECT
            role_title,
            location_metro,
            CAST(p25_base AS FLOAT64) AS p25_base,
            CAST(p50_base AS FLOAT64) AS p50_base,
            CAST(p75_base AS FLOAT64) AS p75_base,
            CAST(p90_base AS FLOAT64) AS p90_base,
            CAST(p50_total_cash AS FLOAT64) AS p50_total_cash,
            CAST(p75_total_cash AS FLOAT64) AS p75_total_cash,
            source,
            CAST(effective_date AS STRING) AS effective_date
        FROM {fq("market_benchmarks")}
        WHERE role_title = @role_title
          AND location_metro = @location_metro
        ORDER BY effective_date DESC
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("role_title", "STRING", role_title),
            bigquery.ScalarQueryParameter("location_metro", "STRING", location_metro),
        ]
    )
    rows = list(_get_client().query(query, job_config=job_config).result())
    if not rows:
        return {"error": f"No market benchmark data found for {role_title} in {location_metro}"}
    row = dict(rows[0])
    return row
