"""Native support metadata and measured finite-surface contact. bpy offline only."""
import json,math
KEY='previs_support_index';TABLE='previs_support_registry'
def apply_support(obj,state,frame):
    value={k:v for k,v in state.items() if k!='contract'};registry=json.loads(obj.get(TABLE,'[]'))
    if value not in registry:registry.append(value);obj[TABLE]=json.dumps(registry,sort_keys=True,separators=(',',':'))
    obj[KEY]=registry.index(value)
    if frame is not None:obj.keyframe_insert(data_path='["'+KEY+'"]',frame=frame)
def native_support(obj):
    if KEY not in obj:return None
    values=json.loads(obj[TABLE]);i=float(obj[KEY])
    if abs(i-round(i))>1e-7 or not 0<=round(i)<len(values):raise ValueError('INVALID_NATIVE_SUPPORT_INDEX')
    return values[round(i)]
def bounds(obj):
    from mathutils import Vector
    points=[obj.matrix_world@Vector(p) for p in obj.bound_box]
    return [min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]
def surface_at(obj,x,y):
    """Declared planar local +Z face of existing simple cuboid; finite footprint."""
    from mathutils import Vector
    lo=[min(p[i] for p in obj.bound_box) for i in range(3)];hi=[max(p[i] for p in obj.bound_box) for i in range(3)];inv=obj.matrix_world.inverted();a=inv@Vector((x,y,100));d=inv.to_3x3()@Vector((0,0,-1))
    if abs(d.z)<1e-8:raise ValueError('UNSUPPORTED_VERTICAL_SUPPORT_FACE')
    v=a+d*((hi[2]-a.z)/d.z);point=obj.matrix_world@v
    return point,all(lo[i]-1e-5<=v[i]<=hi[i]+1e-5 for i in (0,1))
def contact_measure(objects,c,body_center,body_bottom):
    from mathutils import Vector
    src=objects[c['source']]
    if c['role']=='HAND':
        p=objects[c['probe']].matrix_world.translation;target=src.matrix_world.translation
        return dict(point=list(p),gap=(p-target).length,inside=True,span=(p-Vector(body_center)).length,link_error=0)
    if c['role']=='SEAT':
        point=Vector((body_center[0],body_center[1],body_bottom));surface,inside=surface_at(src,point.x,point.y)
        return dict(point=list(point),gap=point.z-surface.z,inside=inside,span=0,link_error=0)
    probe=objects[c['probe']];lo,hi=bounds(probe);point=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]));surface,inside=surface_at(src,point.x,point.y)
    link=objects[c['link']];ll,lh=bounds(link);top=Vector((body_center[0]+c['offset'][0],body_center[1]+c['offset'][1],body_bottom));span=(top-point).length
    link_error=max(abs(ll[2]-point.z),abs(lh[2]-max(body_bottom,point.z+.002)),abs((ll[0]+lh[0])/2-top.x),abs((ll[1]+lh[1])/2-top.y))
    return dict(point=list(point),gap=point.z-surface.z,inside=inside,span=span,link_error=link_error)
