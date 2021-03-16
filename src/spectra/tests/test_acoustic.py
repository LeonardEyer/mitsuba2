# Superficial testing. Basically a wrapper around irregular

import mitsuba
import pytest
import enoki as ek
import numpy as np
import matplotlib.pyplot as plt

MTS_SOUND_SPEED = 343


def make_freq(freq, vals, absorption=True):
    return mitsuba.core.xml.load_string(f'''
        <spectrum version='2.0.0' type='acoustic'>
            <float name="freq_min" value="20"/>
            <float name="freq_max" value="20000"/>
            <boolean name="absorption" value="{absorption}"/>
            <string name="frequencies" value="{','.join(str(x) for x in freq)}"/>
            <string name="values" value="{','.join(str(x) for x in vals)}"/>
        </spectrum>''').expand()[0]


def make_acoustic_step_width(step_width):
    return mitsuba.core.xml.load_string(f'''
        <spectrum version='2.0.0' type='acoustic'>
            <float name="lambda_min" value="0.017"/>
            <float name="lambda_max" value="17"/>
            <boolean name="absorption" value="false"/>
            <integer name="octave_step_width" value="{step_width}"/>
        </spectrum>''').expand()[0]


def test01_eval_frequency(variant_scalar_acoustic):
    from mitsuba.render import SurfaceInteraction3f
    obj = make_freq([20, 40, 16000], [1., 0.9, .5], absorption=False)

    freqs = [20000, 16000, 40, 20]
    values = [0, 0.5, 0.9, 1]
    si = SurfaceInteraction3f()

    for i in range(len(freqs)):
        si.wavelengths = MTS_SOUND_SPEED / freqs[i]
        assert np.allclose(obj.eval(si), values[i])


def test02_eval_frequency_absorb(variant_scalar_acoustic):
    from mitsuba.render import SurfaceInteraction3f
    obj = make_freq([20, 40, 16000], [1., 0.9, .5], absorption=True)

    freqs = [20000, 16000, 40, 20]
    values = [1, 0.5, 0.9, 1]
    si = SurfaceInteraction3f()

    for i in range(len(freqs)):
        si.wavelengths = MTS_SOUND_SPEED / freqs[i]
        assert np.allclose(obj.eval(si), 1 - values[i])


def test03_sample_fractional_oct(variant_scalar_acoustic):
    from mitsuba.render import SurfaceInteraction3f

    obj = make_acoustic_step_width(1)

    si = SurfaceInteraction3f()

    assert ek.allclose(obj.sample_spectrum(si, 0.0)[0], 0.01532125)
    assert ek.allclose(obj.sample_spectrum(si, 0.5)[0], 0.4845)
    assert ek.allclose(obj.sample_spectrum(si, 1.0)[0], 15.32124721)


def test04_sample_discrete(variant_scalar_acoustic):
    from mitsuba.render import SurfaceInteraction3f

    freqs = np.array([8, 16, 31.5, 63, 125, 250, 500, 1000])
    wavs = freqs / MTS_SOUND_SPEED

    obj = make_freq(freqs, wavs, absorption=False)

    si = SurfaceInteraction3f()

    print(wavs)
    print(obj.sample_spectrum(si, 1.0))
