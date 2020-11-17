import math
import numpy as np
import os

import pytest
import enoki as ek
import mitsuba


def test01_construct(variant_scalar_spectral):
    from mitsuba.core.xml import load_string
    from mitsuba.render import Histogram

    hist = Histogram(channel_count=10, time_step_count=1000)

    assert hist.channel_count() == 10
    assert hist.time_step_count() == 1000

    hist = Histogram(channel_count=45, time_step_count=2)

    assert hist.channel_count() == 45
    assert hist.time_step_count() == 2


def test02_put_values_basic(variant_scalar_spectral8):
    from mitsuba.render import Histogram
    from mitsuba.core import Mask

    hist = Histogram(channel_count=8, time_step_count=10)

    spectrum = np.random.uniform(size=(8,))

    hist.put(0, spectrum)
