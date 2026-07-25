import numpy as np


def check_persistence(
    classifications,
    target_classification,
    required_consecutive=3
):
    """
    Check whether a target classification occurs for a required
    number of consecutive estimates.
    """

    if required_consecutive <= 0:
        raise ValueError(
            "required_consecutive must be greater than zero."
        )

    if not target_classification:
        raise ValueError(
            "target_classification cannot be empty."
        )

    current_run = 0
    max_run = 0

    for classification in classifications:

        if classification == target_classification:
            current_run += 1
            max_run = max(
                max_run,
                current_run
            )
        else:
            current_run = 0

    persistent = (
        max_run >= required_consecutive
    )

    return {
        "persistent": persistent,
        "max_consecutive": max_run,
        "required_consecutive": required_consecutive,
    }

def calculate_persistence_delay(
    classifications,
    classification_times,
    target_classification,
    required_consecutive=3,
):
    """
    Calculate the time between the first target threshold crossing
    and the first time the persistence requirement is satisfied.

    This measures the delay introduced by requiring consecutive
    abnormal estimates.

    Returns None for persistence confirmation time and delay if the
    persistence requirement is never reached.
    """

    if required_consecutive <= 0:
        raise ValueError(
            "required_consecutive must be greater than zero."
        )

    if not target_classification:
        raise ValueError(
            "target_classification cannot be empty."
        )

    if len(classifications) != len(classification_times):
        raise ValueError(
            "classifications and classification_times "
            "must have equal length."
        )

    first_threshold_time = None
    persistence_confirmation_time = None

    current_run = 0

    for classification, time in zip(
        classifications,
        classification_times,
    ):

        if classification == target_classification:

            if first_threshold_time is None:
                first_threshold_time = float(time)

            current_run += 1

            if (
                current_run >= required_consecutive
                and persistence_confirmation_time is None
            ):
                persistence_confirmation_time = float(time)
                break

        else:
            current_run = 0

    if (
        first_threshold_time is not None
        and persistence_confirmation_time is not None
    ):
        persistence_delay_seconds = (
            persistence_confirmation_time
            - first_threshold_time
        )
    else:
        persistence_delay_seconds = None

    return {
        "first_threshold_time": first_threshold_time,
        "persistence_confirmation_time":
            persistence_confirmation_time,
        "persistence_delay_seconds":
            persistence_delay_seconds,
    }








def check_hr_pr_consistency(
    heart_rates,
    heart_rate_times,
    pulse_rates,
    pulse_rate_times,
    max_time_difference=0.5,
    max_rate_difference=10.0
):
    """
    Compare ECG-derived HR estimates with PLETH-derived PR estimates
    using one-to-one nearest-time matching.

    Each HR estimate can match at most one PR estimate, and each PR
    estimate can be used at most once.

    HR-PR disagreement is contextual evidence only. It does not prove
    that an alarm is false.

    This is a simplified experimental method and is not a clinically
    validated cross-parameter consistency algorithm.
    """

    heart_rates = np.asarray(
        heart_rates,
        dtype=float
    )

    heart_rate_times = np.asarray(
        heart_rate_times,
        dtype=float
    )

    pulse_rates = np.asarray(
        pulse_rates,
        dtype=float
    )

    pulse_rate_times = np.asarray(
        pulse_rate_times,
        dtype=float
    )

    if len(heart_rates) != len(heart_rate_times):
        raise ValueError(
            "heart_rates and heart_rate_times must have equal length."
        )

    if len(pulse_rates) != len(pulse_rate_times):
        raise ValueError(
            "pulse_rates and pulse_rate_times must have equal length."
        )

    if max_time_difference <= 0:
        raise ValueError(
            "max_time_difference must be greater than zero."
        )

    if max_rate_difference < 0:
        raise ValueError(
            "max_rate_difference cannot be negative."
        )

    matches = []

    # Keep track of PR estimates that have already been matched.
    used_pr_indices = set()

    for hr, hr_time in zip(
        heart_rates,
        heart_rate_times
    ):

        if not np.isfinite(hr):
            continue

        # Find all unused, finite PR candidates.
        candidate_indices = [
            index
            for index in range(len(pulse_rates))
            if (
                index not in used_pr_indices
                and np.isfinite(pulse_rates[index])
            )
        ]

        if not candidate_indices:
            continue

        candidate_time_differences = np.array([
            abs(
                pulse_rate_times[index]
                - hr_time
            )
            for index in candidate_indices
        ])

        nearest_candidate_position = np.argmin(
            candidate_time_differences
        )

        nearest_pr_index = candidate_indices[
            nearest_candidate_position
        ]

        nearest_time_difference = (
            candidate_time_differences[
                nearest_candidate_position
            ]
        )

        if (
            nearest_time_difference
            > max_time_difference
        ):
            continue

        # Reserve this PR estimate so it cannot be reused.
        used_pr_indices.add(
            nearest_pr_index
        )

        pr = pulse_rates[
            nearest_pr_index
        ]

        rate_difference = abs(
            hr - pr
        )

        consistent = (
            rate_difference
            <= max_rate_difference
        )

        matches.append(
            {
                "hr": float(hr),
                "pr": float(pr),
                "hr_time": float(hr_time),
                "pr_time": float(
                    pulse_rate_times[
                        nearest_pr_index
                    ]
                ),
                "time_difference": float(
                    nearest_time_difference
                ),
                "rate_difference": float(
                    rate_difference
                ),
                "consistent": bool(
                    consistent
                ),
            }
        )

    matched_pairs = len(
        matches
    )

    consistent_pairs = sum(
        match["consistent"]
        for match in matches
    )

    inconsistent_pairs = (
        matched_pairs
        - consistent_pairs
    )

    if matched_pairs > 0:
        consistency_fraction = (
            consistent_pairs
            / matched_pairs
        )
    else:
        consistency_fraction = None

    return {
        "matched_pairs": matched_pairs,
        "consistent_pairs": consistent_pairs,
        "inconsistent_pairs": inconsistent_pairs,
        "consistency_fraction": consistency_fraction,
        "matches": matches,
    }


