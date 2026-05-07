from ..logic.compensation_rules import (
    apply_base_cap,
    compute_signon_bridge,
    validate_offer,
)
from ..logic.compa_ratio import calculate_compa_ratio


def calculate_offer(
    candidate_competing_offer: float,
    proposed_base: float,
    annual_bonus_target_pct: float,
    max_peer_base: float,
    band_midpoint: float,
) -> dict:
    """
    Calculate the final offer structure and validate it against compensation rules.

    Enforces:
    - Base salary cannot exceed the highest internal peer (max_peer_base)
    - Total first-year cash must meet or exceed the competing offer
    - Any gap is bridged via sign-on bonus

    Args:
        candidate_competing_offer: Total first-year value of the candidate's competing offer.
        proposed_base: Recruiter's proposed base salary.
        annual_bonus_target_pct: Annual bonus as a decimal (e.g. 0.15 for 15%).
        max_peer_base: Highest base salary among internal peers in same role+location.
        band_midpoint: Midpoint of the salary band for Compa-Ratio calculation.

    Returns:
        dict with: capped_base, base_cap_applied, annual_bonus, total_cash_no_signon,
                   signon_bonus_required, total_first_year_value, compa_ratio,
                   meets_competing_offer, rule_violations (list).
    """
    capped_base = apply_base_cap(proposed_base, max_peer_base)
    base_cap_applied = capped_base < proposed_base

    annual_bonus = round(capped_base * annual_bonus_target_pct, 2)
    total_cash_no_signon = round(capped_base + annual_bonus, 2)
    signon_bonus_required = round(compute_signon_bridge(total_cash_no_signon, candidate_competing_offer), 2)
    total_first_year_value = round(total_cash_no_signon + signon_bonus_required, 2)
    compa_ratio = calculate_compa_ratio(capped_base, band_midpoint)
    meets_competing_offer = total_first_year_value >= candidate_competing_offer

    rule_violations = validate_offer(
        capped_base=capped_base,
        max_peer_base=max_peer_base,
        total_first_year_value=total_first_year_value,
        competing_offer=candidate_competing_offer,
        compa_ratio=compa_ratio,
    )

    return {
        "capped_base": capped_base,
        "base_cap_applied": base_cap_applied,
        "annual_bonus": annual_bonus,
        "total_cash_no_signon": total_cash_no_signon,
        "signon_bonus_required": signon_bonus_required,
        "total_first_year_value": total_first_year_value,
        "compa_ratio": compa_ratio,
        "meets_competing_offer": meets_competing_offer,
        "rule_violations": rule_violations,
    }
