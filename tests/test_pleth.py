import numpy as np
import pytest

from src.signal_processing.pleth import calculate_pulse_rate


def test_calculate_pulse_rate_regular_60_bpm():
    """
    Pulse peaks occurring once every second should produce 60 bpm.
    """

    fs = 250

    peak_indices = np.array([
        0,
        250,
        500,
        750,
        1000
    ])

    peak_times, pulse_intervals, pulse_rates = calculate_pulse_rate(
        peak_indices,
        fs
    )

    assert np.allclose(
        pulse_intervals,
        [1.0, 1.0, 1.0, 1.0]
    )

    assert np.allclose(
        pulse_rates,
        [60.0, 60.0, 60.0, 60.0]
    )


def test_calculate_pulse_rate_regular_120_bpm():
    """
    Pulse peaks occurring every 0.5 seconds should produce 120 bpm.
    """

    fs = 250

    peak_indices = np.array([
        0,
        125,
        250,
        375,
        500
    ])

    _, pulse_intervals, pulse_rates = calculate_pulse_rate(
        peak_indices,
        fs
    )

    assert np.allclose(
        pulse_intervals,
        [0.5, 0.5, 0.5, 0.5]
    )

    assert np.allclose(
        pulse_rates,
        [120.0, 120.0, 120.0, 120.0]
    )


def test_less_than_two_pleth_peaks():
    """
    Fewer than two peaks cannot produce a pulse interval.
    """

    fs = 250

    peak_indices = np.array([100])

    peak_times, pulse_intervals, pulse_rates = calculate_pulse_rate(
        peak_indices,
        fs
    )

    assert len(peak_times) == 1
    assert len(pulse_intervals) == 0
    assert len(pulse_rates) == 0


def test_invalid_sampling_frequency():
    """
    Sampling frequency must be greater than zero.
    """

    peak_indices = np.array([0, 250])

    with pytest.raises(ValueError):
        calculate_pulse_rate(
            peak_indices,
            fs=0
        )