def make_context_aware_decision(
    threshold_crossings,
    persistence_result,
    hr_quality,
    pr_quality,
    consistency_result,
):
    """
    Make a simplified context-aware alarm decision.

    Possible decisions:
        NO_ALARM
        ALARM
        REVIEW

    Decision context:
        - Target threshold crossings
        - Persistence of the abnormal classification
        - ECG-derived HR quality
        - PLETH-derived PR quality

    ECG HR vs PLETH PR consistency is retained as contextual
    information but is not used as a hard alarm decision criterion.

    Preliminary inspection showed that HR/PR disagreement occurred
    in both true and false reference alarms. Therefore, disagreement
    alone is not treated as evidence that an alarm is false and does
    not automatically suppress or downgrade an alarm.

    This is an experimental educational simulator rule and is not a
    clinically validated alarm-management algorithm.
    """

    if threshold_crossings < 0:
        raise ValueError(
            "threshold_crossings cannot be negative."
        )

    if "persistent" not in persistence_result:
        raise ValueError(
            "persistence_result must contain 'persistent'."
        )

    if "caution" not in hr_quality:
        raise ValueError(
            "hr_quality must contain 'caution'."
        )

    if "caution" not in pr_quality:
        raise ValueError(
            "pr_quality must contain 'caution'."
        )

    if "consistency_fraction" not in consistency_result:
        raise ValueError(
            "consistency_result must contain 'consistency_fraction'."
        )

    # ---------------------------------------------------------
    # No target threshold evidence
    # ---------------------------------------------------------

    if threshold_crossings == 0:
        return {
            "decision": "NO_ALARM",
            "reason": "NO_TARGET_THRESHOLD_CROSSING",
        }

    # ---------------------------------------------------------
    # Persistent ECG threshold evidence with acceptable
    # ECG-derived HR quality
    #
    # HR/PR consistency remains contextual information and
    # does not override this decision.
    # ---------------------------------------------------------

    if (
        persistence_result["persistent"]
        and not hr_quality["caution"]
    ):
        return {
            "decision": "ALARM",
            "reason": (
                "PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_HR_QUALITY"
            ),
        }

    # ---------------------------------------------------------
    # Non-persistent threshold evidence with acceptable
    # HR and PR quality
    # ---------------------------------------------------------

    if (
        not persistence_result["persistent"]
        and not hr_quality["caution"]
        and not pr_quality["caution"]
    ):
        return {
            "decision": "REVIEW",
            "reason": (
                "NON_PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_QUALITY"
            ),
        }

    # ---------------------------------------------------------
    # Threshold evidence exists, but signal context raises
    # quality concerns
    # ---------------------------------------------------------

    return {
        "decision": "REVIEW",
        "reason": "THRESHOLD_EVIDENCE_WITH_QUALITY_CAUTION",
    }