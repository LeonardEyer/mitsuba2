import bpy
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *

#! 
D.objects['path2.003'].vertices
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! AttributeError: 'Object' object has no attribute 'vertices'
#! 
D.objects['path2.003'].mesh
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! AttributeError: 'Object' object has no attribute 'mesh'
#! 
D.objects['path2.003'].data.vertices
#~ bpy.data.meshes['path2.003'].vertices
#~ 
D.objects['path2.003'].data.vertices[0]
#~ bpy.data.meshes['path2.003'].vertices[0]
#~ 
D.objects['path2.003'].data.vertices.co
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! AttributeError: 'bpy_prop_collection' object has no attribute 'co'
#! 
D.objects['path2.003'].data.vertices[0].co
#~ Vector((9.0, 6.0, 1.0))
#~ 
def get_vertices(object):
    verts = object.data.vertices
    verts_local = [x.co for x in verts]
    verts_global = [obj.matrix_world @ v.co for v in verts]
    return verts_global
    
get_verts(D.objects['path2.003'])
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! NameError: name 'get_verts' is not defined
#! 
get_vertiices(D.objects['path2.003'])
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! NameError: name 'get_vertiices' is not defined
#! 
get_vertices(D.objects['path2.003'])
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#!   File "<blender_console>", line 4, in get_vertices
#!   File "<blender_console>", line 4, in <listcomp>
#! NameError: name 'obj' is not defined
#! 
def get_vertices(object):
    verts = object.data.vertices
    verts_global = [object.matrix_world @ v.co for v in verts]
    return verts_global
    
