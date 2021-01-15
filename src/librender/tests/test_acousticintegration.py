import math
import numpy as np

import pytest
import enoki as ek
import mitsuba
import matplotlib.pyplot as plt

fractional_octave_1_bins = [22.38721139, 44.66835922, 89.12509381, 177.827941,
                            354.81338923, 707.94578438, 1412.53754462, 2818.38293126,
                            5623.4132519, 11220.18454302, 22387.21138568]

sphere_room_scene = """
<scene version="2.0.0">
    <shape type="sphere">
        <point name="center" x="2" y="0" z="0"/>
        <float name="radius" value="1"/>
        <bsdf type="diffuse"/>
        <emitter type="area">
            <spectrum name="radiance" value="1"/>
        </emitter>
    </shape>  
    
    <shape type="sphere">
        <boolean name="flip_normals" value="true"/>
        <point name="center" x="0" y="0" z="0"/>
        <float name="radius" value="10"/>
        <bsdf type="diffuse"/>
    </shape>
    
    <shape type="sphere">
        <point name="center" x="-2" y="0" z="0"/>
        <float name="radius" value="1"/>
        <sensor type="irradiancemeter">
            <spectrum name="srf" type="acoustic">
                <float name="lambda_min" value="0.017"/>
                <float name="lambda_max" value="17"/>
                <integer name="octave_step_width" value="1"/>
            </spectrum>
            
            <sampler type="independent">
                <integer name="sample_count" value="4"/>
                <integer name="seed" value="0"/>
            </sampler>
            
            <film type="tape">
                <integer name="width" value="1"/>
                <integer name="height" value="1"/>
                <rfilter type="box"/>
            </film>
        </sensor>
    </shape>
</scene>
"""

box_room_scene = """
<scene version="2.0.0">

    <shape type="obj"> <!-- Bottom -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
        </transform>
        <ref id="neutral"/>
    </shape>

    <shape type="obj">  <!-- Left -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="0" y="1" z="0" angle="90"/>
            <translate x="-5" y="0" z="5"/>
        </transform>
        <bsdf type="diffuse">
            <rgb name="reflectance" value="0.61, 0.53, 1.00"/>
        </bsdf>
    </shape>

    <shape type="obj">  <!-- Back -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="1" y="0" z="0" angle="90"/>
            <translate x="0" y="5" z="5"/>
        </transform>
        <ref id="neutral"/>
    </shape>
    
    <shape type="obj">  <!-- Front -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="1" y="0" z="0" angle="-90"/>
            <translate x="0" y="-5" z="-5"/>
        </transform>
        <ref id="neutral"/>
    </shape>

    <shape type="obj">  <!-- Right -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="0" y="1" z="0" angle="-90"/>
            <translate x="5" y="0" z="5"/>
        </transform>
        <bsdf type="diffuse">
            <rgb name="reflectance" value="0.98, 0.77, 0.19"/>
        </bsdf>
    </shape>

    <shape type="obj">  <!-- Top -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="0" y="1" z="0" angle="180"/>
            <translate x="0" y="0" z="10"/>
        </transform>
        <ref id="neutral"/>
    </shape>
</scene>
"""


def make_integrator(bins, time_steps, max_depth=2):
    from mitsuba.core.xml import load_string
    integrator = load_string(f"""
    <integrator version='2.0.0' type='acousticpath'>
        <string name='wavelength_bins' value='{','.join(bins)}'/>
        <integer name='time_steps' value='{time_steps}'/>
        <integer name='max_depth' value='{max_depth}'/>
    </integrator>
    """)
    assert integrator is not None
    return integrator


def test01_create(variant_scalar_spectral):
    from mitsuba.core.xml import load_string
    bins = list(map(str, [20, 40, 80, 16000]))
    integrator = make_integrator(bins, 1, 1)
    print(integrator)


def test02_render(variant_scalar_spectral):
    from mitsuba.core.xml import load_string
    bins = list(map(str, fractional_octave_1_bins))
    integrator = make_integrator(bins, 1, 2)

    scene = load_string(sphere_room_scene)
    sensor = scene.sensors()[0]

    status = integrator.render(scene, sensor)

    film = sensor.film()
    raw = film.raw()
    print(raw)

    assert status

    print("ok")
