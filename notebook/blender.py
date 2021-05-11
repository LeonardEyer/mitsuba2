import bpy
from bpy import data as D
from bpy import context as C
import mathutils as mathutils
from math import *

def get_vertices(object):
    verts = object.data.vertices
    verts_global = [object.matrix_world @ v.co for v in verts]
    return verts_global
    
def does_intersect(a, b, sphere_pos, sphere_radius=1.0):
    a, b = mathutils.geometry.intersect_line_sphere(a, b, sphere_pos, sphere_radius)
    if a == None or b == None:
        return False
    return True

def pairs(x):
    return list(zip(x[::2], x[1::2]))
 
def line_intersects(line_verts, sphere_pos, sphere_radius=1.0):
    for a, b in pairs(line_verts):
        if does_intersect(a, b, sphere_pos, sphere_radius):
            return True
    return False

path_names = ['path' + str(i+1) + '.003' for i in range(99)]
path_objs = [D.objects[name] for name in path_names]


emitter_pos = [20, 7, 2]
sensor_pos = [9, 1, 6]

def hide_not_intersected_sphere(pos, radius=1.0):
    def for_obj(obj):
        obj.hide_set(not line_intersects(get_vertices(obj), pos, radius))
    return for_obj

for x in path_objs:
    hide_not_intersected_sphere(emitter_pos)(x)
    
