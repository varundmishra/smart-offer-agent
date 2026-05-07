def calculate_compa_ratio(base_salary: float, band_midpoint: float) -> float:
    """Returns base_salary / band_midpoint rounded to 4 decimal places."""
    if band_midpoint <= 0:
        raise ValueError(f"band_midpoint must be > 0, got {band_midpoint}")
    return round(base_salary / band_midpoint, 4)
