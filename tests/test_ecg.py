import numpy as np
import pytest

from src.signal_processing.ecg import calculate_heart_rate


def test_calculate_heart_rate_regular_60_bpm():
    """
    QRS complexes occurring once every second should produce 60 bpm.
    """

    fs = 250

    qrs_indices = np.array([
        0,
        250,
        500,
        750,
        1000
    ])

    qrs_times, rr_intervals, heart_rates = calculate_heart_rate(
        qrs_indices,
        fs
    )

    assert np.allclose(
        rr_intervals,
        [1.0, 1.0, 1.0, 1.0]
    )

    assert np.allclose(
        heart_rates,
        [60.0, 60.0, 60.0, 60.0]
    )


def test_calculate_heart_rate_regular_120_bpm():
    """
    QRS complexes occurring every 0.5 seconds should produce 120 bpm.
    """

    fs = 250

    qrs_indices = np.array([
        0,
        125,
        250,
        375,
        500
    ])

    _, rr_intervals, heart_rates = calculate_heart_rate(
        qrs_indices,
        fs
    )

    assert np.allclose(
        rr_intervals,
        [0.5, 0.5, 0.5, 0.5]
    )

    assert np.allclose(
    heart_rates,
    [120.0, 120.0, 120.0, 120.0]
)


def test_less_than_two_qrs_detections():
    """
    Fewer than two QRS detections cannot produce an RR interval.
    """

    fs = 250

    qrs_indices = np.array([100])

    qrs_times, rr_intervals, heart_rates = calculate_heart_rate(
        qrs_indices,
        fs
    )

    assert len(qrs_times) == 1
    assert len(rr_intervals) == 0
    assert len(heart_rates) == 0


def test_invalid_sampling_frequency():
    """
    Sampling frequency must be greater than zero.
    """

    qrs_indices = np.array([0, 250])

    with pytest.raises(ValueError):
        calculate_heart_rate(
            qrs_indices,
            fs=0
        )