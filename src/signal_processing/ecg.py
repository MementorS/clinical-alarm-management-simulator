import numpy as np
import wfdb.processing


def detect_qrs(ecg_signal, fs):
    """
    Detect QRS complexes in a single ECG signal using WFDB XQRS.

    Parameters
    ----------
    ecg_signal : array-like
        Single-channel ECG waveform.
    fs : float
        Sampling frequency in Hz.

    Returns
    -------
    numpy.ndarray
        Sample indices of detected QRS complexes.
    """

    ecg_signal = np.asarray(ecg_signal, dtype=float)

    if ecg_signal.ndim != 1:
        raise ValueError("ecg_signal must be one-dimensional.")

    if len(ecg_signal) == 0:
        raise ValueError("ecg_signal cannot be empty.")

    if fs <= 0:
        raise ValueError("fs must be greater than zero.")

    qrs_indices = wfdb.processing.xqrs_detect(
        sig=ecg_signal,
        fs=fs
    )

    return np.asarray(qrs_indices)


def calculate_heart_rate(qrs_indices, fs):
    """
    Calculate beat-to-beat heart rate from QRS sample indices.

    Parameters
    ----------
    qrs_indices : array-like
        Sample indices of detected QRS complexes.
    fs : float
        Sampling frequency in Hz.

    Returns
    -------
    qrs_times : numpy.ndarray
        QRS detection times in seconds.

    rr_intervals : numpy.ndarray
        RR intervals in seconds.

    heart_rates : numpy.ndarray
        Beat-to-beat heart rates in beats per minute.
    """

    qrs_indices = np.asarray(qrs_indices)

    if fs <= 0:
        raise ValueError("fs must be greater than zero.")

    qrs_times = qrs_indices / fs

    if len(qrs_indices) < 2:
        return qrs_times, np.array([]), np.array([])

    rr_intervals = np.diff(qrs_times)

    valid_rr = rr_intervals > 0

    rr_intervals = rr_intervals[valid_rr]

    heart_rates = 60.0 / rr_intervals

    return qrs_times, rr_intervals, heart_rates


def extract_heart_rate(ecg_signal, fs):
    """
    Run the complete ECG-to-heart-rate pipeline.

    Returns
    -------
    dict
        QRS indices, QRS times, RR intervals, heart rates,
        and heart-rate timestamps.
    """

    qrs_indices = detect_qrs(ecg_signal, fs)

    qrs_times, rr_intervals, heart_rates = calculate_heart_rate(
        qrs_indices,
        fs
    )

    return {
        "qrs_indices": qrs_indices,
        "qrs_times": qrs_times,
        "rr_intervals": rr_intervals,
        "heart_rates": heart_rates,
        "heart_rate_times": qrs_times[1:],
    }

