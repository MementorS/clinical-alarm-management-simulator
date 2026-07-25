import wfdb

from src.signal_processing.ecg import extract_heart_rate
from src.signal_processing.pleth import extract_pulse_rate
from src.signal_processing.signal_quality import assess_rate_quality
from src.alarm_systems.baseline import evaluate_baseline
from src.alarm_systems.context_aware import (
    check_persistence,
    check_hr_pr_consistency,
    make_context_aware_decision,
)


RECORDS = [
    "b124s",
    "b184s",
    "t106s",
    "t469l",
]

WINDOW_START = 290.0
WINDOW_END = 300.0

REQUIRED_CONSECUTIVE = 3


for record_name in RECORDS:

    print("\n" + "=" * 70)
    print("Record:", record_name)

    # ---------------------------------------------------------
    # Load record
    # ---------------------------------------------------------

    record = wfdb.rdrecord(
        record_name,
        pn_dir="challenge-2015/training"
    )

    alarm_type = record.comments[0]
    reference_label = record.comments[1]

    print("Alarm type:", alarm_type)
    print("Reference label:", reference_label)
    print("Signals:", record.sig_name)

    # ---------------------------------------------------------
    # ECG -> HR
    # ---------------------------------------------------------

    ecg_index = record.sig_name.index("II")
    ecg = record.p_signal[:, ecg_index]

    hr_result = extract_heart_rate(
        ecg,
        record.fs
    )

    heart_rates = hr_result["heart_rates"]
    heart_rate_times = hr_result["heart_rate_times"]

    hr_window_mask = (
        (heart_rate_times >= WINDOW_START)
        & (heart_rate_times <= WINDOW_END)
    )

    window_hr = heart_rates[
        hr_window_mask
    ]

    window_hr_times = heart_rate_times[
        hr_window_mask
    ]

    # ---------------------------------------------------------
    # Baseline threshold classifications
    # ---------------------------------------------------------

    baseline_results = evaluate_baseline(
        window_hr
    )

    classifications = [
        result["classification"]
        for result in baseline_results
    ]

    # ---------------------------------------------------------
    # Determine target alarm classification
    # ---------------------------------------------------------

    if alarm_type == "Bradycardia":
        target_classification = "BRADYCARDIA"

    elif alarm_type == "Tachycardia":
        target_classification = "TACHYCARDIA"

    else:
        print(
            "Alarm type not supported by this simplified analysis."
        )
        continue

    # ---------------------------------------------------------
    # Count target threshold crossings
    # ---------------------------------------------------------

    threshold_crossings = sum(
        classification == target_classification
        for classification in classifications
    )

    # ---------------------------------------------------------
    # System A decision
    # ---------------------------------------------------------

    if threshold_crossings > 0:
        system_a_decision = "ALARM"
    else:
        system_a_decision = "NO_ALARM"

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    persistence_result = check_persistence(
        classifications,
        target_classification,
        required_consecutive=REQUIRED_CONSECUTIVE
    )

    # ---------------------------------------------------------
    # HR quality
    # ---------------------------------------------------------

    hr_quality = assess_rate_quality(
        window_hr
    )

        # ---------------------------------------------------------
    # PLETH -> PR
    # ---------------------------------------------------------

    if "PLETH" in record.sig_name:

        pleth_index = record.sig_name.index("PLETH")

        pleth = record.p_signal[:, pleth_index]

        pr_result = extract_pulse_rate(
            pleth,
            record.fs
        )

        pulse_rates = pr_result["pulse_rates"]
        pulse_rate_times = pr_result["pulse_rate_times"]

        pr_window_mask = (
            (pulse_rate_times >= WINDOW_START)
            & (pulse_rate_times <= WINDOW_END)
        )

        window_pr = pulse_rates[pr_window_mask]
        window_pr_times = pulse_rate_times[pr_window_mask]

        pr_quality = assess_rate_quality(
            window_pr
        )

        consistency_result = check_hr_pr_consistency(
            window_hr,
            window_hr_times,
            window_pr,
            window_pr_times
        )

    else:

        window_pr = []
        window_pr_times = []

        pr_quality = {
            "empty": True,
            "non_finite": False,
            "out_of_range": False,
            "sudden_jump": False,
            "caution": True,
        }

        consistency_result = {
            "matched_pairs": 0,
            "consistent_pairs": 0,
            "inconsistent_pairs": 0,
            "consistency_fraction": None,
            "matches": [],
        }

    # ---------------------------------------------------------
    # System B context-aware decision
    # IMPORTANT: outside the PLETH if/else block
    # ---------------------------------------------------------

    system_b_result = make_context_aware_decision(
        threshold_crossings=threshold_crossings,
        persistence_result=persistence_result,
        hr_quality=hr_quality,
        pr_quality=pr_quality,
        consistency_result=consistency_result,
    )

    # ---------------------------------------------------------
    # Print analysis
    # ---------------------------------------------------------
    print(
        f"\nEvaluation window: "
        f"{WINDOW_START}-{WINDOW_END} seconds"
    )

    print("\n--- BASELINE ---")

    print(
        "HR estimates:",
        len(window_hr)
    )

    print(
        "Target threshold crossings:",
        threshold_crossings
    )

    print("\n--- PERSISTENCE ---")

    print(
        "Target classification:",
        target_classification
    )

    print(
        "Maximum consecutive abnormal estimates:",
        persistence_result["max_consecutive"]
    )

    print(
        "Persistence reached:",
        persistence_result["persistent"]
    )

    print("\n--- HR QUALITY ---")

    print(
        hr_quality
    )

    print("\n--- PLETH / PR ---")

    print(
        "PR estimates:",
        len(window_pr)
    )

    print(
        "PR quality:",
        pr_quality
    )

    print("\n--- HR vs PR CONSISTENCY ---")

    print(
        "Matched pairs:",
        consistency_result["matched_pairs"]
    )

    print(
        "Consistent pairs:",
        consistency_result["consistent_pairs"]
    )

    print(
        "Inconsistent pairs:",
        consistency_result["inconsistent_pairs"]
    )

    print(
        "Consistency fraction:",
        consistency_result["consistency_fraction"]
    )

    # ---------------------------------------------------------
    # System comparison
    # ---------------------------------------------------------

    print("\n--- SYSTEM COMPARISON ---")

    print(
        "Reference label:",
        reference_label
    )

    print(
        "System A decision:",
        system_a_decision
    )

    print(
        "System B decision:",
        system_b_result["decision"]
    )

    print(
        "System B reason:",
        system_b_result["reason"]
    )