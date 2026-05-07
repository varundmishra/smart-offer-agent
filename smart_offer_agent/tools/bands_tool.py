from google.cloud import bigquery

from smart_offer_agent.config import GCP_PROJECT, fq

_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=GCP_PROJECT)
    return _client


def get_salary_band(role_title: str, location_metro: str) -> dict:
    """
    Retrieve the approved salary band for a given role and location.

    The band_midpoint is used as the denominator for Compa-Ratio calculation (FR3).

    Args:
        role_title: The job title (e.g. "Senior Software Engineer").
        location_metro: The metro area (e.g. "San Francisco CA").

    Returns:
        dict with band_min, band_midpoint, band_max, grade_level, effective_year.
        Returns error dict if no band found.
    """
    # Return the most recent band available — avoids hard failures when the
    # seed data year lags behind the current calendar year.
    query = f"""
        SELECT
            CAST(band_min AS FLOAT64) AS band_min,
            CAST(band_midpoint AS FLOAT64) AS band_midpoint,
            CAST(band_max AS FLOAT64) AS band_max,
            grade_level,
            effective_year
        FROM {fq("salary_bands")}
        WHERE role_title = @role_title
          AND location_metro = @location_metro
        ORDER BY effective_year DESC
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
        return {"error": f"No salary band found for {role_title} in {location_metro}"}
    return dict(rows[0])
