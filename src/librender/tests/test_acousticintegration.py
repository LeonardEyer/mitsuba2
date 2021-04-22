import math
import numpy as np
import matplotlib.pyplot as plt

import pytest
import enoki as ek
import mitsuba


def make_shoebox_scene(emitter_pos, sensor_pos, box_dimensions, radius, max_time, time_steps, spp, wavs, scattering=0.0,
                       absorption=0.0, hide_sensor=True):
    from mitsuba.core import ScalarTransform4f

    def transform(scale=None, rotate=None, translate=None):
        if translate is None:
            translate = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]
        if rotate is None:
            rotate = ([0, 0, 0], 0)

        a = ScalarTransform4f.scale(scale)
        b = ScalarTransform4f.rotate(*rotate)
        c = ScalarTransform4f.translate(translate)
        return c * b * a

    global_translation = transform(translate=np.array(box_dimensions) / 2)

    scene = {
        "type": "scene",
        "bsdf_neutral": {
            "type": "acousticbsdf",
            "scattering": {
                "type": "acoustic",
                "value": scattering
            },
            "absorption": {
                "type": "acoustic",
                "absorption": True,
                "value": absorption
            }
        },
        "emitter_shape": {
            "id": "emitter",
            "type": "sphere",
            "radius": radius,
            "to_world": transform(translate=emitter_pos),
            "emitter": {
                "type": "area",
                "radiance": {
                    "type": "uniform",
                    "value": 1
                }
            }
        },
        "sensor": {
            "type": "microphone",
            "to_world": transform(translate=sensor_pos),
            "wavelengths": ','.join(str(x) for x in wavs),
            "sampler": {
                "type": "independent",
                "sample_count": spp
            },
            "myfilm": {
                "type": "tape",
                "max_time": max_time,
                "time_steps": time_steps,
            }
        },
        "shoebox": {
            "id": "shoebox_ref",
            "type": "shapegroup",
            "bottom": {
                "type": "rectangle",
                "to_world": transform(
                    scale=[1, 1, 1],
                    translate=[0, 0, -1]),
                "bsdf": {
                    "type": "ref",
                    "id": "bsdf_neutral"
                }
            },
            "left": {
                "type": "rectangle",
                "to_world": transform(
                    scale=[1, 1, 1],
                    rotate=([0, 1, 0], 90),
                    translate=[-1, 0, 0]),
                "bsdf": {
                    "type": "ref",
                    "id": "bsdf_neutral"
                }
            },
            "back": {
                "type": "rectangle",
                "to_world": transform(
                    scale=[1, 1, 1],
                    rotate=([1, 0, 0], 90),
                    translate=[0, 1, 0]),
                "bsdf": {
                    "type": "ref",
                    "id": "bsdf_neutral"
                }
            },
            "front": {
                "type": "rectangle",
                "to_world": transform(
                    scale=[1, 1, 1],
                    rotate=([1, 0, 0], -90),
                    translate=[0, -1, 0]),
                "bsdf": {
                    "type": "ref",
                    "id": "bsdf_neutral"
                }
            },
            "right": {
                "type": "rectangle",
                "to_world": transform(
                    scale=[1, 1, 1],
                    rotate=([0, 1, 0], -90),
                    translate=[1, 0, 0]),
                "bsdf": {
                    "type": "ref",
                    "id": "bsdf_neutral"
                }
            },
            "top": {
                "type": "rectangle",
                "to_world": transform(
                    scale=[1, 1, 1],
                    rotate=([0, 1, 0], 180),
                    translate=[0, 0, 1]),
                "bsdf": {
                    "type": "ref",
                    "id": "bsdf_neutral"
                }
            }
        },
        "shoebox_instance": {
            "type": "instance",
            "shape": {
                "type": "ref",
                "id": "shoebox_ref"
            },
            "to_world": global_translation * transform(scale=np.array(box_dimensions) / 2)
        }
    }
    return scene


def get_vals(data, time_steps, bin_count):
    return np.array(data, copy=False).reshape([time_steps, bin_count])


def make_integrator(bins, samples_per_pass, max_depth=5, max_time=1.):
    str_bins = list(map(str, bins))
    from mitsuba.core.xml import load_string

    integrator = load_string(f"""
    <integrator version='2.0.0' type='acousticpath'>
        <float name='max_time' value='{max_time}'/>
        <integer name='max_depth' value='{max_depth}'/>
        <string name='wavelength_bins' value='{','.join(str_bins)}'/>
        <integer name='samples_per_pass' value='{samples_per_pass}'/>
    </integrator>
    """)
    assert integrator is not None
    return integrator


def test01_create(variant_scalar_acoustic):
    bins = [20, 40, 80, 16000]
    integrator = make_integrator(bins, 1, 1)
    print(integrator)


def test015_test(variant_scalar_acoustic):
    from mitsuba.core.xml import load_string, load_dict
    from mitsuba.render import TimeDependentIntegrator
    bins = [3, 4]
    max_time = 1
    time_steps = 1000 * max_time

    integrator = make_integrator(bins=bins, samples_per_pass=100, max_time=max_time, max_depth=10)
    print("integrator.__class__.__name__:", integrator.__class__.__name__)

    assert isinstance(integrator, TimeDependentIntegrator)


def test02_render_specular_multiple_equal(variant_scalar_acoustic):
    from mitsuba.core.xml import load_string, load_dict
    #from enoki import cuda_set_log_level
    #cuda_set_log_level(0)
    bins = [3, 4]
    max_time = 1
    time_steps = 1000 * max_time

    scene = load_dict(make_shoebox_scene(emitter_pos=[20, 7, 2],
                                         sensor_pos=[9, 6, 1],
                                         box_dimensions=[25, 12, 7],
                                         radius=0.7,
                                         max_time=max_time,
                                         time_steps=time_steps,
                                         spp=100,
                                         wavs=bins[:-1],
                                         scattering=0.0,
                                         absorption=0.1))

    integrator = make_integrator(bins=bins, samples_per_pass=100, max_time=max_time, max_depth=10)
    print(integrator)

    sensor = scene.sensors()[0]

    status = integrator.render(scene, sensor)
    status = integrator.render(scene, sensor)
    assert status

    film = sensor.film()
    raw = film.bitmap(raw=True)
    counts = film.bitmap(raw=False)
    vals = get_vals(raw, time_steps, len(bins) - 1)
    vals_count = get_vals(counts, time_steps, len(bins) - 1)

    sums = np.sum(vals, axis=0)
    total = np.sum(sums)

    print("sum:", sums)
    print("%:", sums / total)

    assert True

    # plt.plot(vals_count, label='count')
    # #plt.plot(vals, label='vals')
    # # plt.plot(vals / vals_count, label='normalized')
    # plt.legend()
    # plt.show()
