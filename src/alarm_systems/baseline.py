import numpy as np


def classify_heart_rate(
    heart_rate,
    brady_threshold=40.0,
    tachy_threshold=140.0
):
    """
    Classify a single heart-rate value using simplified
    threshold-based alarm logic.

    Parameters
    ----------
    heart_rate : float
        Heart rate in beats per minute.

    brady_threshold : float
        HR values below this threshold are classified
        as Bradycardia.

    tachy_threshold : float
        HR values above this threshold are classified
        as Tachycardia.

    Returns
    -------
    str
        "BRADYCARDIA", "TACHYCARDIA", or "NORMAL".
    """

    if not np.isfinite(heart_rate):
        raise ValueError("heart_rate must be a finite number.")

    if brady_threshold >= tachy_threshold:
        raise ValueError(
            "brady_threshold must be lower than tachy_threshold."
        )

    if heart_rate < brady_threshold:
        return "BRADYCARDIA"

    if heart_rate > tachy_threshold:
        return "TACHYCARDIA"

    return "NORMAL"


def evaluate_baseline(
    heart_rates,
    brady_threshold=40.0,
    tachy_threshold=140.0
):
    """
    Evaluate a sequence of heart-rate values using the simplified
    System A baseline alarm logic.

    Each HR value is classified independently. No signal-quality,
    persistence, PLETH, or cross-parameter checks are applied.

    Parameters
    ----------
    heart_rates : array-like
        Sequence of derived heart-rate values in bpm.

    brady_threshold : float
        HR values below this threshold are classified as Bradycardia.

    tachy_threshold : float
        HR values above this threshold are classified as Tachycardia.

    Returns
    -------
    list of dict
        One result for each HR value.
    """

    heart_rates = np.asarray(heart_rates, dtype=float)

    if heart_rates.ndim != 1:
        raise ValueError("heart_rates must be one-dimensional.")

    results = []

    for index, heart_rate in enumerate(heart_rates):

        classification = classify_heart_rate(
            heart_rate,
            brady_threshold=brady_threshold,
            tachy_threshold=tachy_threshold
        )

        results.append(
            {
                "index": index,
                "heart_rate": float(heart_rate),
                "classification": classification,
                "alarm": classification != "NORMAL",
            }
        )

    return results