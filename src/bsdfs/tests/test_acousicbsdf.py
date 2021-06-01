import mitsuba
import pytest
import enoki as ek
from enoki.dynamic import UInt32


def conductor_bsdf(reflectance):
    return f"""
    <bsdf version="2.0.0" type="conductor">
        <float name="specular_reflectance" value="{reflectance}"/>
    </bsdf>
"""


def diffuse_bsdf(reflectance):
    return f"""
    <bsdf version="2.0.0" type="diffuse">
        <float name="reflectance" value="{reflectance}"/>
    </bsdf>
"""


def acoustic_bsdf(scattering, absorption):
    return f"""
<bsdf version="2.0.0" type="acousticbsdf">
    <spectrum name="scattering" value="{scattering}"/>
    <spectrum name="absorption" value="{absorption}"/>
</bsdf>
"""


def reflect_local(wi):
    return [-wi[0], -wi[1], wi[2]]


def test01_create(variant_scalar_acoustic):
    from mitsuba.render import BSDFFlags
    from mitsuba.core.xml import load_string

    bsdf = load_string(acoustic_bsdf(0, 0))
    assert bsdf is not None


def test02_eval_pdf(variant_scalar_acoustic):
    from mitsuba.core import Frame3f
    from mitsuba.render import BSDFFlags, BSDFContext, SurfaceInteraction3f
    from mitsuba.core.xml import load_string
    from mitsuba.core.math import InvPi
    import numpy as np

    for scattering in np.linspace(0, 1, 5):
        for absorption in np.linspace(0, 1, 5):

            acoustic = load_string(acoustic_bsdf(scattering=scattering, absorption=absorption))
            diffuse = load_string(diffuse_bsdf(reflectance=1 - absorption))

            # Compare random uniform data points
            for i in range(100):
                ## Eval
                si = SurfaceInteraction3f()
                si.t = np.random.uniform(size=1)
                si.p = np.random.uniform(size=3)
                si.n = np.random.uniform(size=3)
                si.sh_frame = Frame3f(si.n)
                si.wi = np.random.uniform(size=3)
                si.wavelengths = np.random.uniform(0.017, 17, size=1)

                wo = np.random.uniform(size=3)
                ctx = BSDFContext()

                if ek.allclose(si.wi, reflect_local(wo)):
                    continue

                value_acoustic = acoustic.eval(ctx, si, wo)
                pdf_acoustic = acoustic.pdf(ctx, si, wo)

                # Eval and pdf are zero if wo is not equal to the reflected wi
                assert ek.allclose(value_acoustic, diffuse.eval(ctx, si, wo) * scattering)
                assert ek.allclose(pdf_acoustic, diffuse.pdf(ctx, si, wo) * scattering)

            # Compare random uniform data points with perfect reflection
            for i in range(100):
                ## Eval
                si = SurfaceInteraction3f()
                si.t = np.random.uniform(size=1)
                si.p = np.random.uniform(size=3)
                si.n = np.random.uniform(size=3)
                si.sh_frame = Frame3f(si.n)
                si.wi = np.random.uniform(size=3)
                si.wavelengths = np.random.uniform(0.017, 17, size=1)

                wo = reflect_local(si.wi)
                ctx = BSDFContext()

                value_acoustic = acoustic.eval(ctx, si, wo)
                pdf_acoustic = acoustic.pdf(ctx, si, wo)

                # Eval and pdf are one if wo is equal to the reflected wi
                assert ek.allclose(value_acoustic, ((1 - absorption) * (1 - scattering)) + (diffuse.eval(ctx, si, wo) * scattering))
                assert ek.allclose(pdf_acoustic, (1 - scattering) + (diffuse.pdf(ctx, si, wo) * scattering))


def test03_sample(variant_scalar_acoustic):
    from mitsuba.core import Frame3f
    from mitsuba.render import BSDFFlags, BSDFContext, SurfaceInteraction3f, reflect
    from mitsuba.core.xml import load_string
    from mitsuba.core.math import InvPi
    import numpy as np

    for scattering in np.linspace(0, 1, 5):
        for absorption in np.linspace(0, 1, 5):

            acoustic = load_string(acoustic_bsdf(scattering=scattering, absorption=absorption))
            conductor = load_string(conductor_bsdf(reflectance=1 - absorption))
            diffuse = load_string(diffuse_bsdf(reflectance=1 - absorption))

            # Compare random uniform data points
            for i in range(100):
                si = SurfaceInteraction3f()
                si.t = np.random.uniform(size=1)
                si.p = np.random.uniform(size=3)
                si.n = np.random.uniform(size=3)
                si.sh_frame = Frame3f(si.n)
                si.wi = np.random.uniform(size=3)
                si.wavelengths = np.random.uniform(0.017, 17, size=1)
                ctx = BSDFContext()

                ## Sample
                sample1 = np.random.uniform(size=1)
                sample2 = np.random.uniform(size=2)
                bs_a, weight_a = acoustic.sample(ctx, si, sample1, sample2)
                bs_b, weight_b = conductor.sample(ctx, si, sample1, sample2)
                bs_c, weight_c = diffuse.sample(ctx, si, sample1, sample2)

                is_specular = sample1 > scattering

                if is_specular:
                    assert bs_a.wo == bs_b.wo
                    assert ek.allclose(weight_a, weight_b * (1 - scattering))
                else:
                    assert bs_a.wo == bs_c.wo
                    assert ek.allclose(weight_a, weight_c * scattering)
