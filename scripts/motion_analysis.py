"""Measurement math only; no animation writes or biomechanical claims."""
import math

def sub(a,b):return [x-y for x,y in zip(a,b)]
def norm(v):return math.sqrt(sum(x*x for x in v))
def distance(a,b):return norm(sub(a,b))
def mean(v):return sum(v)/len(v) if v else 0.
def velocity(a,b,dt):return [v/dt for v in sub(a,b)] if dt>0 else None
def quaternion_angle(a,b):
    dot=abs(sum(x*y for x,y in zip(a,b)))/max(1e-15,norm(a)*norm(b))
    return math.degrees(2*math.acos(min(1.,dot)))
def direction_summary(points):
    d=sub(points[-1],points[0]);length=sum(distance(a,b) for a,b in zip(points,points[1:]))
    return dict(delta=d,net=norm(d),path_length=length,coherence=norm(d)/length if length else 0)
def recovery_summary(positions,speeds,tilts):
    k=max(1,len(speeds)//3)
    return dict(initial_speed=mean(speeds[:k]),final_speed=mean(speeds[-k:]),
        max_speed=max(speeds),max_step=max([distance(a,b) for a,b in zip(positions,positions[1:])] or [0]),
        final_displacement=distance(positions[-k],positions[-1]),
        initial_tilt=mean(tilts[:k]),final_tilt=mean(tilts[-k:]))
