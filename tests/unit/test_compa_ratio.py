"""
Unit tests for compa_ratio.py — no GCP credentials needed.
All salary values are in INR.
"""
import pytest
from smart_offer_agent.logic.compa_ratio import calculate_compa_ratio


class TestCalculateCompaRatio:
    def test_at_midpoint_is_one(self):
        # base == midpoint → compa = 1.0
        assert calculate_compa_ratio(3_500_000, 3_500_000) == 1.0

    def test_below_midpoint(self):
        # 3,150,000 / 3,500,000 = 0.9
        result = calculate_compa_ratio(3_150_000, 3_500_000)
        assert result == pytest.approx(0.9, abs=0.0001)

    def test_above_midpoint(self):
        # 3,850,000 / 3,500,000 = 1.1
        result = calculate_compa_ratio(3_850_000, 3_500_000)
        assert result == pytest.approx(1.1, abs=0.0001)

    def test_rounded_to_four_decimal_places(self):
        # 4,400,000 / 3,500,000 = 1.257142...  → rounds to 1.2571
        result = calculate_compa_ratio(4_400_000, 3_500_000)
        assert result == 1.2571

    def test_zero_midpoint_raises(self):
        with pytest.raises(ValueError, match="band_midpoint must be > 0"):
            calculate_compa_ratio(4_400_000, 0)

    def test_negative_midpoint_raises(self):
        with pytest.raises(ValueError):
            calculate_compa_ratio(4_400_000, -100)
