"""Opt-in authored motion envelopes. Legacy relative continuity thresholds stay intact."""
import math
from motion_analysis import norm,sub,distance
ZERO_SPEED_EPS=0.003
MIN_RAMP_SAMPLES=8
MAX_STEP_FRACTION=0.1

def evaluate_envelope(positions,fps,entry_velocity,exit_velocity,semantics):
    allowed={'AUTHORED_START','AUTHORED_STOP','CONTINUOUS_TRANSITION','SMOOTH_OFFSET'}
    if not semantics or not set(semantics)<=allowed:raise ValueError('INVALID_BOUNDARY_SEMANTIC')
    vel=[list(entry_velocity)]+[[x*fps for x in sub(b,a)] for a,b in zip(positions,positions[1:])]+[list(exit_velocity)]
    peak=max(map(norm,vel));eps=ZERO_SPEED_EPS
    if peak<=eps:return {'status':'PASS','semantics':semantics,'peak_speed':peak,'basis':'ALL_SAMPLES_NEAR_ZERO'}
    steps=[distance(a,b)/peak for a,b in zip(vel,vel[1:])]
    failures=[]
    if max(steps)>MAX_STEP_FRACTION:failures.append('ABRUPT_VELOCITY_STEP')
    def ramp(values,label):
        speeds=list(map(norm,values));first=next((i for i,s in enumerate(speeds) if s>eps),None)
        reach=next((i for i,s in enumerate(speeds) if s>=peak*.5),None)
        if first is None or reach is None or reach<MIN_RAMP_SAMPLES:failures.append(label+'_ACCELERATION_WINDOW_MISSING')
        # The first moving interval must remain close to the declared zero limit.
        if speeds[1]>max(eps,peak*.01):failures.append(label+'_BOUNDARY_LIMIT_MISMATCH')
        if reach is not None and any(speeds[i+1]+eps<speeds[i] for i in range(reach)):failures.append(label+'_NON_PROGRESSIVE_RAMP')
    if 'AUTHORED_START' in semantics:
        if norm(entry_velocity)>eps:failures.append('AUTHORED_START_NONZERO_ENTRY')
        ramp(vel,'ENTRY')
    if 'AUTHORED_STOP' in semantics:
        if norm(exit_velocity)>eps:failures.append('AUTHORED_STOP_NONZERO_EXIT')
        ramp(vel[::-1],'EXIT')
    # Direction comparisons are meaningful above zero; no tiny-floor ratio.
    angles=[]
    for a,b in zip(vel,vel[1:]):
        if min(norm(a),norm(b))>peak*.01:
            angle=math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/(norm(a)*norm(b))))));angles.append(angle)
            if angle>45:failures.append('DIRECTION_DISCONTINUITY')
    return {'status':'FAIL' if failures else 'PASS','semantics':semantics,'failure_codes':sorted(set(failures)),'peak_speed':peak,'max_velocity_step_fraction':max(steps),'max_direction_change':max(angles or [0]),'entry_velocity':entry_velocity,'exit_velocity':exit_velocity,'technical_defaults':{'source':'TECHNICAL_DEFAULT S53R/1.0','zero_speed_eps':eps,'minimum_ramp_samples':MIN_RAMP_SAMPLES,'max_step_fraction':MAX_STEP_FRACTION},'basis':'SAMPLED_AUTHORED_ENVELOPE_NOT_RELATIVE_TO_ZERO; C2 retained'}

def apply_semantics(report,rows,p):
    from primitive_sampler import sub
    q=p['parameters'];typ=p['primitive_type'];sem=[]
    if typ=='OFFSET_PATH':
        pos=[r['offset'] for r in rows];entry=exit=[0,0,0];sem=['AUTHORED_START','AUTHORED_STOP','SMOOTH_OFFSET']
        if q['return_mode']=='TRANSITION_TO_NEW_PATH':return report
        peak=min(range(len(rows)),key=lambda i:abs(rows[i]['time']-q['peak_time']))
        parts=[evaluate_envelope(pos[:peak+1],report['fps'],entry,exit,sem),evaluate_envelope(pos[peak:],report['fps'],entry,exit,sem)]
    else:
        pos=[r['position'] for r in rows];entry=rows[0]['velocity'];exit=rows[-1]['velocity']
        if norm(entry)<=ZERO_SPEED_EPS:sem.append('AUTHORED_START')
        if norm(exit)<=ZERO_SPEED_EPS:sem.append('AUTHORED_STOP')
        if not sem:return report
        parts=[evaluate_envelope(pos,report['fps'],entry,exit,sem)]
    report['legacy_relative_dimensions']=dict(report['dimensions'])
    report['boundary_semantic_evidence']=parts
    report['dimensions']['C1']='PASS' if all(x['status']=='PASS' for x in parts) else 'FAIL'
    report['status']='FAIL' if 'FAIL' in report['dimensions'].values() else 'WARNING' if 'WARNING' in report['dimensions'].values() else 'PASS'
    return report
