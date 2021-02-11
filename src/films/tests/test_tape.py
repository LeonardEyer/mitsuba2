import mitsuba
import pytest
import os
import enoki as ek


def generate_tape(time_steps=1, max_time=1.):
    return f"""
<film version="2.0.0" type="tape">
    <integer name="time_steps" value="{time_steps}"/>
    <float name="max_time" value="{max_time}"/>
    <rfilter type="box"/>
</film>
"""


def test01_construct(variant_scalar_rgb):
    from mitsuba.core.xml import load_string

    # With default reconstruction filter
    film = load_string(generate_tape(4))

    assert film is not None
    assert film.size() == [4, 1]

    film.prepare([1., 2., 3.])

    assert film.size() == [4, 3]

