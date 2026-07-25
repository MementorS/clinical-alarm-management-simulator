import matplotlib.pyplot as plt
import wfdb

from src.signal_processing.ecg import extract_heart_rate


RECORD_NAME = "b187l"
PN_DIR = "challenge-2015/training"

PLOT_START = 285.0
PLOT_END = 300.0


def main():

    # ---------------------------------------------------------
    # Load record
    # ---------------------------------------------------------

    record = wfdb.rdrecord(
        RECORD_NAME,
        pn_dir=PN_DIR,
    )

    print("Record:", RECORD_NAME)
    print("Alarm type:", record.comments[0])
    print("Reference label:", record.comments[1])
    print("Signals:", record.sig_name)
    print("Sampling frequency:", record.fs)

    # ---------------------------------------------------------
    # Extract ECG Lead II
    # ---------------------------------------------------------

    ecg_index = record.sig_name.index("II")

    ecg = record.p_signal[
        :,
        ecg_index
    ]

    # Create ECG time axis
    ecg_times = (
        range(len(ecg))
    )

    ecg_times = [
        sample / record.fs
        for sample in ecg_times
    ]

    # ---------------------------------------------------------
    # Extract HR
    # ---------------------------------------------------------

    hr_result = extract_heart_rate(
        ecg,
        record.fs,
    )

    heart_rates = hr_result[
        "heart_rates"
    ]

    heart_rate_times = hr_result[
        "heart_rate_times"
    ]

    # ---------------------------------------------------------
    # Restrict ECG to plotting window
    # ---------------------------------------------------------

    start_sample = int(
        PLOT_START * record.fs
    )

    end_sample = int(
        PLOT_END * record.fs
    )

    plot_ecg = ecg[
        start_sample:end_sample
    ]

    plot_ecg_times = ecg_times[
        start_sample:end_sample
    ]

    # ---------------------------------------------------------
    # Restrict HR to plotting window
    # ---------------------------------------------------------

    hr_mask = (
        (heart_rate_times >= PLOT_START)
        & (heart_rate_times <= PLOT_END)
    )

    plot_hr = heart_rates[
        hr_mask
    ]

    plot_hr_times = heart_rate_times[
        hr_mask
    ]

    # ---------------------------------------------------------
    # Plot ECG
    # ---------------------------------------------------------

    plt.figure(
        figsize=(14, 5)
    )

    plt.plot(
        plot_ecg_times,
        plot_ecg,
    )

    plt.axvline(
        290.0,
        linestyle="--",
        label="Evaluation window start",
    )

    plt.xlabel(
        "Time (seconds)"
    )

    plt.ylabel(
        "ECG amplitude"
    )

    plt.title(
        "b187l - ECG Lead II (285-300 seconds)"
    )

    plt.legend()

    plt.tight_layout()

    plt.show()

    # ---------------------------------------------------------
    # Plot extracted HR
    # ---------------------------------------------------------

    plt.figure(
        figsize=(14, 5)
    )

    plt.plot(
        plot_hr_times,
        plot_hr,
        marker="o",
    )

    # Simplified project thresholds
    plt.axhline(
        40,
        linestyle="--",
        label="Bradycardia threshold",
    )

    plt.axhline(
        140,
        linestyle="--",
        label="Tachycardia threshold",
    )

    plt.axvline(
        290.0,
        linestyle="--",
        label="Evaluation window start",
    )

    plt.xlabel(
        "Time (seconds)"
    )

    plt.ylabel(
        "Extracted HR (bpm)"
    )

    plt.title(
        "b187l - Extracted Heart Rate (285-300 seconds)"
    )

    plt.legend()

    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()