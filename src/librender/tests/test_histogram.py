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
    return np.array(hist.data(), copy=False).reshape([hist.width(), hist.height()])


def put_check(hist, time, wav, spec):
    from mitsuba.core import Point2f
    data = np.zeros(shape=hist.size())
    for i, idx in enumerate(zip(time, wav)):
        pos = np.array(Point2f(idx)) - np.array(Point2f(hist.offset()))
        size = np.array(Point2f(hist.size()))
        if (0 <= pos).all() and (pos < size).all():
            insert_idx = tuple(pos.flatten().astype(int))
            data[insert_idx] += spec[i]
    return data


def check_value(hist, time, wav, spec, atol=1e-9, verbose=False):
    vals = get_vals(hist)
    check = put_check(hist, time, wav, spec)

    # Correct structure
    correct = np.allclose(vals, check, atol=atol)

    if not correct:
        print("What we got:\n", vals)
        print("Sum:", np.sum(vals))
        print("What we want:\n", check)
        print("Sum:", np.sum(check))
    elif verbose:
        print(vals)

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

    hist = Histogram([5, 10], 1)

    assert hist.width() == 5
    assert hist.height() == 10
    assert hist.size() == [5, 10]

    hist = Histogram([20000, 4])

    assert hist.width() == 20000
    assert hist.height() == 4
    assert hist.size() == [20000, 4]

    rfilter = load_string("<rfilter version='2.0.0' type='box'/>")
    hist = Histogram([1, 1], 1, filter=rfilter)

    assert hist.border_size() == rfilter.border_size()


def test02_put_values_basic(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    # Setup histogram
    hist = Histogram([6, 3])
    hist.clear()

    time_bin = [0, 1, 3, 4, 5]
    wavelength_bin = [0, 1, 2, 0, 1]
    spectrum = [1, 1, 1, 1, 1]

    # Insert
    for i, pos in enumerate(zip(time_bin, wavelength_bin)):
        hist.put(pos, spectrum[i])

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test03_put_values_basic_masked(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    # Setup histogram
    hist = Histogram([6, 3])
    hist.clear()

    time_bin = [0, 1, 3, 4, 5]
    wavelength_bin = [0, 1, 2, 0, 1]
    spectrum = [1, 1, 1, 1, 1]
    mask = [True, False, False, True, False]

    for i, pos in enumerate(zip(time_bin, wavelength_bin)):
        hist.put(pos, spectrum[i], mask[i])
        # Apply mask to the spectrum values
        spectrum[i] *= mask[i]

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test04_put_values_basic_accumulate(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    # Setup histogram
    hist = Histogram([6, 3])
    hist.clear()

    spectrum = np.ones(20)
    wavelength_bin = np.random.randint(0, 3, size=(20,))
    time_bin = np.random.randint(0, 6, size=(20,))

    # Distribute to 5 different time steps
    for i, pos in enumerate(zip(time_bin, wavelength_bin)):
        hist.put(pos, spectrum[i])

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test05_put_packets_basic(variant_packet_acoustic):
    from mitsuba.render import Histogram
    from enoki.dynamic import Vector2f

    hist = Histogram([20, 3])
    hist.clear()

    spectrum = np.ones(shape=(10, 1))
    wavelength_bin = np.random.randint(0, 3, size=(10, 1))
    time_bin = np.random.randint(0, 20, size=(10, 1))

    pos = np.zeros(shape=(10, 2))
    pos[:, 0] = time_bin[:, 0]
    pos[:, 1] = wavelength_bin[:, 0]

    hist.put(pos, spectrum)

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test06_put_histogram_basic(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram([10, 3])
    hist2 = Histogram([10, 3])

    spectrum = np.ones(shape=(10,))
    wavelength_bin = np.random.randint(0, 3, size=(10,))
    time_bin = np.random.randint(0, 10, size=(10,))

    hist.clear()
    hist2.clear()

    for i, pos in enumerate(zip(time_bin, wavelength_bin)):
        hist2.put(pos, spectrum[i])
        hist.put(pos, spectrum[i])

    hist2.put(hist)

    check_value(hist2, time_bin, wavelength_bin, spectrum * 2)


def test07_put_histogram_offset(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram([10, 4])
    hist2 = Histogram([10, 2])
    hist3 = Histogram([10, 2])
    hist.clear()
    hist2.clear()
    hist3.clear()

    # Set the third histogram to have a wavelength bin offset of two
    hist3.set_offset([0, 2])

    spectrum = [1] * 20
    wavelength_bin = np.random.randint(0, 4, size=(20,))
    time_bin = np.random.randint(0, 10, size=(20,))

    for i, pos in enumerate(zip(time_bin, wavelength_bin)):
        hist2.put(pos, spectrum[i])
        hist3.put(pos, spectrum[i])

    hist.put(hist2)
    hist.put(hist3)

    # check_value(hist2, time_bin, wavelength_bin, spectrum, verbose=True)
    # check_value(hist3, time_bin, wavelength_bin, spectrum, verbose=True)
    check_value(hist, time_bin, wavelength_bin, spectrum)


def test08_put_packet_histogram_basic(variant_packet_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram([10, 4])
    hist2 = Histogram([10, 4])

    hist.clear()
    hist2.clear()

    spectrum = np.ones(shape=(10, 1))
    wavelength = np.random.randint(0, 4, size=(10, 1))
    time = np.random.randint(0, 10, size=(10, 1))

    pos = np.zeros(shape=(10, 2))
    pos[:, 0] = time[:, 0]
    pos[:, 1] = wavelength[:, 0]

    hist.put(pos, spectrum)
    hist2.put(hist)

    check_value(hist2, time, wavelength, spectrum)


def test09_basic_counts(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram([5, 3])

    time = [0, 1, 2, 2, 3]
    wavelength = [0, 1, 2, 2, 1]
    spectrum = [.1, .6, .7, .5, .2]

    # Setup histogram
    hist.clear()

    # Insert
    for i, pos in enumerate(zip(time, wavelength)):
        hist.put(pos, spectrum[i])

    check_value(hist, time, wavelength, spectrum)

    counts = np.array(hist.counts(), copy=False).reshape([hist.width(), hist.height()])
    print(counts)
    # Double entries
    assert counts[2][2] == 2


def test10_put_hist_counts(variant_scalar_acoustic):
    from mitsuba.render import Histogram

    hist = Histogram([3, 5])
    hist2 = Histogram([3, 5])

    wavelength = [0, 1, 2, 2, 1]
    # Weightings
    spectrum = [.1, .6, .7, .5, .2]

    time = [0, 1, 2, 2, 3]

    # Setup histogram
    hist.clear()
    hist2.clear()

    # Insert
    for i, pos in enumerate(zip(time, wavelength)):
        hist.put(pos, spectrum[i])
        hist2.put(pos, spectrum[i])

    check_value(hist, time, wavelength, spectrum)

    hist.put(hist2)

    counts = np.array(hist.counts(), copy=False).reshape([hist.width(), hist.height()])

    # Double Double entries
    assert counts[2][2] == 4
