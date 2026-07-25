import wfdb

from src.signal_processing.ecg import extract_heart_rate
from src.alarm_systems.baseline import evaluate_baseline


RECORDS = [
    "b124s",
    "b184s",
    "t106s",
    "t469l",
]

WINDOW_START = 290.0
WINDOW_END = 300.0


for record_name in RECORDS:

    print("\n" + "=" * 60)
    print("Record:", record_name)

    record = wfdb.rdrecord(
        record_name,
        pn_dir="challenge-2015/training"
    )

    alarm_type = record.comments[0]
    reference_label = record.comments[1]

    print("Alarm type:", alarm_type)
    print("Reference label:", reference_label)

    # Initial baseline uses ECG Lead II only
    lead_index = record.sig_name.index("II")
    ecg = record.p_signal[:, lead_index]

    # ECG -> QRS -> RR -> HR
    hr_result = extract_heart_rate(
        ecg,
        record.fs
    )

    heart_rates = hr_result["heart_rates"]
    heart_rate_times = hr_result["heart_rate_times"]

    # Select only HR estimates completed during
    # the 290-300 second pre-alarm window
    window_mask = (
        (heart_rate_times >= WINDOW_START)
        & (heart_rate_times <= WINDOW_END)
    )

    window_heart_rates = heart_rates[window_mask]
    window_heart_rate_times = heart_rate_times[window_mask]

    # Run System A only on this window
    baseline_results = evaluate_baseline(
        window_heart_rates
    )

    brady_count = sum(
        result["classification"] == "BRADYCARDIA"
        for result in baseline_results
    )

    tachy_count = sum(
        result["classification"] == "TACHYCARDIA"
        for result in baseline_results
    )

    normal_count = sum(
        result["classification"] == "NORMAL"
        for result in baseline_results
    )

    print(
        f"Evaluation window: "
        f"{WINDOW_START}-{WINDOW_END} seconds"
    )

    print(
        "HR estimates in window:",
        len(window_heart_rates)
    )

    if len(window_heart_rates) > 0:
        print(
            "Minimum HR in window:",
            window_heart_rates.min()
        )

        print(
            "Maximum HR in window:",
            window_heart_rates.max()
        )

    print("Normal estimates:", normal_count)
    print("Bradycardia estimates:", brady_count)
    print("Tachycardia estimates:", tachy_count)