import math
import numpy as np
import matplotlib.pyplot as plt

import pytest
import enoki as ek
import mitsuba

fractional_octave_1_bins = [0.01532125, 0.03056991, 0.06099498, 0.12170099, 0.2428254, 0.48450038,
                            0.96670535, 1.92883075, 3.8485233, 7.67881351, 15.32124721]


def sphere_room_scene(spp):
    return f"""
<scene version="2.0.0">
    <shape type="sphere">
        <point name="center" x="2" y="0" z="0"/>
        <float name="radius" value="1"/>
        <bsdf type="diffuse"/>
        <emitter type="area">
            <spectrum name="radiance" value="0.017:1.0, 17:1.0"/>
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
                <integer name="sample_count" value="{spp}"/>
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


def box_room_scene(max_time, time_steps, spp, wavs, scattering=0.0, hide_sensor=True):
    return f"""
<scene version="2.0.0">
    <bsdf type="conductor" id="blens2"/>
    
    <bsdf type="blendbsdf" id="blens">
        <spectrum name="weight" value="0.0"/>
        <bsdf type="conductor"/>
        <bsdf type="diffuse">
            <spectrum name="reflectance" type="acoustic">
                <string name="wavelengths" value="0.017, 17"/>
                <string name="values" value="0.1, 0.1"/>
             </spectrum>
        </bsdf>
    </bsdf>
    
    <bsdf type="acousticbsdf" id="blend">
        <spectrum name="scattering" value="{scattering}"/>
        <spectrum name="absorption" type="acoustic">
            <boolean name="absorption" value="true"/>
            <string name="wavelengths" value="0.017, 17"/>
            <string name="values" value="0.1, 0.1"/>
         </spectrum>
    </bsdf>

    <shape type="sphere" id="emitter">
        <point name="center" x="3" y="-3" z="2.5"/>
        <float name="radius" value="1"/>
        <emitter type="area">
            <spectrum name="radiance" type="uniform"/>
        </emitter>
    </shape>

    <shape type="sphere" id="sensor">
        <boolean name="visible" value="{not hide_sensor}"/>
        <point name="center" x="-3" y="3" z="2.5"/>
        <float name="radius" value="1"/>
        <sensor type="microphone">
            <string name="wavelengths" value="{','.join(str(x) for x in wavs)}"/>
            
            <sampler type="independent">
                <integer name="sample_count" value="{spp}"/>
                <integer name="seed" value="0"/>
            </sampler>
            
            <film type="tape">
                <float name="max_time" value="{max_time}"/>
                <integer name="time_steps" value="{time_steps}"/>
                <rfilter type="box"/>
            </film>
        </sensor>
    </shape>

    <shape type="obj" id="bottom"> <!-- Bottom -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
        </transform>
        <ref id="blend"/>
    </shape>

    <shape type="obj" id="left">  <!-- Left -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="0" y="1" z="0" angle="90"/>
            <translate x="-5" y="0" z="5"/>
        </transform>
        <ref id="blend"/>
    </shape>

    <shape type="obj" id="back">  <!-- Back -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="1" y="0" z="0" angle="90"/>
            <translate x="0" y="5" z="5"/>
        </transform>
        <ref id="blend"/>
    </shape>

    <shape type="obj" id="front">  <!-- Front -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="1" y="0" z="0" angle="-90"/>
            <translate x="0" y="-5" z="5"/>
        </transform>
        <ref id="blend"/>
    </shape>

    <shape type="obj" id="right">  <!-- Right -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="0" y="1" z="0" angle="-90"/>
            <translate x="5" y="0" z="5"/>
        </transform>
        <ref id="blend"/>
    </shape>

    <shape type="obj" id="top">  <!-- Top -->
        <string name="filename" value="resources/data/common/meshes/rectangle.obj"/>
        <transform name="to_world">
            <scale x="5" y="5" z="5"/>
            <rotate x="0" y="1" z="0" angle="180"/>
            <translate x="0" y="0" z="10"/>
        </transform>
        <ref id="blend"/>
    </shape>
</scene>
"""


def ISM_room_scene(max_time, time_steps, spp, wavs, scattering=0.0, absorption=0.0, hide_sensor=True):
    return f"""
<scene version="2.1.0">
    <bsdf type="acousticbsdf" id="blend">
        <spectrum name="scattering" value="{scattering}"/>
        <spectrum name="absorption" type="acoustic">
            <boolean name="absorption" value="true"/>
            <float name="value" value="{absorption}"/>
         </spectrum>
    </bsdf>
    
    <shape type="ply" id="cube">
        <string name="filename" value="resources/data/scenes/acoustic/meshes/Cube.ply"/>
        <ref id="blend"/>
    </shape>
    <shape type="ply" id="emitter">
        <string name="filename" value="resources/data/scenes/acoustic/meshes/Emitter.ply"/>
        <emitter type="area">
            <spectrum name="radiance" type="uniform"/>
        </emitter>
    </shape>
    <shape type="ply" id="receiver">
        <boolean name="visible" value="{not hide_sensor}"/>
        <string name="filename" value="resources/data/scenes/acoustic/meshes/Receiver.ply"/>
        <sensor type="microphone">
            <string name="wavelengths" value="{','.join(str(x) for x in wavs)}"/>
            
            <sampler type="independent">
                <integer name="sample_count" value="{spp}"/>
                <integer name="seed" value="0"/>
            </sampler>
            
            <film type="tape">
                <float name="max_time" value="{max_time}"/>
                <integer name="time_steps" value="{time_steps}"/>
                <rfilter type="box"/>
            </film>
        </sensor>
    </shape>
</scene>
"""


def get_vals(data, time_steps, bin_count):
    return np.array(data, copy=False).reshape([time_steps, bin_count])


def make_integrator(bins, max_time=1.):
    str_bins = list(map(str, bins))
    from mitsuba.core.xml import load_string
    integrator = load_string(f"""
    <integrator version='2.0.0' type='acousticpath'>
        <float name='max_time' value='{max_time}'/>
        <string name='wavelength_bins' value='{','.join(str_bins)}'/>
    </integrator>
    """)
    assert integrator is not None
    return integrator


def test01_create(variant_scalar_acoustic):
    from mitsuba.core.xml import load_string
    bins = [20, 40, 80, 16000]
    integrator = make_integrator(bins, 1)
    print(integrator)


def test02_render_specular_single(variant_scalar_acoustic):
    from mitsuba.core.xml import load_string

    bins = [1, 2]
    max_time = 1
    time_steps = 100

    integrator = make_integrator(bins=bins, max_time=max_time)

    scene = load_string(ISM_room_scene(
        max_time=max_time,
        time_steps=time_steps,
        spp=10,
        wavs=bins[:-1],
        scattering=0.0,
        absorption=0.5
    ))
    sensor = scene.sensors()[0]

    status = integrator.render(scene, sensor)
    assert status

    film = sensor.film()
    raw = film.bitmap(raw=True)
    counts = film.bitmap(raw=False)
    vals = get_vals(raw, time_steps, len(bins) - 1)
    vals_count = get_vals(counts, time_steps, len(bins) - 1)

    print("sum:", np.sum(vals))

    plt.plot(vals_count, label='count')
    plt.plot(vals, label='vals')
    plt.plot(vals / vals_count, label='normalized')
    plt.legend()
    plt.show()
