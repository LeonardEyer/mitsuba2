import numpy as np
import pytest

import enoki as ek
import mitsuba


def sensor_dict(center, wavs):
    from mitsuba.core import ScalarTransform4f

    d = {
        "type": "microphone",
        "wavelengths": ",".join(str(x) for x in wavs),
        "to_world": ScalarTransform4f.translate(center),
    }

    return d


def test_construct(variant_scalar_acoustic):
    """We construct an irradiance meter attached to a sphere and assert that the
    following parameters get set correctly:
    - associated shape
    - film
    """
    from mitsuba.core import ScalarVector3f
    from mitsuba.core.xml import load_dict

    center_v = ScalarVector3f(0.0)
    sensor = load_dict(sensor_dict(center_v, [10, 20]))


@pytest.mark.parametrize(
    ("center", "radius"),
    [([2.0, 5.0, 8.3], 2.0), ([0.0, 0.0, 0.0], 1.0), ([1.0, 4.0, 0.0], 5.0)]
)
def test_sampling(variant_scalar_acoustic, center, radius):
    """We construct an irradiance meter attached to a sphere and assert that
    sampled rays originate at the sphere's center
    """
    from mitsuba.core import ScalarVector3f
    from mitsuba.core.xml import load_dict

    wavs = [1, 2, 3, 4, 5]

    center_v = ScalarVector3f(center)
    sensor = load_dict(sensor_dict(center_v, wavs))
    num_samples = 100

    wav_samples = np.linspace(0, 1, num_samples)
    pos_samples = np.random.rand(num_samples, 2)
    dir_samples = np.random.rand(num_samples, 2)

    for i in range(num_samples):
        ray, weight = sensor.sample_ray_differential(
            0.0, wav_samples[i], pos_samples[i], dir_samples[i])

        # assert that the ray starts at the sphere center
        assert ek.allclose(ray.o, center_v)

        idx = np.ceil(wav_samples[i] * (len(wavs) - 1))
        assert ray.wavelengths[0] == wavs[int(idx)]
        assert weight == np.pi
