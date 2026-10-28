"""Opt-in bpy adapter. Refuses driven rigs; never removes constraints to hide errors."""
from .motion import position,aim,progress
def curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   for slot in action.slots:
    bag=strip.channelbag(slot)
    if bag:
     yield from bag.fcurves
def apply_camera(camera,plan,start,end):
 from mathutils import Vector
 if camera.type!='CAMERA' or end<=start:raise ValueError('CAMERA_AND_FRAME_RANGE')
 if camera.parent or len(camera.constraints) or (camera.animation_data and camera.animation_data.drivers):raise ValueError('RIG_REQUIRES_EXPLICIT_ADAPTER')
 if camera.data.animation_data and camera.data.animation_data.drivers:raise ValueError('DRIVEN_CAMERA_DATA_REQUIRES_ADAPTER')
 # Validate every planned sample before writing a key; invalid late samples must
 # not leave a half-mutated camera behind.
 import math
 for f in range(start,end+1):
  u=(f-start)/(end-start);p=position(plan,u);a=aim(plan,u)
  if not all(math.isfinite(v) for v in p+a) or sum((x-y)**2 for x,y in zip(p,a))<1e-16:raise ValueError('INVALID_CAMERA_SAMPLE')
 camera.rotation_mode='QUATERNION';previous=None
 rotation=plan.get('rotation_interpolation','AIM_TARGET')
 if rotation not in {'AIM_TARGET','QUATERNION_ENDPOINTS'}:raise ValueError('UNKNOWN_ROTATION_INTERPOLATION')
 endpoints=None
 if rotation=='QUATERNION_ENDPOINTS':
  if plan['kind']!='STATIC_ROTATION':raise ValueError('ENDPOINT_ROTATION_REQUIRES_FIXED_POSITION')
  targets=[Vector(aim(plan,u))-Vector(position(plan,u)) for u in [0,1]]
  if min(v.length for v in targets)<1e-8:raise ValueError('AIM_AT_CAMERA')
  endpoints=[v.to_track_quat('-Z','Y') for v in targets]
  if abs(targets[1].normalized().z)>1-1e-8:
   # At the vertical pole, world-up cannot determine roll. Preserve the starting roll.
   endpoints[1]=targets[0].normalized().rotation_difference(targets[1].normalized())@endpoints[0]
 for f in range(start,end+1):
  u=(f-start)/(end-start);p=Vector(position(plan,u));target=Vector(aim(plan,u))
  if (target-p).length<1e-8:raise ValueError('AIM_AT_CAMERA')
  q=(target-p).to_track_quat('-Z','Y')
  if endpoints:q=endpoints[0].slerp(endpoints[1],progress(u,plan.get('rotation_curve',plan.get('curve','LINEAR')),plan.get('rotation_beats')))
  if previous and previous.dot(q)<0:q.negate()
  previous=q.copy();camera.location=p;camera.rotation_quaternion=q
  camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_quaternion',frame=f)
 if camera.animation_data:
  for fc in curves(camera.animation_data.action):
   if fc.data_path in {'location','rotation_quaternion'}:
    for k in fc.keyframe_points:
     if start<=k.co.x<=end:k.interpolation='LINEAR'
 return {'kind':plan['kind'],'start':start,'end':end,'interframe':'piecewise linear, native subframes must be measured','purpose':plan.get('purpose')}
