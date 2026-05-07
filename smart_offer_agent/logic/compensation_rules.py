from __future__ import annotations


def apply_base_cap(proposed_base: float, max_peer_base: float) -> float:
    """Cap proposed base at the highest internal peer salary."""
    return min(proposed_base, max_peer_base)


def compute_signon_bridge(total_cash: float, competing_offer: float) -> float:
    """Return the sign-on bonus needed to match the competing offer."""
    return max(0.0, competing_offer - total_cash)


def validate_offer(
    capped_base: float,
    max_peer_base: float,
    total_first_year_value: float,
    competing_offer: float,
    compa_ratio: float,
) -> list[str]:
    """
    Validate the offer against FR2 business rules.
    Returns a list of violation strings. Empty list means the offer is valid.
    """
    violations: list[str] = []

    if capped_base > max_peer_base:
        violations.append(
            f"Base salary cap violated: capped_base ${capped_base:,.0f} "
            f"exceeds max peer base ${max_peer_base:,.0f}"
        )

    if total_first_year_value < competing_offer:
        violations.append(
            f"Competing offer not met: total first-year value ${total_first_year_value:,.0f} "
            f"is below competing offer ${competing_offer:,.0f}"
        )

    if compa_ratio > 1.20:
        violations.append(
            f"Compa-ratio {compa_ratio:.4f} exceeds upper guard of 1.20"
        )

    return violations
