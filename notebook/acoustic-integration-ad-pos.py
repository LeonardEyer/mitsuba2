#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import matplotlib.pyplot as plt
import mitsuba
mitsuba.set_variant('gpu_autodiff_acoustic')
from mitsuba.python.util import traverse
import time
from tqdm.notebook import trange, tqdm
from mitsuba.core import xml, Thread, Transform4f, Bitmap, Float, Vector3f, UInt32
from mitsuba.python.autodiff import render, write_bitmap, Adam, SGD
import enoki as ek
ek.cuda_set_log_level(0)


# In[25]:


def estimate_detector_radius(room_dimensions, N):
    return ((15 * room_dimensions[0] * room_dimensions[1] * room_dimensions[2]) / (2 * np.pi * N))**(1/2)

def estimate_max_depth(box_dimensions, max_time, boost=1):
    max_box_distance = np.linalg.norm(box_dimensions) / 2
    max_box_time = max_box_distance / 343
    max_depth_estimate = np.ceil(max_time / max_box_time * boost).astype(int) 
    return max_depth_estimate

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
                "blur_size": 0.5
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
            "filename": "resources/cuberoom.obj",
            "bsdf": {
                "type": "ref",
                "id": "bsdf_neutral"
            },
            #"to_world": transform(scale=np.array(box_dimensions))
        },
        "integrator": {
            "type": "acousticpathreparam",
            "max_depth": int(max_depth),
            "max_time": max_time,
            "wavelength_bins": ','.join(str(x) for x in bins),
            "samples_per_pass": samples_per_pass
        }
    }
    return scene

def get_vals(data, size, copy=False):
    return np.array(data, copy=copy).reshape(size)


# Convert flat array into a vector of arrays (will be included in next enoki release)
def ravel(buf, dim = 3):
    idx = dim * UInt32.arange(ek.slices(buf) // dim)
    return Vector3f(ek.gather(buf, idx), ek.gather(buf, idx + 1), ek.gather(buf, idx + 2))

# Return contiguous flattened array (will be included in next enoki release)
def unravel(source, target, dim = 3):
    idx = UInt32.arange(ek.slices(source))
    for i in range(dim):
        ek.scatter(target, source[i], dim * idx + i)


# In[26]:


from mitsuba.core.xml import load_string, load_dict


config = {
    "bins": [1],
    "absorption": 0.5,
    "scattering": 1.0,
    "max_time": 1.0,
    "time_steps": 100,
    "spp": 1000,
    "samples_per_pass": 1000,
    "box_dimensions": [1, 1, 1],
    "emitter_pos": [1, 1, 1],
    "sensor_pos": [-1, -1, -1],
    "radius": .1,  #estimate_detector_radius(box_dimensions, spp)
    "max_depth": 50, #estimate_max_depth(0.9),
    "rfilter": {
        "type": "gaussian",
        "stddev": 2.0
    }
}


scene_dict = make_shoebox_scene(**config)
scene = load_dict(scene_dict)
size = scene.sensors()[0].film().size()


# In[4]:


from mitsuba.core import Spectrum, Float

params = traverse(scene)
print(params)
positions_buf = params['shoebox.vertex_positions_buf']
positions_initial = ravel(positions_buf)

# Create differential parameter to be optimized
scale_ref = Vector3f(5, 5, 5)

# Create a new ParameterMap (or dict)
params_optim = {
    "scale" : scale_ref,
}

# Construct an Adam optimizer that will adjust the translation parameters
opt = Adam(params_optim, lr=0.02)

print(ek.gradient(params_optim["scale"]))

# Apply the transformation to mesh vertex position and update scene (e.g. Optix BVH)
def apply_transformation():
    trasfo = Transform4f.scale(params_optim["scale"])
    new_positions = trasfo.transform_point(positions_initial)
    unravel(new_positions, params['shoebox.vertex_positions_buf'])
    params.set_dirty('shoebox.vertex_positions_buf')
    params.update()

# Render a reference image (no derivatives used yet)
apply_transformation()
hist_ref = render(scene, spp=None)
plt.plot(get_vals(hist_ref, size))
plt.show()

print(ek.gradient(params_optim["scale"]))


# In[ ]:


import plotly.graph_objects as go
from plotly.subplots import make_subplots

class OptimizationPlot:
    def __init__(self, name, bins, target, max_time=1.0):
        self._error = []
        self._bins = bins
        self._max_time = max_time
        
        T = np.linspace(0, self._max_time, target.shape[0])
    
        self._fig = go.FigureWidget(make_subplots(rows=1, cols=2, subplot_titles=("EDC", "Error"), specs=[[{"type": "scatter"}, {"type": "scatter"}]]))

        self._fig.add_scatter(row=1, col=1, name="current")
        #self._fig.add_scatter(row=1, col=1, opacity=0.2, name="target")
        self._fig.add_scatter(row=1, col=2)
                
        #self._fig.data[0].x = T
        #self._fig.data[0].y = [0] * target.shape[0]
        #self._fig.data[1].x = T
        #self._fig.data[1].y = target

    def plot_optimization_state(self, current, err_ref):
        self._error.append(err_ref)
        self._fig.data[0].y = current

        self._fig.data[1].y = self._error
        
        time.sleep(0.1)

    @property
    def error(self):
        return self._error
    
    def show(self):
        return self._fig


# In[ ]:


iterations = 0
np_hist_ref = get_vals(hist_ref, size, copy=True)

def mse(a, b):
    return ek.hsum(ek.sqr(a - b)) / len(hist)

# rescale object before starting the optimization process
params_optim["scale"] = Vector3f(7.0, 7.0, 7.0)

opt_plot = OptimizationPlot("Optimize room scale", config['bins'], np_hist_ref, config['max_time'])
opt_plot.show()


# In[ ]:


pbar = tqdm(range(iterations), desc='iterations')

for it in pbar:
    # Perform a differentiable rendering of the scene
    hist = render(scene, optimizer=opt, unbiased=False, spp=None, pre_render_callback=apply_transformation)

    np_hist = get_vals(hist, size, copy=True)

    # Objective: MSE between 'hist' and 'hist_ref'
    ob_val = mse(hist, hist_ref)

    # Back-propagate errors to input parameters
    ek.backward(ob_val)

    # Optimizer: take a gradient step
    opt.step()

    # Compute error
    err_ref = np.sum(np.square(scale_ref - params_optim["scale"]))
    
    pbar.set_postfix({'scale': params_optim["scale"]})

    # Plot progress
    opt_plot.plot_optimization_state(np_hist, err_ref)


# In[ ]:


set_label(params_optim["scale"], "scale")
set_label(ob_val, "objective")
from graphviz import Source
Source(graphviz(ob_val))


# In[ ]:


print(ob_val)


# In[ ]:


plt.plot(hist)


# In[ ]:




