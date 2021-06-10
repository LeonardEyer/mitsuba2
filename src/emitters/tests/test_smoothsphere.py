import mitsuba
import pytest
import enoki as ek
from enoki.dynamic import Float32 as Float
import numpy as np

from mitsuba.python.test.util import fresolver_append_path

def test01_constructor(variant_scalar_acoustic):
    from mitsuba.core.xml import load_dict
    from mitsuba.render import SurfaceInteraction3f
    
    emitter_shape = load_dict({
        "type": "sphere",
        "radius": 1.0,
        "emitter": {
            "type": "smoothsphere",
            "radiance": {
                "type": "uniform",
                "value": 1.0
            },
            "blur_size": 0.5
        }
    })

    it = SurfaceInteraction3f.zero(1)
    it.p = [2, 2, 2]
    it.wavelengths = [1.0]
    #it.p = [0.5, 0.5, 0.5]
    #it.n = [0.5, 0.5, 0.5]
    #it.wi = [1, 0, 0]

    ds, spec = emitter_shape.emitter().sample_direction(it, 1)
    print(ds)
    print("spec:", spec)
    print("1/ds.pdf", 1/ds.pdf)
    print(abs(np.dot(ds.d, ds.n)))

    #spec = emitter_shape.emitter().eval(it)
    #print(spec)

def test02_eval_pdf(variant_scalar_acoustic):

    from mitsuba.core.xml import load_dict
    from mitsuba.render import SurfaceInteraction3f
    
    emitter_shape = load_dict({
        "type": "sphere",
        "radius": 1.0,
        "emitter": {
            "type": "smoothsphere",
            "radiance": {
                "type": "uniform",
                "value": 1.0
            },
            "blur_size": 0.5
        }
    })

    it = SurfaceInteraction3f.zero(1)
    it.p = [1, 0, 0]
    it.wavelengths = [1.0]
    it.n = [0.0, 0.0, 1.0]
    it.wi = [0.5, 0.5, 0.5]

    spec = emitter_shape.emitter().eval(it)
    print(spec)

