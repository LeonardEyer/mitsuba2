#!/usr/bin/env python
# coding: utf-8

# In[1]:


import mitsuba
import numpy as np
mitsuba.set_variant("scalar_rgb")
from mitsuba.core.xml import load_dict
from mitsuba.python.autodiff import render, write_bitmap
#from mitsuba.core import Thread, LogLevel
#Thread.thread().logger().set_log_level(LogLevel.Debug)
#import enoki as ek
#ek.cuda_set_log_level(0)


# In[2]:


def make_shoebox_scene(emitter_pos, sensor_pos, box_dimensions, radius=1.0, spp=8, sp_pass=8):
    from mitsuba.core import ScalarTransform4f
    
    def transform(scale=[1, 1, 1], rotate=([0, 0, 0], 0), translate=[0, 0, 0]):
        a = ScalarTransform4f.scale(scale)
        b = ScalarTransform4f.rotate(*rotate)
        c = ScalarTransform4f.translate(translate)
        return c * b * a
    
    global_translation = transform(translate=np.array(box_dimensions) / 2)
    
    scene = {
        "type": "scene",
        "myintegrator" : {
            "type": "path",
            "max_depth": 5,
            "samples_per_pass": sp_pass
        },
        "bsdf_neutral": {
            "type": "diffuse",
            "reflectance": {
                "type": "rgb",
                "value": [1., 0., 1.]
            }
        },
        "sensor_shape" : {
            "id": "sensor",
            "type": "sphere",
            "radius": radius,
            "to_world": transform(translate=sensor_pos)
        },
        "shoebox": {
            "id": "shoebox",
            "type": "obj",
            "filename": "resources/cuberoom.obj",
            "bsdf": {
                "type": "ref",
                "id": "bsdf_neutral"
            },
            "to_world": global_translation * transform(scale=np.array(box_dimensions) / 2)
        },
        "mysensor": {
            "type": "perspective",
            "near_clip": 0.1,
            "far_clip": 1000,
            "fov": 70,
            "to_world": global_translation * ScalarTransform4f.look_at(
                target=[-1, -1, -1] * np.array(np.array(box_dimensions) / 2),
                origin=[.8, .8, 0] * np.array(np.array(box_dimensions) / 2),
                up=[0, 0, 1]
            ),
            "myfilm": {
                "type": "hdrfilm",
                "width": 10,
                "height": 10,
                "pixel_format": "rgb"
            },
            "sampler": {
                "type": "independent",
                "sample_count" : spp
            }
        }
    }
    
    scene['emitter_shape'] =  {
        "id": "emitter",
        "type" : "sphere",
        "radius": radius,
        "to_world": transform(translate=emitter_pos),
        "emitter": {
            "type": "area",
            "radiance": {
                "type": "uniform",
                "value": 1
            },
            #"blur_size": 0.2
        }
    }
    
    #del scene['emitter_shape']['emitter']
    
    scene['ceiling_light'] = {
        "type": "rectangle",
        "to_world": global_translation * transform(scale=np.array(box_dimensions) / 4, rotate=([0, 1, 0], 180), translate=[0, 0, 1]),
        "emitter": {
            "type": "smootharea",
            "radiance": {
                "type": "uniform",
                "value": 10
            },
            "blur_size": .5
        }
    }
    
    del scene['ceiling_light']['emitter']
    return scene


# In[3]:


scene_dict = make_shoebox_scene([20, 8, 3], [9, 6, 1], [25, 12, 7], radius=0.5, spp=1, sp_pass=1)
scene = load_dict(scene_dict)


# In[4]:


#image_ref = render(scene, spp=16)
scene.integrator().render(scene, scene.sensors()[0])

crop_size = scene.sensors()[0].film().crop_size()


#write_bitmap('output/out.jpg', image_ref, crop_size)


# In[ ]:





# In[ ]:




