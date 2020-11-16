import math
import numpy as np
import os

import pytest
import enoki as ek
import mitsuba


def test01_construct(variant_scalar_rgb):
    from mitsuba.core.xml import load_string
    from mitsuba.render import Histogram

    hist = Histogram()