get_vertices(D.objects['path2.003'])
#~ [Vector((9.0, 6.0, 1.0)), Vector((14.260000228881836, 12.0, 2.5590600967407227)), Vector((14.260000228881836, 12.0, 2.5590600967407227)), Vector((24.780099868774414, 0.0, 5.6771697998046875)), Vector((24.780099868774414, 0.0, 5.6771697998046875)), Vector((25.0, 0.25080400705337524, 5.742340087890625)), Vector((25.0, 0.25080400705337524, 5.742340087890625)), Vector((20.756799697875977, 5.090869903564453, 7.0)), Vector((20.756799697875977, 5.090869903564453, 7.0)), Vector((14.699799537658691, 12.0, 5.204710006713867)), Vector((14.699799537658691, 12.0, 5.204710006713867)), Vector((4.1797099113464355, 0.0, 2.0866000652313232)), Vector((4.1797099113464355, 0.0, 2.0866000652313232)), Vector((0.0, 4.7676801681518555, 0.8477489948272705)), Vector((0.0, 4.7676801681518555, 0.8477489948272705)), Vector((2.860189914703369, 8.030229568481445, 0.0)), Vector((2.860189914703369, 8.030229568481445, 0.0)), Vector((6.3403801918029785, 12.0, 1.0315200090408325)), Vector((6.3403801918029785, 12.0, 1.0315200090408325)), Vector((16.86050033569336, 0.0, 4.149630069732666))]
#~ 
len(get_vertices(D.objects['path2.003'])=



c


dsa
#!   File "<blender_console>", line 13
#!     dsa
#!       ^
#! SyntaxError: invalid syntax
#! 
len(get_vertices(D.objects['path2.003'])
)
#~ 20
#~ 
len(get_vertices(D.objects['path6.003']))
#~ 20
#~ 
mathutils.geometry.intersect_line_sphere([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5], 0.1)
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! NameError: name 'mathutils' is not defined
#! 
import mathutils as mathutils
mathutils.geometry.intersect_line_sphere([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5], 0.1)
#~ (Vector((0.557735025882721, 0.557735025882721, 0.557735025882721)), Vector((0.44226500391960144, 0.44226500391960144, 0.44226500391960144)))
#~ 
mathutils.geometry.intersect_line_sphere([0, 0, 0], [1, 1, 1], [5, 5, 5], 0.1)
#~ (None, None)
#~ 
def does_intersect(a, b, sphere_pos, sphere_radius=1.0):
    a, b = mathutils.geometry.intersect_line_sphere(a, b, sphere_pos, sphere_radius)
    if a == None or b == None:
        return False
    return True
    
does_intersect([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5], 0.1)
#~ True
#~ 
does_intersect([0, 0, 0], [1, 1, 1], [0.5, 0.5, 5], 0.1)
#~ False
#~ 
from itertools import izip
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! ImportError: cannot import name 'izip' from 'itertools' (unknown location)
#! 

def pairwise(t):
    it = iter(t)
    return izip(it,it)
    
pairwise([1. 2. 3. 4. 5. 6. 7. 8. 9])
#!   File "<blender_console>", line 1
#!     pairwise([1. 2. 3. 4. 5. 6. 7. 8. 9])
#!                   ^
#! SyntaxError: invalid syntax
#! 
pairwise([1, 2, 3, 4, 5, 6, 7, 8, 9])
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#!   File "<blender_console>", line 3, in pairwise
#! NameError: name 'izip' is not defined
#! 
t = [1 



]
t = [1, 2, 3, 4, 5, 6, 7, 8, 9]
zip(t[::2], t[1::2])
#~ <zip object at 0x14393b190>
#~ 
list(zip(t[::2], t[1::2]))
#~ [(1, 2), (3, 4), (5, 6), (7, 8)]
#~ 
def pairs(x):
    return list(zip(x[::2], x[1::2]))
    
some_verts = get_vertices(D.objects['path6.003'])
some_verts
#~ [Vector((9.0, 6.0, 1.0)), Vector((10.370699882507324, 12.0, 1.4101200103759766)), Vector((10.370699882507324, 12.0, 1.4101200103759766)), Vector((13.112099647521973, 0.0, 2.230370044708252)), Vector((13.112099647521973, 0.0, 2.230370044708252)), Vector((15.853400230407715, 12.0, 3.0506200790405273)), Vector((15.853400230407715, 12.0, 3.0506200790405273)), Vector((18.59480094909668, 0.0, 3.8708701133728027)), Vector((18.59480094909668, 0.0, 3.8708701133728027)), Vector((21.336200714111328, 12.0, 4.691120147705078)), Vector((21.336200714111328, 12.0, 4.691120147705078)), Vector((24.077499389648438, 0.0, 5.5113701820373535)), Vector((24.077499389648438, 0.0, 5.5113701820373535)), Vector((25.0, 4.037930011749268, 5.787380218505859)), Vector((25.0, 4.037930011749268, 5.787380218505859)), Vector((23.181100845336914, 12.0, 6.331620216369629)), Vector((23.181100845336914, 12.0, 6.331620216369629)), Vector((20.94729995727539, 2.2218101024627686, 7.0)), Vector((20.94729995727539, 2.2218101024627686, 7.0)), Vector((20.439699172973633, 0.0, 6.848130226135254))]
#~ 
pairs(some_verts)
#~ [(Vector((9.0, 6.0, 1.0)), Vector((10.370699882507324, 12.0, 1.4101200103759766))), (Vector((10.370699882507324, 12.0, 1.4101200103759766)), Vector((13.112099647521973, 0.0, 2.230370044708252))), (Vector((13.112099647521973, 0.0, 2.230370044708252)), Vector((15.853400230407715, 12.0, 3.0506200790405273))), (Vector((15.853400230407715, 12.0, 3.0506200790405273)), Vector((18.59480094909668, 0.0, 3.8708701133728027))), (Vector((18.59480094909668, 0.0, 3.8708701133728027)), Vector((21.336200714111328, 12.0, 4.691120147705078))), (Vector((21.336200714111328, 12.0, 4.691120147705078)), Vector((24.077499389648438, 0.0, 5.5113701820373535))), (Vector((24.077499389648438, 0.0, 5.5113701820373535)), Vector((25.0, 4.037930011749268, 5.787380218505859))), (Vector((25.0, 4.037930011749268, 5.787380218505859)), Vector((23.181100845336914, 12.0, 6.331620216369629))), (Vector((23.181100845336914, 12.0, 6.331620216369629)), Vector((20.94729995727539, 2.2218101024627686, 7.0))), (Vector((20.94729995727539, 2.2218101024627686, 7.0)), Vector((20.439699172973633, 0.0, 6.848130226135254)))]
#~ 
for a, b in pairs(some_verts)
#!   File "<blender_console>", line 1
#!     for a, b in pairs(some_verts)
#!                                 ^
#! SyntaxError: invalid syntax
#! 
for a, b in pairs(some_verts):
    print(does_intersect(a, b, [9, 6, 1])
    
    


)

#~ False
#~ False
#~ False
#~ False
#~ False
#~ False
#~ False
#~ False
#~ False
#~ False
#~ 
def line_intersects(line_verts, sphere_pos, sphere_radius=1.0):
    for a, b in pairs(line_verts):
        if does_intersect(a, b, sphere_pos, sphere_radius):
            return true
    return False
    
line_intersects(some_verts, [9, 6, 1])
#~ False
#~ 
def line_obj_intersect_sensor(obj):
    return line_intersects(get_vertices(obj), [9, 6, 1])
    
line_obj_intersect_sensor(D.objects['path6.003'])
#~ False
#~ 
['path' + i + '.003' for in in range(99)]
#!   File "<blender_console>", line 1
#!     ['path' + i + '.003' for in in range(99)]
#!                               ^
#! SyntaxError: invalid syntax
#! 
['path' + i + '.003' for i in range(99)]
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#!   File "<blender_console>", line 1, in <listcomp>
#! TypeError: can only concatenate str (not "int") to str
#! 
['path' + str(i) + '.003' for i in range(99)]
#~ ['path0.003', 'path1.003', 'path2.003', 'path3.003', 'path4.003', 'path5.003', 'path6.003', 'path7.003', 'path8.003', 'path9.003', 'path10.003', 'path11.003', 'path12.003', 'path13.003', 'path14.003', 'path15.003', 'path16.003', 'path17.003', 'path18.003', 'path19.003', 'path20.003', 'path21.003', 'path22.003', 'path23.003', 'path24.003', 'path25.003', 'path26.003', 'path27.003', 'path28.003', 'path29.003', 'path30.003', 'path31.003', 'path32.003', 'path33.003', 'path34.003', 'path35.003', 'path36.003', 'path37.003', 'path38.003', 'path39.003', 'path40.003', 'path41.003', 'path42.003', 'path43.003', 'path44.003', 'path45.003', 'path46.003', 'path47.003', 'path48.003', 'path49.003', 'path50.003', 'path51.003', 'path52.003', 'path53.003', 'path54.003', 'path55.003', 'path56.003', 'path57.003', 'path58.003', 'path59.003', 'path60.003', 'path61.003', 'path62.003', 'path63.003', 'path64.003', 'path65.003', 'path66.003', 'path67.003', 'path68.003', 'path69.003', 'path70.003', 'path71.003', 'path72.003', 'path73.003', 'path74.003', 'path75.003', 'path76.003', 'path77.003', 'path78.003', 'path79.003', 'path80.003', 'path81.003', 'path82.003', 'path83.003', 'path84.003', 'path85.003', 'path86.003', 'path87.003', 'path88.003', 'path89.003', 'path90.003', 'path91.003', 'path92.003', 'path93.003', 'path94.003', 'path95.003', 'path96.003', 'path97.003', 'path98.003']
#~ 
['path' + str(i+1) + '.003' for i in range(99)]
#~ ['path1.003', 'path2.003', 'path3.003', 'path4.003', 'path5.003', 'path6.003', 'path7.003', 'path8.003', 'path9.003', 'path10.003', 'path11.003', 'path12.003', 'path13.003', 'path14.003', 'path15.003', 'path16.003', 'path17.003', 'path18.003', 'path19.003', 'path20.003', 'path21.003', 'path22.003', 'path23.003', 'path24.003', 'path25.003', 'path26.003', 'path27.003', 'path28.003', 'path29.003', 'path30.003', 'path31.003', 'path32.003', 'path33.003', 'path34.003', 'path35.003', 'path36.003', 'path37.003', 'path38.003', 'path39.003', 'path40.003', 'path41.003', 'path42.003', 'path43.003', 'path44.003', 'path45.003', 'path46.003', 'path47.003', 'path48.003', 'path49.003', 'path50.003', 'path51.003', 'path52.003', 'path53.003', 'path54.003', 'path55.003', 'path56.003', 'path57.003', 'path58.003', 'path59.003', 'path60.003', 'path61.003', 'path62.003', 'path63.003', 'path64.003', 'path65.003', 'path66.003', 'path67.003', 'path68.003', 'path69.003', 'path70.003', 'path71.003', 'path72.003', 'path73.003', 'path74.003', 'path75.003', 'path76.003', 'path77.003', 'path78.003', 'path79.003', 'path80.003', 'path81.003', 'path82.003', 'path83.003', 'path84.003', 'path85.003', 'path86.003', 'path87.003', 'path88.003', 'path89.003', 'path90.003', 'path91.003', 'path92.003', 'path93.003', 'path94.003', 'path95.003', 'path96.003', 'path97.003', 'path98.003', 'path99.003']
#~ 
path_names = ['path' + str(i+1) + '.003' for i in range(99)]
path_objs = [D.objects[name] for name in path_names]
map(line_obj_intersect_sensor, path_objs)
#~ <map object at 0x1286f8c90>
#~ 
list(map(line_obj_intersect_sensor, path_objs))
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#!   File "<blender_console>", line 2, in line_obj_intersect_sensor
#!   File "<blender_console>", line 4, in line_intersects
#! NameError: name 'true' is not defined
#! 
path_names
#~ ['path1.003', 'path2.003', 'path3.003', 'path4.003', 'path5.003', 'path6.003', 'path7.003', 'path8.003', 'path9.003', 'path10.003', 'path11.003', 'path12.003', 'path13.003', 'path14.003', 'path15.003', 'path16.003', 'path17.003', 'path18.003', 'path19.003', 'path20.003', 'path21.003', 'path22.003', 'path23.003', 'path24.003', 'path25.003', 'path26.003', 'path27.003', 'path28.003', 'path29.003', 'path30.003', 'path31.003', 'path32.003', 'path33.003', 'path34.003', 'path35.003', 'path36.003', 'path37.003', 'path38.003', 'path39.003', 'path40.003', 'path41.003', 'path42.003', 'path43.003', 'path44.003', 'path45.003', 'path46.003', 'path47.003', 'path48.003', 'path49.003', 'path50.003', 'path51.003', 'path52.003', 'path53.003', 'path54.003', 'path55.003', 'path56.003', 'path57.003', 'path58.003', 'path59.003', 'path60.003', 'path61.003', 'path62.003', 'path63.003', 'path64.003', 'path65.003', 'path66.003', 'path67.003', 'path68.003', 'path69.003', 'path70.003', 'path71.003', 'path72.003', 'path73.003', 'path74.003', 'path75.003', 'path76.003', 'path77.003', 'path78.003', 'path79.003', 'path80.003', 'path81.003', 'path82.003', 'path83.003', 'path84.003', 'path85.003', 'path86.003', 'path87.003', 'path88.003', 'path89.003', 'path90.003', 'path91.003', 'path92.003', 'path93.003', 'path94.003', 'path95.003', 'path96.003', 'path97.003', 'path98.003', 'path99.003']
#~ 
def line_intersects(line_verts, sphere_pos, sphere_radius=1.0):
    for a, b in pairs(line_verts):
        if does_intersect(a, b, sphere_pos, sphere_radius):
            return True
    return False
    
list(map(line_obj_intersect_sensor, path_objs))
#~ [False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, True, False, False, False, False, False, False, True, False, True, False, True, False, False, False]
#~ 
def hide_not_intersected(obj):
    obj.visible = line_obj_intersect_sensor(obj)
    
hide_not_visible(D.objects['path6.003'])
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#! NameError: name 'hide_not_visible' is not defined
#! 
hide_not_intersected(D.objects['path6.003'])
#! Traceback (most recent call last):
#!   File "<blender_console>", line 1, in <module>
#!   File "<blender_console>", line 2, in hide_not_intersected
#! AttributeError: 'Object' object has no attribute 'visible'
#! 
D.objects['path0.003'].hide_set(False)
D.objects['path0.003'].hide_set(True)
def hide_not_intersected(obj):
    obj.hide_set(not line_obj_intersect_sensor(obj))
    
hide_not_intersected( D.objects['path0.003'])
hide_not_intersected( D.objects['path0.003'])
map(hide_not_intersected, path_objs)
#~ <map object at 0x138898650>
#~ 
for x in path_objs:
    hide_not_intersected(x)
    
sum(list(map(line_obj_intersect_sensor, path_objs)))
#~ 14
#~ 
