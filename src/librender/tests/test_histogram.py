import math
import numpy as np
import os

import pytest
import enoki as ek
import mitsuba
import matplotlib.pyplot as plt

# Set a seed for the deterministic usage of np distributions
np.random.seed(0)


def get_vals(hist):
    return np.array(hist.data(), copy=False).reshape([hist.height(), hist.width()])


def put_check(hist, time, wav, spec, bins=None):
    """
    The expected method we want in c++
    """

    # Extract necessary variables
    h_wav_range = hist.wav_range()
    h_wav_size = h_wav_range[1] - h_wav_range[0]

    h_time_range = hist.time_range()
    h_time_size = h_time_range[1] - h_time_range[0]

    h_nbins = hist.bin_count()
    h_ntime = hist.time_step_count()

    if bins is None:
        # Define the bins and calculate indices
        bins = [i * (h_wav_size / h_nbins) + h_wav_range[0] for i in range(h_nbins + 1)]

    bin_ids = np.digitize(wav, bins).astype(int)

    time_bins = [i * (h_time_size / h_ntime) + h_time_range[0] for i in range(h_ntime + 1)]
    time_bin_ids = np.digitize(time, time_bins).astype(int)

    # Accumulate
    total = np.zeros(shape=(h_ntime, h_nbins))
    for i, t in enumerate(time):
        row = bin_ids[i]

        time_idx = time_bin_ids[i]

        # Skip invalid time/bin
        if np.logical_or(time_idx == 0, time_idx == len(time_bins)).any() \
                or np.logical_or(row == 0, row == len(bins)).any():
            continue

            # Safety for mono variant
        if not isinstance(row, np.ndarray):
            total[time_idx - 1][row - 1] += spec[i]
            continue
        for j, bin_idx in enumerate(row):
            total[time_idx - 1][bin_idx - 1] += spec[i, j]

    return total


def check_value(hist, time, wav, spec, bins=None, atol=1e-9, verbose=False):
    vals = get_vals(hist)
    check = put_check(hist, time, wav, spec, bins)

    # Correct structure
    correct = np.allclose(vals, check, atol=atol)

    if verbose or correct:
        print("What we got:\n", vals)
        print("Sum:", np.sum(vals))
        print("What we want:\n", check)
        print("Sum:", np.sum(check))

    assert correct


def plot_hist(hist):
    vals = get_vals(hist)

    labels = [f'Channel {i + 1}' for i in range(hist.bin_count())]

    plt.plot(vals)
    plt.legend(labels)
    plt.show()


def test01_construct(variant_scalar_acoustic):
    from mitsuba.core.xml import load_string
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=1000, time_range=[3, 15], wavelength_bins=np.linspace(0, 10, 10))

    assert hist.bin_count() == 9
    assert hist.time_step_count() == 1000
    assert hist.wav_range() == [0, 10]
    assert hist.time_range() == [3, 15]
    assert hist.width() == 9
    assert hist.height() == 1000
    assert hist.size() == [9, 1000]
    assert np.allclose(hist.wavelength_bins(), np.linspace(0, 10, 10))

    hist = Histogram(time_step_count=2, time_range=[0, 4], wavelength_bins=np.linspace(12, 300, 45))

    assert hist.bin_count() == 44
    assert hist.time_step_count() == 2
    assert hist.wav_range() == [12, 300]
    assert hist.time_range() == [0, 4]
    assert hist.width() == 44
    assert hist.height() == 2
    assert hist.size() == [44, 2]
    assert np.allclose(hist.wavelength_bins(), np.linspace(12, 300, 45))

    hist = Histogram(time_step_count=2, time_range=[0, 4], wavelength_bins=[100, 200, 300])

    assert hist.wavelength_bins() == [100, 200, 300]
    assert hist.wav_range() == [100, 300]
    assert hist.bin_count() == 2
    assert hist.time_step_count() == 2
    assert hist.width() == hist.bin_count()
    assert hist.height() == hist.time_step_count()
    assert hist.size() == [2, 2]

    # Test invalid construction parameters
    with pytest.raises(RuntimeError):
        Histogram(time_step_count=2, time_range=[0, 4], wavelength_bins=[1, 0])

    with pytest.raises(RuntimeError):
        Histogram(time_step_count=2, time_range=[0, 4], wavelength_bins=[-300, 10])

    with pytest.raises(RuntimeError):
        Histogram(time_step_count=2, time_range=[6, 4], wavelength_bins=[0, 1])

    with pytest.raises(RuntimeError):
        Histogram(time_step_count=2, time_range=[-1, 4], wavelength_bins=[0, 1])


