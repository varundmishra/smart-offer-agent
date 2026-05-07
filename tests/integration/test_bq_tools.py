"""
Integration tests for BRD2 BigQuery tools.
Requires live GCP credentials and the your-project-id project to be seeded.

Run with:
    RUN_INTEGRATION=true pytest tests/integration/ -v
"""
import os
import pytest

if not os.getenv("RUN_INTEGRATION"):
    pytest.skip("Set RUN_INTEGRATION=true to run these tests", allow_module_level=True)

from smart_offer_agent.tools.bands_tool import get_salary_band
from smart_offer_agent.tools.market_tool import get_market_benchmarks
from smart_offer_agent.tools.peers_tool import get_internal_peers


# ─── Salary Bands ────────────────────────────────────────────────────────────

class TestGetSalaryBand:
    def test_returns_band_for_known_role_and_metro(self):
        result = get_salary_band("Senior Software Engineer", "Bengaluru")
        assert "error" not in result
        assert result["band_min"] > 0
        assert result["band_midpoint"] > result["band_min"]
        assert result["band_max"] > result["band_midpoint"]
        assert result["grade_level"] == "L5"

    def test_returns_band_for_mumbai(self):
        result = get_salary_band("Senior Software Engineer", "Mumbai")
        assert "error" not in result
        # Mumbai has 1.06x multiplier, so midpoint > Bengaluru midpoint
        blr = get_salary_band("Senior Software Engineer", "Bengaluru")
        assert result["band_midpoint"] > blr["band_midpoint"]

    def test_returns_most_recent_year(self):
        result = get_salary_band("Product Manager", "Hyderabad")
        assert "error" not in result
        assert result["effective_year"] >= 2026

    def test_unknown_role_returns_error(self):
        result = get_salary_band("Astronaut", "Bengaluru")
        assert "error" in result

    def test_unknown_metro_returns_error(self):
        result = get_salary_band("Senior Software Engineer", "San Francisco CA")
        assert "error" in result

    @pytest.mark.parametrize("metro", [
        "Bengaluru", "Mumbai", "Hyderabad", "Pune",
        "Delhi NCR", "Chennai", "Noida", "Gurugram",
    ])
    def test_all_metros_have_band_for_senior_swe(self, metro):
        result = get_salary_band("Senior Software Engineer", metro)
        assert "error" not in result, f"No band found for {metro}"


# ─── Market Benchmarks ───────────────────────────────────────────────────────

class TestGetMarketBenchmarks:
    def test_returns_benchmarks_for_known_role_and_metro(self):
        result = get_market_benchmarks("Senior Software Engineer", "Bengaluru")
        assert "error" not in result
        assert result["p25_base"] > 0
        assert result["p50_base"] > result["p25_base"]
        assert result["p75_base"] > result["p50_base"]
        assert result["p90_base"] > result["p75_base"]
        assert result["source"] == "Mercer_India_2026"

    def test_mumbai_benchmarks_higher_than_bengaluru(self):
        blr = get_market_benchmarks("Senior Software Engineer", "Bengaluru")
        mum = get_market_benchmarks("Senior Software Engineer", "Mumbai")
        assert mum["p50_base"] > blr["p50_base"]

    def test_unknown_role_returns_error(self):
        result = get_market_benchmarks("Chief Wizard", "Bengaluru")
        assert "error" in result

    @pytest.mark.parametrize("role", [
        "Senior Software Engineer", "Product Manager", "UX Designer",
        "Data Scientist", "Senior Data Scientist",
    ])
    def test_multiple_roles_have_bengaluru_benchmark(self, role):
        result = get_market_benchmarks(role, "Bengaluru")
        assert "error" not in result, f"No benchmark found for {role}"


# ─── Internal Peers ──────────────────────────────────────────────────────────

class TestGetInternalPeers:
    def test_returns_peers_with_required_fields(self):
        result = get_internal_peers("Senior Software Engineer", "Bengaluru")
        assert "error" not in result
        assert result["peer_count"] > 0
        assert result["max_peer_base"] > 0
        assert result["avg_peer_base"] > 0
        peers = result["peers"]
        assert len(peers) > 0
        for peer in peers:
            assert "employee_id" in peer
            assert "base_salary" in peer
            assert peer["base_salary"] > 0

    def test_max_peer_base_is_max_of_all_peers(self):
        result = get_internal_peers("Senior Software Engineer", "Bengaluru")
        peer_salaries = [p["base_salary"] for p in result["peers"]]
        assert result["max_peer_base"] == max(peer_salaries)

    def test_avg_peer_base_is_within_range(self):
        result = get_internal_peers("Product Manager", "Mumbai")
        peers = result["peers"]
        computed_avg = sum(p["base_salary"] for p in peers) / len(peers)
        assert abs(result["avg_peer_base"] - computed_avg) < 1  # allow rounding

    def test_unknown_role_returns_empty_peers(self):
        result = get_internal_peers("Chief Wizard", "Bengaluru")
        # Should return empty peers, not crash
        assert result["peer_count"] == 0 or "error" in result
