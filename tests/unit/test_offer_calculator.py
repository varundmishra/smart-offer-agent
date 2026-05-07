"""
Unit tests for offer_calculator.py (calculate_offer) — no GCP credentials needed.
All salary values are in INR. Scenarios use Senior Software Engineer in Bengaluru:
  band_midpoint = 3,500,000  |  typical max_peer_base ~ 4,800,000
"""
import pytest
from smart_offer_agent.tools.offer_calculator import calculate_offer


# Shared fixture values (Senior SWE, Bengaluru)
BAND_MID = 3_500_000
MAX_PEER = 4_800_000
BONUS_PCT = 0.15


class TestCalculateOfferHappyPath:
    def test_no_cap_no_signon(self):
        """Proposed base is within peer ceiling and total cash meets competing offer."""
        result = calculate_offer(
            candidate_competing_offer=5_000_000,
            proposed_base=4_400_000,
            annual_bonus_target_pct=BONUS_PCT,
            max_peer_base=MAX_PEER,
            band_midpoint=BAND_MID,
        )
        assert result["capped_base"] == 4_400_000
        assert result["base_cap_applied"] is False
        # bonus = 4,400,000 * 0.15 = 660,000
        assert result["annual_bonus"] == pytest.approx(660_000, abs=1)
        # total_cash = 4,400,000 + 660,000 = 5,060,000 ≥ competing 5,000,000
        assert result["total_cash_no_signon"] == pytest.approx(5_060_000, abs=1)
        assert result["signon_bonus_required"] == 0.0
        assert result["meets_competing_offer"] is True
        assert result["rule_violations"] == []

    def test_signon_bridges_gap(self):
        """Total cash falls short of competing offer — sign-on bonus should bridge the gap."""
        result = calculate_offer(
            candidate_competing_offer=5_200_000,
            proposed_base=4_000_000,
            annual_bonus_target_pct=BONUS_PCT,
            max_peer_base=MAX_PEER,
            band_midpoint=BAND_MID,
        )
        # total_cash = 4,000,000 + 600,000 = 4,600,000
        # sign-on = 5,200,000 - 4,600,000 = 600,000
        assert result["signon_bonus_required"] == pytest.approx(600_000, abs=1)
        assert result["total_first_year_value"] == pytest.approx(5_200_000, abs=1)
        assert result["meets_competing_offer"] is True

    def test_compa_ratio_calculated_correctly(self):
        result = calculate_offer(
            candidate_competing_offer=5_000_000,
            proposed_base=3_500_000,  # exactly at midpoint
            annual_bonus_target_pct=BONUS_PCT,
            max_peer_base=MAX_PEER,
            band_midpoint=BAND_MID,
        )
        assert result["compa_ratio"] == pytest.approx(1.0, abs=0.0001)


class TestCalculateOfferCapRule:
    def test_cap_applied_when_proposed_exceeds_peer(self):
        """FR2: base must never exceed max_peer_base."""
        result = calculate_offer(
            candidate_competing_offer=6_200_000,
            proposed_base=6_000_000,     # exceeds peer ceiling
            annual_bonus_target_pct=BONUS_PCT,
            max_peer_base=MAX_PEER,      # 4,800,000
            band_midpoint=BAND_MID,
        )
        assert result["capped_base"] == MAX_PEER
        assert result["base_cap_applied"] is True

    def test_cap_does_not_produce_peer_violation(self):
        """After capping, capped_base == max_peer_base should not trigger a violation."""
        result = calculate_offer(
            candidate_competing_offer=6_000_000,
            proposed_base=6_000_000,
            annual_bonus_target_pct=BONUS_PCT,
            max_peer_base=MAX_PEER,
            band_midpoint=BAND_MID,
        )
        cap_violations = [v for v in result["rule_violations"] if "cap violated" in v.lower()]
        assert cap_violations == []

    def test_high_compa_ratio_flagged(self):
        """Compa-ratio > 1.20 should appear in rule_violations."""
        # base = 4,400,000, midpoint = 3,500,000 → compa = 1.2571
        result = calculate_offer(
            candidate_competing_offer=5_000_000,
            proposed_base=4_400_000,
            annual_bonus_target_pct=BONUS_PCT,
            max_peer_base=MAX_PEER,
            band_midpoint=BAND_MID,
        )
        assert any("compa-ratio" in v.lower() for v in result["rule_violations"])


class TestCalculateOfferDifferentRoles:
    def test_product_manager_mumbai(self):
        """Product Manager in Mumbai: band_mid=3,180,000 (3,000,000 * 1.06), bonus=15%."""
        result = calculate_offer(
            candidate_competing_offer=7_000_000,
            proposed_base=5_800_000,
            annual_bonus_target_pct=0.15,
            max_peer_base=6_500_000,
            band_midpoint=3_180_000,
        )
        assert result["capped_base"] == 5_800_000
        assert result["base_cap_applied"] is False
        assert result["annual_bonus"] == pytest.approx(870_000, abs=1)

    def test_data_scientist_hyderabad(self):
        """Data Scientist in Hyderabad: band_mid=2,604,000 (2,800,000 * 0.93), bonus=12%."""
        result = calculate_offer(
            candidate_competing_offer=3_500_000,
            proposed_base=2_800_000,
            annual_bonus_target_pct=0.12,
            max_peer_base=3_200_000,
            band_midpoint=2_604_000,
        )
        assert result["capped_base"] == 2_800_000
        # compa = 2,800,000 / 2,604,000 ≈ 1.0753 — within guard
        assert result["compa_ratio"] == pytest.approx(1.0753, abs=0.001)
