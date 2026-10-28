"""Evaluated mesh projection + clipped rectangle ESTIMATE, never pixel bounds."""
def summarize_projection(points):
    if not points:return dict(projected_bounds=None,clipped_bounds=None,screen_center=None,screen_height_ratio=0.,screen_width_ratio=0.,visible_fraction_estimate=0.,projection_state='BEHIND_OR_DEPTH_CLIPPED',method='EVALUATED_MESH_PROJECTED_RECT_ESTIMATE')
    xs=[p[0] for p in points];ys=[p[1] for p in points];b=[min(xs),min(ys),max(xs),max(ys)]
    c=[max(0.,b[0]),max(0.,b[1]),min(1.,b[2]),min(1.,b[3])]
    area=max(0,b[2]-b[0])*max(0,b[3]-b[1]);visible=max(0,c[2]-c[0])*max(0,c[3]-c[1])
    fraction=visible/area if area else 0.
    return dict(projected_bounds=b,clipped_bounds=c if visible>0 else None,screen_center=[(b[0]+b[2])/2,(b[1]+b[3])/2],
        screen_height_ratio=b[3]-b[1],screen_width_ratio=b[2]-b[0],visible_fraction_estimate=fraction,
        projection_state='OUT_OF_FRAME' if not visible else 'PARTIAL' if fraction<1-1e-8 else 'IN_FRAME',method='EVALUATED_MESH_PROJECTED_RECT_ESTIMATE')

def project_mesh(scene,camera,vertices,edges):
    """Clip actual mesh edges to camera near/far depth before perspective divide."""
    from bpy_extras.object_utils import world_to_camera_view
    inv=camera.matrix_world.inverted();near=camera.data.clip_start;far=camera.data.clip_end
    depths=[-(inv@v).z for v in vertices];points=[]
    for v,d in zip(vertices,depths):
        if near<=d<=far:points.append(world_to_camera_view(scene,camera,v)[:2])
    for i,j in edges:
        a,b=depths[i],depths[j]
        if a==b:continue
        for plane in (near,far):
            t=(plane-a)/(b-a)
            if 0<t<1:points.append(world_to_camera_view(scene,camera,vertices[i].lerp(vertices[j],t))[:2])
    return points

def occlusion_label(visible_count,total):
    if total==0:return dict(occlusion_ratio=None,visibility='HIDDEN',confidence='ESTIMATED',samples=0)
    ratio=1-visible_count/total
    return dict(occlusion_ratio=ratio,visibility='HIDDEN' if ratio>=1 else 'MOSTLY_OCCLUDED' if ratio>=.75 else 'PARTIAL' if ratio>.05 else 'VISIBLE',confidence='ESTIMATED',samples=total)

def bounds_gap(a,b):
    if a is None or b is None:return None
    dx=max(a[0]-b[2],b[0]-a[2],0);dy=max(a[1]-b[3],b[1]-a[3],0)
    return (dx*dx+dy*dy)**.5
