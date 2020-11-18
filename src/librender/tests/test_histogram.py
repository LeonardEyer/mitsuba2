import math
import numpy as np
import os

import pytest
import enoki as ek
import mitsuba
import matplotlib.pyplot as plt


def check_value(hist, arr, atol=1e-9):
    vals = np.array(hist.data(), copy=False).reshape([hist.time_step_count(), hist.channel_count()])

    ref = np.empty(shape=vals.shape)
    ref[:] = arr  # Allows to benefit from broadcasting when passing `arr`

    assert ek.allclose(vals, arr)

    # Easier to read in case of assert failure
    # for k in range(vals.shape[1]):
    #    assert ek.allclose(vals[:, k], ref[:, k], atol=atol), \
    #        'Channel %d:\n' % (k) + str(vals[:, k]) \
    #        + '\n\n' + str(ref[:, k])


def plot_hist(hist):
    vals = np.array(hist.data(), copy=False).reshape([hist.time_step_count(), hist.channel_count()])

    labels = [f'Channel {i+1}' for i in range(hist.channel_count())]

    plt.plot(vals)
    plt.legend(labels)
    plt.show()


def test01_construct(variant_scalar_spectral):
    from mitsuba.core.xml import load_string
    from mitsuba.render import Histogram

    hist = Histogram(channel_count=10, time_step_count=1000)

    assert hist.channel_count() == 10
    assert hist.time_step_count() == 1000

    hist = Histogram(channel_count=45, time_step_count=2)

    assert hist.channel_count() == 45
    assert hist.time_step_count() == 2


def test02_put_values_basic(variant_scalar_spectral):
    from mitsuba.render import Histogram
    from mitsuba.core import Mask, Spectrum

    hist = Histogram(channel_count=4, time_step_count=10)

    spectrum = np.random.uniform(size=(10, 4))

    hist.clear()

    for i in range(10):
        hist.put(i, spectrum[i])

    check_value(hist, spectrum)


def test03_put_values_basic_masked(variant_scalar_spectral):
    from mitsuba.render import Histogram
    from mitsuba.core import Mask, Spectrum

    hist = Histogram(channel_count=4, time_step_count=10)

    spectrum = np.random.uniform(size=(10, 4))

    mask = np.random.uniform(size=(10,)) > 0.3

    hist.clear()

    for i in range(10):
        hist.put(i, spectrum[i], not mask[i])

    spectrum[mask] = 0.

    check_value(hist, spectrum)


def test04_put_values_basic_accumulate(variant_scalar_spectral):
    from mitsuba.render import Histogram
    from mitsuba.core import Mask, Spectrum

    hist = Histogram(channel_count=4, time_step_count=10)

    spectrum = np.random.uniform(size=(20, 4))

    # Accumulate in 10 bins
    spectrum_accum = np.zeros(shape=(10, 4))
    for i in range(20):
        spectrum_accum[i % 10] += spectrum[i]

    hist.clear()

    # Distribute to 10 different time steps
    for i in range(20):
        hist.put(i % 10, spectrum[i])

    check_value(hist, spectrum_accum)


def test05_put_8d_values_basic(variant_scalar_spectral8):
    from mitsuba.render import Histogram
    from mitsuba.core import Mask

    hist = Histogram(channel_count=8, time_step_count=10)

    spectrum = np.random.uniform(size=(10, 8))

    hist.clear()

    for i in range(10):
        hist.put(i, spectrum[i])

    check_value(hist, spectrum)


def test06_put_packets_basic(variant_packet_spectral):
    from mitsuba.render import Histogram
    from mitsuba.core import Mask

    hist = Histogram(channel_count=4, time_step_count=10)

    spectrum = np.random.uniform(size=(10, 4))

    hist.clear()

    hist.put(np.arange(10), spectrum)

    check_value(hist, spectrum)
