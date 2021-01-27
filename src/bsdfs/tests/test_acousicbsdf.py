import mitsuba
import pytest
import enoki as ek
from enoki.dynamic import UInt32


def blend_bsdf(weight=0.1):
    return f"""
<bsdf version="2.0.0" type="blendbsdf">
    <float name="weight" value="{weight}"/>
    <bsdf type="conductor"/>
    <bsdf type="diffuse">
        <spectrum name="reflectance" type="acoustic">
            <string name="wavelengths" value="0.017, 17"/>
            <string name="values" value=".1, .1"/>
         </spectrum>
    </bsdf>
</bsdf>
"""


def acoustic_bsdf(scattering=0.1):
    return f"""
<bsdf version="2.0.0" type="acousticbsdf">
    <float name="scattering" value="{scattering}"/>
    <spectrum name="absorption" type="acoustic">
        <string name="wavelengths" value="0.017, 17"/>
        <string name="values" value=".1, .1"/>
     </spectrum>
</bsdf>
"""


def test01_create(variant_scalar_acoustic):
    from mitsuba.render import BSDFFlags
    from mitsuba.core.xml import load_string

    bsdf = load_string(acoustic_bsdf())
    assert bsdf is not None


def test02_eval_equal_to_blendbsdf(variant_scalar_acoustic):
    from mitsuba.core import Frame3f
    from mitsuba.render import BSDFFlags, BSDFContext, SurfaceInteraction3f
    from mitsuba.core.xml import load_string
    from mitsuba.core.math import InvPi
    import numpy as np

    for weight in np.linspace(0, 1, 10):

        acoustic = load_string(acoustic_bsdf(weight))
        blend = load_string(blend_bsdf(weight))

        # Compare random uniform data points
        for i in range(100):
            ## Eval
            si = SurfaceInteraction3f()
            si.t = np.random.uniform(size=1)
            si.p = np.random.uniform(size=3)
            si.n = np.random.uniform(size=3)
            si.sh_frame = Frame3f(si.n)
            si.wi = np.random.uniform(size=3)

            wo = np.random.uniform(size=3)
            ctx = BSDFContext()

            value_acoustic = acoustic.eval(ctx, si, wo)
            value_blend = blend.eval(ctx, si, wo)

            assert value_acoustic == value_blend


def test03_sample_equal_to_blendbsdf(variant_scalar_acoustic):
    from mitsuba.core import Frame3f
    from mitsuba.render import BSDFFlags, BSDFContext, SurfaceInteraction3f
    from mitsuba.core.xml import load_string
    from mitsuba.core.math import InvPi
    import numpy as np

    for weight in np.linspace(0, 1, 10):

        acoustic = load_string(acoustic_bsdf(weight))
        blend = load_string(blend_bsdf(weight))

        # Compare random uniform data points
        for i in range(100):
            si = SurfaceInteraction3f()
            si.t = np.random.uniform(size=1)
            si.p = np.random.uniform(size=3)
            si.n = np.random.uniform(size=3)
            si.sh_frame = Frame3f(si.n)
            si.wi = np.random.uniform(size=3)

            wo = np.random.uniform(size=3)
            ctx = BSDFContext()

            ## Sample
            sample1 = np.random.uniform(size=1)
            sample2 = np.random.uniform(size=2)
            bs_a, weight_a = acoustic.sample(ctx, si, sample1, sample2)
            bs_b, weight_b = blend.sample(ctx, si, sample1, sample2)

            assert bs_a.wo == bs_b.wo
            assert bs_a.pdf == bs_b.pdf
            assert bs_a.eta == bs_b.eta
            assert weight_a == weight_b