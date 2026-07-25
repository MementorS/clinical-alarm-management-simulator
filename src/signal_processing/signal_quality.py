import numpy as np


def assess_rate_quality(
    rates,
    min_valid_rate=20.0,
    max_valid_rate=220.0,
    max_rate_jump=50.0
):
    """
    Apply simple quality checks to a sequence of derived HR or PR values.

    These checks identify potentially unreliable rate estimates.
    They do not determine whether an alarm is true or false and are
    not clinically validated signal-quality indices.

    Parameters
    ----------
    rates : array-like
        Sequence of derived heart-rate or pulse-rate estimates.

    min_valid_rate : float
        Lower plausibility bound used by this simulator.

    max_valid_rate : float
        Upper plausibility bound used by this simulator.

    max_rate_jump : float
        Maximum allowed change between consecutive rate estimates
        before a sudden-jump flag is raised.

    Returns
    -------
    dict
        Quality assessment containing individual flags and an
        overall caution flag.
    """

    rates = np.asarray(rates, dtype=float)

    if rates.ndim != 1:
        raise ValueError(
            "rates must be one-dimensional."
        )

    if min_valid_rate >= max_valid_rate:
        raise ValueError(
            "min_valid_rate must be lower than max_valid_rate."
        )

    if max_rate_jump <= 0:
        raise ValueError(
            "max_rate_jump must be greater than zero."
        )

    if len(rates) == 0:
        return {
            "empty": True,
            "non_finite": False,
            "out_of_range": False,
            "sudden_jump": False,
            "caution": True,
        }

    non_finite = bool(
        np.any(~np.isfinite(rates))
    )

    finite_rates = rates[
        np.isfinite(rates)
    ]

    out_of_range = bool(
        np.any(
            (finite_rates < min_valid_rate)
            | (finite_rates > max_valid_rate)
        )
    )

    if len(finite_rates) >= 2:
        rate_changes = np.abs(
            np.diff(finite_rates)
        )

        sudden_jump = bool(
            np.any(
                rate_changes > max_rate_jump
            )
        )

    else:
        sudden_jump = False

    caution = (
        non_finite
        or out_of_range
        or sudden_jump
    )

    return {
        "empty": False,
        "non_finite": non_finite,
        "out_of_range": out_of_range,
        "sudden_jump": sudden_jump,
        "caution": caution,
    }