"""
Unit tests for compensation_rules.py — no GCP credentials needed.
All salary values are in INR.
"""
import pytest
from smart_offer_agent.logic.compensation_rules import (
    apply_base_cap,
    compute_signon_bridge,
    validate_offer,
)


# ─── apply_base_cap ──────────────────────────────────────────────────────────

class TestApplyBaseCap:
    def test_proposed_below_cap_unchanged(self):
        assert apply_base_cap(4_400_000, 4_800_000) == 4_400_000

    def test_proposed_equals_cap_unchanged(self):
        assert apply_base_cap(4_800_000, 4_800_000) == 4_800_000

    def test_proposed_exceeds_cap_clamped(self):
        assert apply_base_cap(6_000_000, 4_800_000) == 4_800_000

    def test_large_overshoot_clamped(self):
        # Proposed far above peer ceiling
        assert apply_base_cap(10_000_000, 4_800_000) == 4_800_000


# ─── compute_signon_bridge ───────────────────────────────────────────────────

class TestComputeSignonBridge:
    def test_total_cash_meets_competing_offer(self):
        # No sign-on needed
        assert compute_signon_bridge(5_200_000, 5_000_000) == 0.0

    def test_total_cash_exactly_equals_competing_offer(self):
        assert compute_signon_bridge(5_000_000, 5_000_000) == 0.0

    def test_gap_bridged_correctly(self):
        # total_cash = 4,620,000  competing = 5,200,000  → bridge = 580,000
        assert compute_signon_bridge(4_620_000, 5_200_000) == 580_000.0

    def test_never_returns_negative(self):
        assert compute_signon_bridge(6_000_000, 3_000_000) == 0.0


# ─── validate_offer ──────────────────────────────────────────────────────────

class TestValidateOffer:
    def test_clean_offer_no_violations(self):
        # Senior SWE Bengaluru: band_mid = 3,500,000, max_peer ~ 4,500,000
        violations = validate_offer(
            capped_base=4_400_000,
            max_peer_base=4_800_000,
            total_first_year_value=5_200_000,
            competing_offer=5_200_000,
            compa_ratio=1.06,
        )
        assert violations == []

    def test_base_exceeds_peer_cap_violation(self):
        violations = validate_offer(
            capped_base=5_100_000,
            max_peer_base=4_800_000,
            total_first_year_value=5_200_000,
            competing_offer=5_200_000,
            compa_ratio=1.06,
        )
        assert any("cap violated" in v.lower() for v in violations)

    def test_total_value_below_competing_offer(self):
        violations = validate_offer(
            capped_base=4_400_000,
            max_peer_base=4_800_000,
            total_first_year_value=4_900_000,
            competing_offer=5_200_000,
            compa_ratio=1.06,
        )
        assert any("competing offer not met" in v.lower() for v in violations)

    def test_compa_ratio_above_upper_guard(self):
        violations = validate_offer(
            capped_base=4_400_000,
            max_peer_base=4_800_000,
            total_first_year_value=5_200_000,
            competing_offer=5_200_000,
            compa_ratio=1.25,  # > 1.20 guard
        )
        assert any("compa-ratio" in v.lower() for v in violations)

    def test_multiple_violations_all_reported(self):
        violations = validate_offer(
            capped_base=5_100_000,   # exceeds peer cap
            max_peer_base=4_800_000,
            total_first_year_value=4_000_000,  # below competing
            competing_offer=5_200_000,
            compa_ratio=1.30,  # > 1.20 guard
        )
        assert len(violations) >= 2
