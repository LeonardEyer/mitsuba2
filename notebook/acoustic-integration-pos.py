#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import matplotlib.pyplot as plt
import mitsuba
mitsuba.set_variant('gpu_acoustic')
import enoki as ek
ek.cuda_set_log_level(0)


# In[3]:


def make_shoebox_scene(emitter_pos, sensor_pos, box_dimensions, radius, max_time, time_steps, 
                       spp, bins, rfilter, max_depth, samples_per_pass, scattering,absorption, hide_sensor=True):
    
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
                "type": "spectrum",
                "value": scattering
            },
            "absorption": {
                "type": "spectrum",
                "value": absorption
            }
        },
        "emitter_shape": {
            "id": "emitter",
            "type": "sphere",
            "radius": radius,
            "to_world": transform(translate=emitter_pos),
            "emitter": {
                "type": "smoothsphere",
                "radiance": {
                    "type": "uniform",
                    "value": 1
                },
                "blur_size": .5
            }
        },
        "sensor": {
            "type": "microphone",
            "to_world": transform(translate=sensor_pos),
            "sampler": {
                "type": "independent",
                "sample_count": spp
            },
            "myfilm": {
                "type": "tape",
                "time_steps": time_steps,
                "wav_bins": len(bins),
                "rfilter": rfilter
            }  
        },
        "shoebox": {
            "id": "shoebox",
            "type": "obj",
            "filename": "../resources/cuberoom.obj",
            "bsdf": {
                "type": "ref",
                "id": "bsdf_neutral"
            },
            "to_world": transform(scale=np.array(box_dimensions))
        },
        "integrator": {
            "type": "acousticpath",
            "max_depth": int(max_depth),
            "max_time": max_time,
            "wavelength_bins": ','.join(str(x) for x in bins),
            "samples_per_pass": samples_per_pass
        }
    }
    return scene

def get_vals(data, size, copy=False):
    return np.array(data, copy=copy).reshape(size)


# In[4]:


from mitsuba.core.xml import load_string, load_dict

config = {
    "bins": [1],
    "absorption": 0.5,
    "scattering": 0.0,
    "max_time": 1,
    "time_steps": 100,
    "spp": 1000,
    "samples_per_pass": 1000,
    "box_dimensions": [5, 5, 5],
    "emitter_pos": [1, 1, 1],
    "sensor_pos": [-1, -1, -1],
    "radius": .1,  
    "max_depth": 50,
    "rfilter": {
        "type": "gaussian",
        "stddev": 2.0
    }
}

scene_dict = make_shoebox_scene(**config)
scene = load_dict(scene_dict)

size = scene.sensors()[0].film().size()

sensor = scene.sensors()[0]
integrator = scene.integrator()

status = integrator.render(scene, sensor)
assert status


# In[5]:


film = sensor.film()
raw = film.bitmap(raw=True)
counts = film.bitmap(raw=False)
vals = get_vals(raw, film.size())
vals_count = get_vals(counts, film.size())

print("sum:", np.sum(vals))

energy = vals / (vals_count + 1e-8)
energy /= energy[0]
energy_db = 10 * (np.log(energy) / np.log(10))


# In[6]:


fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=True, figsize=(15, 5))
ax1.plot(energy)
ax1.set_title("Energy")
ax2.plot(energy_db)
ax2.set_title("Energy [dB]")
ax3.plot(vals)
ax3.set_title("Recorded")
ax4.plot(vals_count)
ax4.set_title("Counts")


# In[7]:


energy


# In[ ]:




