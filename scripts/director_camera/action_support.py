"""Minimal reusable proxy state sampling and geometric support. Not anatomical IK."""
from .motion import mix,progress
def track(nodes,frame):
 if not nodes:raise ValueError('EMPTY_EVENT_TRACK')
 if any(b[0]<=a[0] for a,b in zip(nodes,nodes[1:])):raise ValueError('EVENT_ORDER')
 if frame<=nodes[0][0]:return tuple(nodes[0][1])
 for a,b in zip(nodes,nodes[1:]):
  if frame<=b[0]:return mix(a[1],b[1],progress((frame-a[0])/(b[0]-a[0]),'EASE_IN_OUT'))
 return tuple(nodes[-1][1])
def supported_height(local_min_z,support_z,clearance=0):return support_z+clearance-local_min_z
def prop_distance(prop,anchor,tolerance):
 from .motion import length,sub
 d=length(sub(prop,anchor));return {'distance':d,'within_tolerance':d<=tolerance,'anatomical_grip':'NOT_REVIEWED'}
def world_attachment(matrix,local_offset):
 """Use evaluated orientation as well as translation for persistent held props."""
 from mathutils import Vector
 return matrix@Vector(local_offset)
def evaluated_bounds(objects,depsgraph):
 from mathutils import Vector
 pts=[o.evaluated_get(depsgraph).matrix_world@Vector(p) for o in objects if o.type=='MESH' and not o.hide_render for p in o.evaluated_get(depsgraph).bound_box]
 if not pts:raise ValueError('NO_VISIBLE_SUPPORT_GEOMETRY')
 return {'min':tuple(min(p[i] for p in pts) for i in range(3)),'max':tuple(max(p[i] for p in pts) for i in range(3))}
