import math
import numpy as np
import os

import pytest
import enoki as ek
import mitsuba
import matplotlib.pyplot as plt


def get_vals(hist):
    return np.array(hist.data(), copy=False).reshape([hist.time_step_count(), hist.bin_count()])


def put_check(hist, time, wav, spec):
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

    # Define the bins and calculate indices
    bins = [i * (h_wav_size / h_nbins) + h_wav_range[0] for i in range(h_nbins)]
    bin_ids = np.digitize(wav, bins).astype(int)

    time_bins = [i * (h_time_size / h_ntime) + h_time_range[0] for i in range(h_ntime)]
    time_bin_ids = np.digitize(time, time_bins).astype(int)

    # Accumulate
    total = np.zeros(shape=(h_ntime, h_nbins))
    for i, t in enumerate(time):
        row = bin_ids[i]
        time_idx = time_bin_ids[i]
        for j, b in enumerate(row):
            total[time_idx - 1][b - 1] += spec[i, j]

    return total


def check_value(hist, time, wav, spec, atol=1e-9):
    vals = get_vals(hist)
    check = put_check(hist, time, wav, spec)

    assert np.allclose(vals, check, atol=atol)


def plot_hist(hist):
    vals = get_vals(hist)

    labels = [f'Channel {i + 1}' for i in range(hist.bin_count())]

    plt.plot(vals)
    plt.legend(labels)
    plt.show()


def test01_construct(variant_scalar_rgb):
    from mitsuba.core.xml import load_string
    from mitsuba.render import Histogram

    hist = Histogram(bin_count=10, time_step_count=1000, wav_range=[0, 10], time_range=[3, 15])

    assert hist.bin_count() == 10
    assert hist.time_step_count() == 1000
    assert hist.wav_range() == [0, 10]
    assert hist.time_range() == [3, 15]

    hist = Histogram(bin_count=45, time_step_count=2, wav_range=[12, 300], time_range=[0, 4])

    assert hist.bin_count() == 45
    assert hist.time_step_count() == 2
    assert hist.wav_range() == [12, 300]
    assert hist.time_range() == [0, 4]

    # Test invalid construction parameters
    with pytest.raises(RuntimeError):
        Histogram(bin_count=45, time_step_count=2, wav_range=[300, 10], time_range=[0, 4])

    with pytest.raises(RuntimeError):
        Histogram(bin_count=45, time_step_count=2, wav_range=[-300, 10], time_range=[0, 4])

    with pytest.raises(RuntimeError):
        Histogram(bin_count=45, time_step_count=2, wav_range=[300, 10], time_range=[6, 4])

    with pytest.raises(RuntimeError):
        Histogram(bin_count=45, time_step_count=2, wav_range=[-300, 10], time_range=[-1, 4])


def test02_put_values_basic(variant_scalar_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(bin_count=5, time_step_count=10, wav_range=[5, 15], time_range=[0, 10])

    # Sample wavelengths from centered gaussian
    wavelength = np.random.normal(loc=10, scale=2, size=(10, 4))

    # Cut off bottom and top
    wavelength[wavelength < 5] = 5
    wavelength[wavelength > 14] = 14

    # Generate some decreasing rows
    spectrum = (np.tile(np.arange(10, 0, -1), (4, 1)) * np.arange(1, 5)[np.newaxis].transpose()).transpose()

    # Setup histogram
    hist.clear()

    # Insert
    for i in range(10):
        hist.put(i, wavelength[i], spectrum[i])

    check_value(hist, np.arange(10), wavelength, spectrum)


def test03_put_values_basic_masked(variant_scalar_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(bin_count=4, time_step_count=10, wav_range=[0, 10], time_range=[0, 10])

    spectrum = np.random.uniform(size=(10, 4))
    wavelength = np.random.uniform(0, 10, size=(10, 4))

    mask = np.random.uniform(size=(10,)) > 0.3

    hist.clear()

    for i in range(10):
        hist.put(i, wavelength[i], spectrum[i], not mask[i])

    spectrum[mask] = 0.

    check_value(hist, np.arange(10), wavelength, spectrum)


def test04_put_values_basic_accumulate(variant_scalar_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(bin_count=4, time_step_count=5, wav_range=[0, 10], time_range=[0, 5])

    spectrum = np.random.uniform(size=(20, 4))
    wavelength = np.random.uniform(0, 10, size=(20, 4))
    time = np.random.uniform(0, 5, size=(20,))

    hist.clear()

    # Distribute to 5 different time steps
    for i, t in enumerate(time):
        hist.put(t, wavelength[i], spectrum[i])

    check_value(hist, time, wavelength, spectrum)


def test05_put_packets_basic(variant_packet_spectral):
    from mitsuba.render import Histogram

    hist = Histogram(bin_count=4, time_step_count=10, wav_range=[0, 10], time_range=[0, 10])

    spectrum = np.random.uniform(size=(10, 4))
    wavelengths = np.random.uniform(0, 10, size=(10, 4))
    time = np.random.uniform(0, 10, size=(10,))

    hist.clear()

    hist.put(time, wavelengths, spectrum)

    check_value(hist, time, wavelengths, spectrum)
