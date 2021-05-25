import math
import numpy as np
import os

import pytest
import enoki as ek
import mitsuba
import matplotlib.pyplot as plt

# Set a seed for the deterministic usage of np distributions
np.random.seed(0)


def get_vals(hist, counts=False):
    data = hist.counts() if counts else hist.data()
    return np.array(data, copy=False).reshape(hist.size() + [hist.border_size() * 2, 0])#[hist.border_size():hist.border_size()+hist.size()[0]]


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
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    # Setup histogram
    hist = Histogram([6, 3], 1, filter=rfilter)
    hist.clear()

    time_bin = [0, 1, 3, 4, 5]
    wavelength_bin = [0, 1, 2, 0, 1]
    spectrum = [1, 1, 1, 1, 1]

    # Insert
    for i, pos in enumerate(zip(np.array(time_bin) + 0.5, wavelength_bin)):
        hist.put(pos, spectrum[i])

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test03_put_values_basic_masked(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    # Setup histogram
    hist = Histogram([6, 3], 1, filter=rfilter)
    hist.clear()

    time_bin = np.array([0, 1, 3, 4, 5])
    wavelength_bin = [0, 1, 2, 0, 1]
    spectrum = [1, 1, 1, 1, 1]
    mask = [True, False, False, True, False]

    for i, pos in enumerate(zip(time_bin + 0.5, wavelength_bin)):
        hist.put(pos, spectrum[i], mask[i])
        # Apply mask to the spectrum values
        spectrum[i] *= mask[i]

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test04_put_values_basic_accumulate(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    # Setup histogram
    hist = Histogram([6, 3], 1, filter=rfilter)
    hist.clear()

    spectrum = np.ones(20)
    wavelength_bin = np.random.randint(0, 3, size=(20,))
    time_bin = np.random.randint(0, 6, size=(20,))

    # Distribute to 5 different time steps
    for i, pos in enumerate(zip(time_bin + 0.5, wavelength_bin)):
        hist.put(pos, spectrum[i])

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test05_put_packets_basic(variant_packet_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    hist = Histogram([20, 3], 1, filter=rfilter)
    hist.clear()

    spectrum = np.ones(shape=(10, 1))
    wavelength_bin = np.random.randint(0, 3, size=(10, 1))
    time_bin = np.random.randint(0, 20, size=(10, 1))

    pos = np.zeros(shape=(10, 2))
    pos[:, 0] = time_bin[:, 0] + 0.5
    pos[:, 1] = wavelength_bin[:, 0]

    hist.put(pos, spectrum)

    check_value(hist, time_bin, wavelength_bin, spectrum)


def test06_put_histogram_basic(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    hist = Histogram([10, 3], 1, filter=rfilter)
    hist2 = Histogram([10, 3], 1, filter=rfilter)

    spectrum = np.ones(shape=(10,))
    wavelength_bin = np.random.randint(0, 3, size=(10,))
    time_bin = np.random.randint(0, 10, size=(10,))

    hist.clear()
    hist2.clear()

    for i, pos in enumerate(zip(time_bin + 0.5, wavelength_bin)):
        hist2.put(pos, spectrum[i])
        hist.put(pos, spectrum[i])

    hist2.put(hist)

    check_value(hist2, time_bin, wavelength_bin, spectrum * 2)


def test07_put_histogram_offset(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    hist = Histogram([10, 4], 1, filter=rfilter)
    hist2 = Histogram([10, 2], 1, filter=rfilter)
    hist3 = Histogram([10, 2], 1, filter=rfilter)
    hist.clear()
    hist2.clear()
    hist3.clear()

    # Set the third histogram to have a wavelength bin offset of two
    hist3.set_offset([0, 2])

    spectrum = [1] * 20
    wavelength_bin = np.random.randint(0, 4, size=(20,))
    time_bin = np.random.randint(0, 10, size=(20,))

    for i, pos in enumerate(zip(time_bin + 0.5, wavelength_bin)):
        hist2.put(pos, spectrum[i])
        hist3.put(pos, spectrum[i])

    hist.put(hist2)
    hist.put(hist3)

    # check_value(hist2, time_bin, wavelength_bin, spectrum, verbose=True)
    # check_value(hist3, time_bin, wavelength_bin, spectrum, verbose=True)
    check_value(hist, time_bin, wavelength_bin, spectrum)


def test08_put_packet_histogram_basic(variant_packet_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    hist = Histogram([10, 4], 1, filter=rfilter)
    hist2 = Histogram([10, 4], 1, filter=rfilter)

    hist.clear()
    hist2.clear()

    spectrum = np.ones(shape=(10, 1))
    wavelength = np.random.randint(0, 4, size=(10, 1))
    time = np.random.randint(0, 10, size=(10, 1))

    pos = np.zeros(shape=(10, 2))
    pos[:, 0] = time[:, 0] + 0.5
    pos[:, 1] = wavelength[:, 0]

    hist.put(pos, spectrum)
    hist2.put(hist)

    check_value(hist2, time, wavelength, spectrum)


def test09_basic_counts(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    hist = Histogram([5, 3], 1, filter=rfilter)

    time = np.array([0, 1, 2, 2, 3])
    wavelength = [0, 1, 2, 2, 1]
    spectrum = [.1, .6, .7, .5, .2]

    # Setup histogram
    hist.clear()

    # Insert
    for i, pos in enumerate(zip(time + 0.5, wavelength)):
        hist.put(pos, spectrum[i])

    check_value(hist, time, wavelength, spectrum)

    counts = np.array(hist.counts(), copy=False).reshape([hist.width(), hist.height()])
    print(counts)
    # Double entries
    assert counts[2][2] == 2


def test10_put_hist_counts(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    rfilter = load_string("""<rfilter version="2.0.0" type="box">
            <float name="radius" value="0.4"/>
        </rfilter>""")

    hist = Histogram([3, 5], 1, filter=rfilter)
    hist2 = Histogram([3, 5], 1, filter=rfilter)

    wavelength = [0, 1, 2, 2, 1]
    # Weightings
    spectrum = [.1, .6, .7, .5, .2]
    time = np.array([0, 1, 2, 2, 3])

    # Setup histogram
    hist.clear()
    hist2.clear()

    # Insert
    for i, pos in enumerate(zip(time + 0.5, wavelength)):
        hist.put(pos, spectrum[i])
        hist2.put(pos, spectrum[i])

    check_value(hist, time, wavelength, spectrum)

    hist.put(hist2)

    counts = np.array(hist.counts(), copy=False).reshape([hist.width(), hist.height()])

    # Double Double entries
    assert counts[2][2] == 4


class DummyHistogram:
    def __init__(self, size, rfilter):
        self._size = np.array(size)
        self._border_size = rfilter.border_size() if rfilter is not None else 0
        self._storage = np.zeros(shape=((size[0] + self._border_size * 2), size[1]))
        self._counts = np.zeros(shape=((size[0] + self._border_size * 2), size[1]))
        self._rfilter = rfilter

        self._storage[:self._border_size] = 1
        self._counts[:self._border_size] = 1

    def put(self, pos_, val):
        size = self._size + np.array([2 * self._border_size, 0.])
        pos = pos_ - np.array([- self._border_size + .5, 0.])

        lo = np.ceil(pos - np.array([self._rfilter.radius(), 0.])).astype(np.int)#.clip(min=0)
        hi = np.floor(pos + np.array([self._rfilter.radius(), 0.])).astype(np.int).clip(max=size - 1)
        base = lo - pos
        n = np.ceil((self._rfilter.radius() - 2. * np.finfo(float).eps) * 2).astype(np.int)

        weights = np.array([self._rfilter.eval_discretized(base[0] + i) for i in range(n)])

        #weights /= sum(weights)

        for tr in range(n):
            x = (lo[0] + tr)
            r_pos = np.array([x, lo[1]])

            if np.any(r_pos < 0) or np.any(r_pos >= self._storage.shape):
                continue

            weight = weights[tr]

            self._storage[r_pos[0], r_pos[1]] += val * weight
            self._counts[r_pos[0], r_pos[1]] += 1 * weight

    def data(self):
        return self._storage

    def counts(self):
        return self._counts

    def size(self):
        return self._size

    def border_size(self):
        return self._border_size


def test11_put_with_filter(variant_scalar_acoustic):
    from mitsuba.render import Histogram
    from mitsuba.core.xml import load_string

    """The previous tests used a very simple box filter, parametrized so that
    it essentially had no effect. In this test, we use a more realistic
    Gaussian reconstruction filter, with non-zero radius."""

    try:
        mitsuba.set_variant("packet_acoustic")
        from mitsuba.core.xml import load_string as load_string_packet
        from mitsuba.render import Histogram as HistogramP
        from mitsuba.core import Vector2f, Float
    except ImportError:
        pytest.skip("packet_acoustic mode not enabled")

    rfilter = load_string("""<rfilter version="2.0.0" type="gaussian">
            <float name="stddev" value=".5"/>
        </rfilter>""")

    rfilter_p = load_string_packet("""<rfilter version="2.0.0" type="gaussian">
            <float name="stddev" value=".5"/>
        </rfilter>""")

    size = [20, 1]
    hist = Histogram(size, 1, filter=rfilter)
    hist.clear()

    hist2 = HistogramP(size, 1, filter=rfilter_p)
    hist2.clear()
    hist_ref = DummyHistogram(size, rfilter)

    time_bins = np.linspace(0, 20, 50)
    time_bins += np.random.uniform(-1, 1, 50) * 3
    time_bins.clip(0, 20)
    wavelength_bins = np.zeros(shape=(50,))
    values = np.exp(-np.linspace(0, 2 * np.pi, 50))

    positions = np.array([[a, b] for a, b in zip(time_bins, wavelength_bins)])

    n = time_bins.shape[0]
    for i in range(n):
        hist.put(positions[i], values[i])
        hist_ref.put(positions[i], values[i])

    hist2.put(Vector2f(positions), Float(values))

    hist_vals = get_vals(hist, counts=False)
    hist_counts = get_vals(hist, counts=True)

    hist2_vals = get_vals(hist2, counts=False)
    hist2_counts = get_vals(hist2, counts=True)

    hist_ref_vals = get_vals(hist_ref, counts=False)
    hist_ref_counts = get_vals(hist_ref, counts=True)

    assert np.allclose(hist_vals, hist_ref_vals, atol=1e-8)
    assert np.allclose(hist_counts, hist_ref_counts, atol=1e-6)

    assert np.allclose(hist2_vals, hist_ref_vals, atol=1e-6)
    assert np.allclose(hist2_counts, hist_ref_counts, atol=1e-6)
