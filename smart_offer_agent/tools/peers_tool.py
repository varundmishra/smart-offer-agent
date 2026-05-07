from google.cloud import bigquery

from smart_offer_agent.config import GCP_PROJECT, fq

_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=GCP_PROJECT)
    return _client


def get_internal_peers(role_title: str, location_metro: str) -> dict:
    """
    Retrieve internal peer salary data for a given role and location.

    Call this to understand the internal pay landscape. The max_peer_base field
    is the hard cap for the proposed base salary (FR2 business rule).

    Args:
        role_title: The job title to look up (e.g. "Senior Software Engineer").
        location_metro: The metro area (e.g. "San Francisco CA").

    Returns:
        dict with:
          - peers: list of peer records (employee_id, peer_name, years_experience,
                   years_at_company, base_salary, annual_bonus_target_pct, performance_rating)
          - max_peer_base: highest base salary in the peer group (the FR2 cap)
          - avg_peer_base: average base salary in the peer group
          - peer_count: number of peers found
        Returns empty peers list if no data found.
    """
    query = f"""
        SELECT
            employee_id,
            peer_name,
            years_experience,
            years_at_company,
            CAST(base_salary AS FLOAT64) AS base_salary,
            CAST(annual_bonus_target_pct AS FLOAT64) AS annual_bonus_target_pct,
            IFNULL(performance_rating, 'Unknown') AS performance_rating
        FROM {fq("internal_peers")}
        WHERE role_title = @role_title
          AND location_metro = @location_metro
        ORDER BY base_salary DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("role_title", "STRING", role_title),
            bigquery.ScalarQueryParameter("location_metro", "STRING", location_metro),
        ]
    )
    rows = [dict(r) for r in _get_client().query(query, job_config=job_config).result()]

    if not rows:
        return {
            "peers": [],
            "max_peer_base": 0.0,
            "avg_peer_base": 0.0,
            "peer_count": 0,
            "warning": f"No internal peers found for {role_title} in {location_metro}",
        }

    salaries = [r["base_salary"] for r in rows]
    return {
        "peers": rows,
        "max_peer_base": max(salaries),
        "avg_peer_base": round(sum(salaries) / len(salaries), 2),
        "peer_count": len(rows),
    }