def test02_put_values_basic(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[1, 2, 3])

    # Some wavelengths are out of bounds
    wavelength = [0, 1, 2, 3, 1]
    # Weight evenly
    spectrum = [1, 1, 1, 1, 10]

    time = [0, 1, 3, 4, 5]

    # Setup histogram
    hist.clear()

    # Insert
    for i, t in enumerate(time):
        hist.put(t, wavelength[i], spectrum[i])

    check_value(hist, time, wavelength, spectrum, bins=[1, 2, 3])


def test03_put_values_basic_masked(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=np.linspace(0, 10, 5))

    spectrum = [1] * 5
    wavelength = [0, 1, 2, 3, 4]
    mask = [True, False, True, False, True]
    time = [0, 1, 2, 3, 4]

    hist.clear()

    for i, t in enumerate(time):
        hist.put(t, wavelength[i], spectrum[i], mask[i])
        # Apply mask to the spectrum values
        spectrum[i] *= mask[i]

    check_value(hist, time, wavelength, spectrum)


def test04_put_values_basic_accumulate(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=np.linspace(0, 10, 5))

    spectrum = np.random.uniform(size=(20,))
    wavelength = np.random.uniform(0, 10, size=(20,))
    time = np.random.uniform(0, 5, size=(20,))

    hist.clear()

    # Distribute to 5 different time steps
    for i, t in enumerate(time):
        hist.put(t, wavelength[i], spectrum[i])

    check_value(hist, time, wavelength, spectrum)


def test05_put_packets_basic(variant_packet_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=10, time_range=[0, 10], wavelength_bins=np.linspace(0, 10, 5))

    spectrum = np.random.uniform(size=(10, 4))
    wavelengths = np.random.uniform(0, 10, size=(10, 4))
    time = np.random.uniform(0, 10, size=(10,))

    hist.clear()

    hist.put(time, wavelengths, spectrum)

    check_value(hist, time, wavelengths, spectrum)


def test06_put_values_preset_bins(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[0, 5, 10])

    spectrum = np.ones(shape=(5,))
    wavelength = np.linspace(0, 10, 5).reshape(5, )
    time = np.arange(4)

    hist.clear()

    for i in time:
        hist.put(i, wavelength[i], spectrum[i])

    check_value(hist, time, wavelength, spectrum, bins=[0, 5, 10])


def test07_put_packet_preset_bins(variant_packet_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=10, time_range=[0, 10], wavelength_bins=[0, 5, 10])

    spectrum = np.ones((10, 4))
    wavelength = np.random.uniform(0, 10, size=(10, 4))
    time = np.random.uniform(0, 10, size=(10,))

    hist.clear()

    hist.put(time, wavelength, spectrum)

    check_value(hist, time, wavelength, spectrum, bins=[0, 5, 10])


def test08_put_values_invalid_preset_bins(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[0, 5, 10])

    spectrum = np.ones(shape=(10,))
    wavelength = np.linspace(0, 20, 10)  # Not within wavelength range
    time = np.arange(-5, 5)  # Not within time range

    hist.clear()

    for i, t in enumerate(time):
        enabled = hist.put(t, wavelength[i], spectrum[i])

        if t not in range(5) or np.logical_or(wavelength[i] < 0, wavelength[i] < 10).any():
            print(t, wavelength[i])
            assert not enabled

    check_value(hist, time, wavelength, spectrum, bins=[0, 5, 10])


