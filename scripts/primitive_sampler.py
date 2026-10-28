"""Deterministic execution math. Global frame conversion belongs to timebase only."""
import math
import json
import hashlib
from timebase import time_to_frame, frame_to_time

def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,s): return [x*s for x in a]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def unit(a): return mul(a,1/norm(a)) if norm(a)>1e-12 else [0.,0.,0.]
def lerp(a,b,u): return add(mul(a,1-u),mul(b,u))
def clamp(x): return max(0.,min(1.,x))
def smooth(u): u=clamp(u); return u*u*u*(10+u*(-15+6*u))
def smooth_integral(u): u=clamp(u); return 2.5*u**4-3*u**5+u**6
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sha(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def frames(start,end,fps):
    lo,hi=time_to_frame(start,fps),time_to_frame(end,fps)
    if abs(frame_to_time(lo,fps)-start)>1e-9 or abs(frame_to_time(hi,fps)-end)>1e-9: raise ValueError('OFF_GRID_TIME')
    return range(lo,hi+1)
def qnorm(q): return mul(q,1/math.sqrt(dot(q,q)))
def qmul(a,b):
    w,x,y,z=a;v,i,j,k=b
    return [w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v]
def rotate(q,v): return qmul(qmul(q,[0]+list(v)),[q[0],-q[1],-q[2],-q[3]])[1:]
def yaw_quat(angle): return [math.cos(angle/2),0.,0.,math.sin(angle/2)]
def qangle(a,b): return 2*math.acos(min(1.,abs(dot(qnorm(a),qnorm(b)))))
def slerp(a,b,u):
    a,b=qnorm(a),qnorm(b);d=dot(a,b)
    if d<0: b=mul(b,-1);d=-d
    if d>1-1e-12:return qnorm(lerp(a,b,u))
    t=math.acos(min(1.,d));return add(mul(a,math.sin((1-u)*t)/math.sin(t)),mul(b,math.sin(u*t)/math.sin(t)))
def look_at(position,target):
    """Blender camera local -Z forward, +Y up; world +Z up."""
    z=unit(sub(position,target));x=unit(cross([0.,0.,1.],z))
    if norm(x)<1e-8:x=[1.,0.,0.]
    y=cross(z,x);m=[[x[i],y[i],z[i]] for i in range(3)];t=sum(m[i][i] for i in range(3))
    if t>0:
        s=math.sqrt(t+1)*2;q=[s/4,(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s]
    else:
        i=max(range(3),key=lambda i:m[i][i]);j=(i+1)%3;k=(i+2)%3;s=math.sqrt(1+m[i][i]-m[j][j]-m[k][k])*2
        q=[0.,0.,0.,0.];q[0]=(m[k][j]-m[j][k])/s;q[i+1]=s/4;q[j+1]=(m[j][i]+m[i][j])/s;q[k+1]=(m[k][i]+m[i][k])/s
    return qnorm(q)
def project(position,orientation,lens,target,aspect=16/9):
    p=rotate([orientation[0],-orientation[1],-orientation[2],-orientation[3]],sub(target,position))
    if p[2]>=-1e-8:return None
    return [.5+p[0]*lens/(-p[2]*36),.5+p[1]*lens*aspect/(-p[2]*36)]
def sample_track(track,t,field='position'):
    if not track: raise ValueError('EMPTY_READ_TRACK')
    if t<=track[0]['time'] or t>=track[-1]['time']:
        edge=track[0] if t<=track[0]['time'] else track[-1]
        return add(edge[field],mul(edge['velocity'],t-edge['time'])) if field=='position' and 'velocity' in edge else edge[field]
    for a,b in zip(track,track[1:]):
        if a['time']<=t<=b['time']:
            u=(t-a['time'])/(b['time']-a['time'])
            return slerp(a[field],b[field],u) if field=='orientation' else lerp(a[field],b[field],u)
def derivative(rows,index,field='position'):
    a,b=(rows[0],rows[1]) if index==0 else (rows[-2],rows[-1]) if index==len(rows)-1 else (rows[index-1],rows[index+1])
    return mul(sub(b[field],a[field]),1/(b['time']-a['time']))
def path(points,kind,u):
    if u<=0:return list(points[0])
    if u>=1:return list(points[-1])
    if kind=='BEZIER_SIMPLE':
        if len(points)!=4:raise ValueError('BEZIER_REQUIRES_FOUR_POINTS')
        p=points
        return add(add(mul(p[0],(1-u)**3),mul(p[1],3*u*(1-u)**2)),add(mul(p[2],3*u*u*(1-u)),mul(p[3],u**3)))
    lengths=[norm(sub(b,a)) for a,b in zip(points,points[1:])];total=sum(lengths);d=u*total
    for i,length in enumerate(lengths):
        if d<=length or i==len(lengths)-1:return lerp(points[i],points[i+1],d/length if length else 0)
        d-=length
    return points[0]
def arclength_path(points,kind):
    if kind not in ('LINEAR','POLYLINE','BEZIER_SIMPLE'):raise ValueError('UNSUPPORTED_PATH')
    if len(points)<2 or kind=='LINEAR' and len(points)!=2:raise ValueError('INVALID_PATH_POINTS')
    ps=[path(points,kind,i/512) for i in range(513)] if kind=='BEZIER_SIMPLE' else points
    length=sum(norm(sub(b,a)) for a,b in zip(ps,ps[1:]))
    return length,lambda u:path(ps,'POLYLINE',clamp(u))

def progress(profile,u,duration,length,v0=None,v1=None,peak=None,curve=None):
    """Integrated scalar speed; explicit inconsistent boundary requests are rejected."""
    u=clamp(u);derived={};avg=length/duration if duration else 0
    if any(v is not None and v<0 for v in (v0,v1,peak)):raise ValueError('NEGATIVE_SPEED_TARGET')
    defaults={'CONSTANT':(avg,avg),'EASE_IN':(0,2*avg),'EASE_OUT':(2*avg,0),'EASE_IN_OUT':(0,0),'ACCEL_CRUISE_DECEL':(0,0),'CUSTOM_NORMALIZED_CURVE':(None,None)}
    if profile not in defaults:raise ValueError('UNKNOWN_TIMING_PROFILE')
    a,b=defaults[profile]
    if v0 is None:v0=a;derived['entry_velocity']='DERIVED'
    if v1 is None:v1=b;derived['exit_velocity']='DERIVED'
    if profile=='ACCEL_CRUISE_DECEL':
        ramp=.25;p=(avg-.125*(v0+v1))/.75
        if p<max(v0,v1)-1e-9:raise ValueError('INFEASIBLE_PEAK_SPEED')
        if peak is not None and abs(p-peak)>1e-6:raise ValueError('PEAK_DISTANCE_DURATION_CONFLICT')
        derived['peak_velocity']={'value':p,'source':'DERIVED' if peak is None else 'EXPLICIT'}
        if u<ramp:s=v0*u+(p-v0)*ramp*smooth_integral(u/ramp)
        elif u<=1-ramp:s=ramp*(v0+p)/2+p*(u-ramp)
        else:
            z=(u-(1-ramp))/ramp;s=ramp*(v0+p)/2+p*(1-2*ramp)+p*ramp*z+(v1-p)*ramp*smooth_integral(z)
        return (s/avg if avg else 0),v0,v1,derived
    if profile=='CUSTOM_NORMALIZED_CURVE':
        if not curve or curve[0]!=[0,0] or curve[-1]!=[1,1] or any(b[0]<=a[0] or b[1]<a[1] for a,b in zip(curve,curve[1:])):raise ValueError('INVALID_NORMALIZED_CURVE')
        # Monotone piecewise cubic Hermite, zero slope at plateaus; slopes audit boundary velocities.
        sec=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(curve,curve[1:])]
        slopes=[sec[0]]+[0 if a*b==0 else 2*a*b/(a+b) for a,b in zip(sec,sec[1:])]+[sec[-1]]
        for i,(a,b) in enumerate(zip(curve,curve[1:])):
            if a[0]<=u<=b[0]:
                h=b[0]-a[0];z=(u-a[0])/h;s=(2*z**3-3*z*z+1)*a[1]+(z**3-2*z*z+z)*h*slopes[i]+(-2*z**3+3*z*z)*b[1]+(z**3-z*z)*h*slopes[i+1];break
        a,b=slopes[0]*avg,slopes[-1]*avg
        candidates=[]
        for i,(left,right) in enumerate(zip(curve,curve[1:])):
            h=right[0]-left[0];A=2*left[1]-2*right[1]+h*(slopes[i]+slopes[i+1]);B=-3*left[1]+3*right[1]-h*(2*slopes[i]+slopes[i+1]);C=h*slopes[i]
            zs=[0,1]+([-B/(3*A)] if abs(A)>1e-12 and 0<-B/(3*A)<1 else [])
            candidates.extend((3*A*z*z+2*B*z+C)/h*avg for z in zs)
        custom_peak=max(candidates)
    else:
        s={'CONSTANT':lambda:u,'EASE_IN':lambda:2*smooth_integral(u),'EASE_OUT':lambda:2*u-2*smooth_integral(u),'EASE_IN_OUT':lambda:smooth(u)}[profile]()
    if (v0 is not None and abs(v0-a)>1e-6) or (v1 is not None and abs(v1-b)>1e-6):raise ValueError('TIMING_BOUNDARY_CONFLICT')
    actual=avg if profile=='CONSTANT' else 1.875*avg if profile=='EASE_IN_OUT' else 2*avg if profile in ('EASE_IN','EASE_OUT') else custom_peak
    derived['peak_velocity']={'value':actual,'source':'DERIVED' if peak is None else 'EXPLICIT'}
    if peak is not None:
        if abs(actual-peak)>1e-6:raise ValueError('PEAK_CONFLICT')
    return s,a,b,derived
