def calculate_mosca_risk(x_years: float, y_years: float, z_years: float) -> dict:
    """Mosca's theorem: if X (data shelf-life) + Y (migration time) > Z (years until a
    cryptographically-relevant quantum computer exists), the asset is already at risk.
    """
    total = x_years + y_years
    at_risk = total > z_years
    margin = round(z_years - total, 2)
    if at_risk:
        explanation = (
            f"X+Y ({x_years}+{y_years}={total}) exceeds Z ({z_years}) by "
            f"{abs(margin)} years — data will still need protecting after a quantum "
            f"computer capable of breaking it is expected to exist. Act now."
        )
    else:
        explanation = (
            f"X+Y ({x_years}+{y_years}={total}) is within Z ({z_years}), a margin of "
            f"{margin} years — not yet at risk under current assumptions, but monitor."
        )
    return {
        "at_risk": at_risk,
        "margin": margin,
        "explanation": explanation,
    }