def test09_put_histogram_basic(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=10, time_range=[0, 10], wavelength_bins=[0, 2, 5, 10])
    hist2 = Histogram(time_step_count=10, time_range=[0, 10], wavelength_bins=[0, 2, 5, 10])

    spectrum = np.ones(shape=(10,))
    wavelength = np.random.uniform(0, 10, size=(10,))
    time = np.arange(10)

    hist.clear()
    hist2.clear()

    for t in time:
        hist2.put(t, wavelength[t], spectrum[t])
        hist.put(t, wavelength[t], spectrum[t])

    hist2.put(hist)

    check_value(hist2, time, wavelength, spectrum * 2, bins=[0, 2, 5, 10])


def test10_put_histogram_offset(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[0, 2, 5])
    hist2 = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[0, 2])
    hist3 = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[2, 5])

    # Set the third histogram to have a wavelength bin offset of one
    hist3.set_offset([1, 0])

    spectrum = [1] * 5
    wavelength = [0, 1, 2, 3, 4]
    time = [0, 1, 2, 3, 4]

    hist.clear()
    hist2.clear()
    hist3.clear()

    for t in time:
        hist2.put(t, wavelength[t], spectrum[t])
        hist3.put(t, wavelength[t], spectrum[t])

    hist.put(hist2)
    hist.put(hist3)

    check_value(hist2, time, wavelength, spectrum, bins=[0, 2])
    check_value(hist3, time, wavelength, spectrum, bins=[2, 5])
    check_value(hist, time, wavelength, spectrum, bins=[0, 2, 5])


def test11_put_packet_histogram_basic(variant_packet_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=10, time_range=[0, 10], wavelength_bins=[0, 2, 5, 10])
    hist2 = Histogram(time_step_count=10, time_range=[0, 10], wavelength_bins=[0, 2, 5, 10])

    spectrum = np.random.uniform(size=(10, 4))
    wavelength = np.random.uniform(0, 10, size=(10, 4))
    time = np.arange(10)

    hist.clear()
    hist2.clear()

    hist.put(time, wavelength, spectrum)
    hist2.put(hist)

    check_value(hist2, time, wavelength, spectrum, bins=[0, 2, 5, 10])


def test12_basic_counts(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[1, 2, 3])

    wavelength = [0, 1, 2, 2, 1]
    # Weightings
    spectrum = [.1, .6, .7, .5, .2]

    time = [0, 1, 2, 2, 3]

    # Setup histogram
    hist.clear()

    # Insert
    for i, t in enumerate(time):
        hist.put(t, wavelength[i], spectrum[i])

    check_value(hist, time, wavelength, spectrum, bins=[1, 2, 3])

    counts = np.array(hist.counts(), copy=False).reshape([hist.time_step_count(), hist.bin_count()])

    # Double entries
    assert counts[2][1] == 2


def test13_put_hist_counts(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[1, 2, 3])
    hist2 = Histogram(time_step_count=5, time_range=[0, 5], wavelength_bins=[1, 2, 3])

    wavelength = [0, 1, 2, 2, 1]
    # Weightings
    spectrum = [.1, .6, .7, .5, .2]

    time = [0, 1, 2, 2, 3]

    # Setup histogram
    hist.clear()
    hist2.clear()

    # Insert
    for i, t in enumerate(time):
        hist.put(t, wavelength[i], spectrum[i])
        hist2.put(t, wavelength[i], spectrum[i])

    check_value(hist, time, wavelength, spectrum, bins=[1, 2, 3])

    hist.put(hist2)

    counts = np.array(hist.counts(), copy=False).reshape([hist.time_step_count(), hist.bin_count()])

    # Double Double entries
    assert counts[2][1] == 4
