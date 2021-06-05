#!/usr/bin/env python
# coding: utf-8

# In[34]:


import enoki as ek
import numpy as np
import matplotlib.pyplot as plt
import mitsuba
mitsuba.set_variant('gpu_autodiff_acoustic')
from mitsuba.python.util import traverse


# In[19]:


def pad_first_zeros(arr):
    non_zero = (arr!=0).argmax(axis=0)
    ret = np.copy(arr)
    
    arr_pad = np.copy(arr)
    for i,v in enumerate(non_zero):
        arr_pad[:v,i] = 1
    
    return arr_pad

def estimate_detector_radius(room_dimensions, N):
    return ((15 * room_dimensions[0] * room_dimensions[1] * room_dimensions[2]) / (2 * np.pi * N))**(1/2)

def estimate_max_depth(box_dimensions, max_time, boost=1):
    max_box_distance = np.linalg.norm(box_dimensions) / 2
    max_box_time = max_box_distance / 343
    max_depth_estimate = np.ceil(max_time / max_box_time * boost).astype(int) 
    return max_depth_estimate

def make_shoebox_scene(emitter_pos, sensor_pos, box_dimensions, radius, max_time, time_steps, spp, wavs, samples_per_pass=1, scattering=0.0,
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
            "wavelengths": ','.join(str(x) for x in wavs[:-1]),
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
        },
        "integrator": {
            "type": "acousticpath",
            "max_time": max_time,
            "wavelength_bins": ','.join(str(x) for x in wavs),
            "samples_per_pass": samples_per_pass
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


# In[41]:


from mitsuba.core.xml import load_string, load_dict

bins = [3, 6]
max_time = 1
time_steps = 10 * max_time
spp = 100
box_dimensions=[25, 12, 7]
emitter_pos=[20, 7, 2]
sensor_pos=[9, 6, 1]
max_depth_estimate = estimate_max_depth(box_dimensions, max_time, boost=1.5)

scene = load_dict(make_shoebox_scene(emitter_pos=emitter_pos,
                                     sensor_pos=sensor_pos,
                                     box_dimensions=box_dimensions,
                                     radius=estimate_detector_radius(box_dimensions, spp),
                                     max_time=max_time,
                                     time_steps=time_steps,
                                     spp=spp,
                                     wavs=bins,
                                     samples_per_pass=1000,
                                     scattering=0.0,
                                     absorption=0.1))


# In[57]:


from mitsuba.core import Spectrum

params = traverse(scene)
params.keep(['AcousticBSDF.bsdf_0.specular_reflectance.value'])
param_ref = Spectrum(params['AcousticBSDF.bsdf_0.specular_reflectance.value'])

from mitsuba.python.autodiff import render
hist_ref = render(scene, spp=None)


# In[58]:


plt.plot(hist_ref)


# In[59]:


# Construct an Adam optimizer that will adjust the parameters 'params'
from mitsuba.python.autodiff import Adam
opt = Adam(params, lr=.2)


# In[60]:


for it in range(10):
    # Perform a differentiable rendering of the scene
    hist = render(scene, optimizer=opt, unbiased=False, spp=None)

    # Objective: MSE between 'image' and 'image_ref'
    ob_val = ek.hsum(ek.sqr(hist - hist_ref)) / len(hist)

    # Back-propagate errors to input parameters
    ek.backward(ob_val)

    # Optimizer: take a gradient step
    opt.step()
    
    err_ref = ek.hsum(ek.sqr(param_ref - params['red.reflectance.value']))
    print('Iteration %03i: error=%g' % (it, err_ref[0]))


# In[61]:


plt.plot(hist)

