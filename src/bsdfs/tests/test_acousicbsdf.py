import mitsuba
import pytest
import enoki as ek
from enoki.dynamic import UInt32


def conductor_bsdf(reflectance=0.9):
    return f"""
    <bsdf version="2.0.0" type="conductor">
        <float name="specular_reflectance" value="{reflectance}"/>
    </bsdf>
"""


def acoustic_bsdf(scattering=0.1, absorption=0.1):
    return f"""
<bsdf version="2.0.0" type="acousticbsdf">
    <float name="scattering" value="{scattering}"/>
    <spectrum name="absorption" type="acoustic">
        <boolean name="absorption" value="true"/>
        <float name="value" value="{absorption}"/>
     </spectrum>
</bsdf>
"""


def test01_create(variant_scalar_acoustic):
    from mitsuba.render import BSDFFlags
    from mitsuba.core.xml import load_string

    bsdf = load_string(acoustic_bsdf())
    assert bsdf is not None


def test02_eval_specular(variant_scalar_acoustic):
    from mitsuba.core import Frame3f
    from mitsuba.render import BSDFFlags, BSDFContext, SurfaceInteraction3f
    from mitsuba.core.xml import load_string
    from mitsuba.core.math import InvPi
    import numpy as np

    for absorption in np.linspace(0, 1, 10):

        acoustic = load_string(acoustic_bsdf(scattering=0, absorption=absorption))

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


def test03_sample_specular(variant_scalar_acoustic):
    from mitsuba.core import Frame3f
    from mitsuba.render import BSDFFlags, BSDFContext, SurfaceInteraction3f, reflect
    from mitsuba.core.xml import load_string
    from mitsuba.core.math import InvPi
    import numpy as np

    for absorption in np.linspace(0, 1, 10):

        acoustic = load_string(acoustic_bsdf(scattering=0., absorption=absorption))
        conductor = load_string(conductor_bsdf(reflectance=1-absorption))

        # Compare random uniform data points
        for i in range(100):
            si = SurfaceInteraction3f()
            si.t = np.random.uniform(size=1)
            si.p = np.random.uniform(size=3)
            si.n = np.random.uniform(size=3)
            si.sh_frame = Frame3f(si.n)
            si.wi = np.random.uniform(size=3)
            si.wavelengths = np.random.uniform(0.017, 17, size=1)

            wo = np.random.uniform(size=3)
            ctx = BSDFContext()

            ## Sample
            sample1 = np.random.uniform(size=1)
            sample2 = np.random.uniform(size=2)
            bs_a, weight_a = acoustic.sample(ctx, si, sample1, sample2)
            bs_b, weight_b = conductor.sample(ctx, si, sample1, sample2)

            active = Frame3f.cos_theta(si.wi) > 0

            assert ek.allclose(weight_a, (1. - absorption) * active)
            assert bs_a.wo == reflect(si.wi)
            assert bs_a.wo == bs_b.wo
            assert ek.allclose(weight_a, weight_b)
