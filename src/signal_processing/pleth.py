import numpy as np
from scipy.signal import find_peaks


def detect_pleth_peaks(
    pleth_signal,
    fs,
    min_peak_distance_seconds=0.3,
    prominence=0.03
):
    """
    Detect pulse peaks in a single PLETH waveform.

    This is a simplified peak-detection method for the educational
    simulator and is not a clinically validated pulse detector.

    Parameters
    ----------
    pleth_signal : array-like
        Single-channel PLETH waveform.

    fs : float
        Sampling frequency in Hz.

    min_peak_distance_seconds : float
        Minimum allowed time between detected peaks.

    prominence : float
        Minimum peak prominence used by the simplified detector.

    Returns
    -------
    numpy.ndarray
        Sample indices of detected PLETH peaks.
    """

    pleth_signal = np.asarray(
        pleth_signal,
        dtype=float
    )

    if pleth_signal.ndim != 1:
        raise ValueError(
            "pleth_signal must be one-dimensional."
        )

    if len(pleth_signal) == 0:
        raise ValueError(
            "pleth_signal cannot be empty."
        )

    if fs <= 0:
        raise ValueError(
            "fs must be greater than zero."
        )

    if min_peak_distance_seconds <= 0:
        raise ValueError(
            "min_peak_distance_seconds must be greater than zero."
        )

    if prominence <= 0:
        raise ValueError(
            "prominence must be greater than zero."
        )

    minimum_distance_samples = int(
        min_peak_distance_seconds * fs
    )

    peaks, _ = find_peaks(
        pleth_signal,
        distance=minimum_distance_samples,
        prominence=prominence
    )

    return peaks


def calculate_pulse_rate(
    peak_indices,
    fs
):
    """
    Calculate beat-to-beat pulse rate from PLETH peak indices.

    Parameters
    ----------
    peak_indices : array-like
        Sample indices of detected PLETH peaks.

    fs : float
        Sampling frequency in Hz.

    Returns
    -------
    peak_times : numpy.ndarray
        Detected peak times in seconds.

    pulse_intervals : numpy.ndarray
        Time intervals between consecutive peaks.

    pulse_rates : numpy.ndarray
        Beat-to-beat pulse rates in beats per minute.
    """

    peak_indices = np.asarray(peak_indices)

    if fs <= 0:
        raise ValueError(
            "fs must be greater than zero."
        )

    peak_times = peak_indices / fs

    if len(peak_indices) < 2:
        return (
            peak_times,
            np.array([]),
            np.array([])
        )

    pulse_intervals = np.diff(
        peak_times
    )

    valid_intervals = pulse_intervals > 0

    pulse_intervals = pulse_intervals[
        valid_intervals
    ]

    pulse_rates = (
        60.0 / pulse_intervals
    )

    return (
        peak_times,
        pulse_intervals,
        pulse_rates
    )


def extract_pulse_rate(
    pleth_signal,
    fs,
    min_peak_distance_seconds=0.3,
    prominence=0.03
):
    """
    Run the complete PLETH-to-pulse-rate pipeline.

    Returns
    -------
    dict
        Peak indices, peak times, pulse intervals,
        pulse rates, and pulse-rate timestamps.
    """

    peak_indices = detect_pleth_peaks(
        pleth_signal,
        fs,
        min_peak_distance_seconds,
        prominence
    )

    (
        peak_times,
        pulse_intervals,
        pulse_rates
    ) = calculate_pulse_rate(
        peak_indices,
        fs
    )

    return {
        "peak_indices": peak_indices,
        "peak_times": peak_times,
        "pulse_intervals": pulse_intervals,
        "pulse_rates": pulse_rates,
        "pulse_rate_times": peak_times[1:],
    }