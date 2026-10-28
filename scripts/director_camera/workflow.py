"""Production planning checks and persisted finite repair budgets.

The author (Codex or a human) interprets prose. This module checks explicit
decisions; it never claims semantic understanding or artistic acceptance.
New contract uses integer HALF-OPEN frame ranges. Legacy adapters are explicit.
"""
import hashlib
import json
import math
import os
from pathlib import Path
from .motion import position, aim
from .revision_dependencies import render_dependencies

def integer(value, name):
    if type(value) is not int:
        raise ValueError(name + ': integer frame required')
    return value

def validate_plan(plan):
    if plan.get('schema') != 'DIRECTOR_PLAN/1':
        raise ValueError('DIRECTOR_PLAN/1 required')
    fps=plan['fps']
    if isinstance(fps,bool) or not isinstance(fps,(int,float)) or not math.isfinite(fps) or fps<=0:
        raise ValueError('positive finite fps required')
    if plan.get('frame_convention') != 'HALF_OPEN':
        raise ValueError('explicit HALF_OPEN required')
    first=integer(plan['start'],'start');last=integer(plan['end'],'end')
    if last<=first:raise ValueError('empty timeline')
    shots=plan['shots'];ids=set();cameras=set();cursor=first
    if not shots:raise ValueError('empty shot list')
    for sh in shots:
        sid=sh['id'];s=integer(sh['start'],'shot start');e=integer(sh['end'],'shot end')
        if not isinstance(sid,str) or not sid or sid in ids:raise ValueError('unique nonempty shot ID required')
        ids.add(sid)
        if s!=cursor or e<=s:raise ValueError('gap, overlap or empty shot')
        cursor=e
        for key in ('purpose','first_focus','start_read','end_read','cut_reason','source'):
            if not sh.get(key):raise ValueError('missing directing decision: '+key)
        cam=sh['camera'];cid=cam['id']
        if cid in cameras:raise ValueError('use a separate shot camera; reuse setup values explicitly')
        cameras.add(cid)
        lens=cam['lens_mm']
        if isinstance(lens,bool) or not isinstance(lens,(int,float)) or not math.isfinite(lens) or lens<=0:raise ValueError('invalid lens')
        motion=cam['motion']
        if motion['kind'] in {'ORBIT','INTENTIONAL_ARC','COMPOUND_MOVE','FOLLOW_WITH_LAG'} and not cam.get('movement_reason'):
            raise ValueError('complex move requires narrative reason')
        if e-s==1 and motion['kind']!='STATIC_HOLD':raise ValueError('one-frame shot cannot express a move')
        for i in range(max(2,e-s)):
            u=i/(max(2,e-s)-1);p=position(motion,u);a=aim(motion,u)
            if not all(math.isfinite(x) for x in p+a):raise ValueError('nonfinite camera')
            if sum((x-y)**2 for x,y in zip(p,a))<1e-16:raise ValueError('camera aims at itself')
            if motion['kind']=='STATIC_HOLD' and sum((x-y)**2 for x,y in zip(a,aim(motion,0)))>1e-16:
                raise ValueError('static hold cannot change aim through waypoints')
        for event in sh.get('events',[]):
            f=integer(event['frame'],'event frame')
            if not s<=f<e or not event.get('id') or not event.get('observable'):
                raise ValueError('event needs in-shot frame, ID and visible result')
        for f in sh.get('motion_nodes',[]):
            if not s<=integer(f,'motion node')<e:raise ValueError('motion node outside shot')
    if cursor!=last:raise ValueError('timeline coverage mismatch')
    return dict(technical='PLAN_VALID',director='NOT_REVIEWED',frames=last-first,shots=len(shots))

def review_schedule(plan):
    validate_plan(plan);rows=[]
    step=max(1,round(plan['fps']/2))
    for sh in plan['shots']:
        s,e=sh['start'],sh['end'];frames={s,e-1,*range(s,e,step),*sh.get('motion_nodes',[])}
        windows=[]
        for event in sh.get('events',[]):
            a,b=max(s,event['frame']-2),min(e,event['frame']+3)
            frames.update(range(a,b));windows.append(dict(event=event['id'],start=a,end=b,observable=event['observable']))
        rows.append(dict(shot=sh['id'],frames=sorted(frames),event_windows=windows))
    return dict(shots=rows,cut_pairs=[[s['start']-1,s['start']] for s in plan['shots'][1:]],
                playback={'speed':1,'scope':'entire encoded video','status':'NOT_REVIEWED'},
                evidence_note='Extract from encoded MP4; these are requested samples, not completed visual review.')

def invalidation(plan, changes):
    """Inclusive legacy helper behind an explicit half-open conversion.
    Persistent state changes propagate until an explicitly supplied reset.
    Shared changes invalidate all; missing dependency evidence invalidates all.
    """
    validate_plan(plan)
    converted=[]
    for change in changes:
        c=dict(change);span=c.get('frames')
        if span is not None:
            a,b=span
            integer(a,'change start');integer(b,'change end')
            if b<=a:raise ValueError('empty change')
            if c.get('persistent'):
                if c['channel'] not in {'action','prop','local_scene'}:raise ValueError('persistent state channel required')
                b=c.get('reset_frame',plan['end'])
                if type(b) is not int or b<span[1]:raise ValueError('reset precedes changed interval')
            c['frames']=[a,b-1]
        if c.get('dependency_complete') is False:c.pop('frames',None)
        converted.append(c)
    shots=[dict(id=s['id'],start=s['start'],end=s['end']-1) for s in plan['shots']]
    return render_dependencies(shots,converted)

def reserve_attempt(path, project, issue, cause, evidence, channels, limit=3):
    """Single writer, exclusive lock. Same issue across variant names shares budget.
    Crashed reservations count. A reset is a separately authorized new scope,
    never an automatic rename. Existing reservations and errors are preserved.
    """
    if not all(isinstance(x,str) and x.strip() for x in [project,issue,cause,evidence]):raise ValueError('bound issue and evidence required')
    if len(channels)!=1 or channels[0] not in {'CAMERA','ACTION','PROP','SCENE','EDITING','LIGHTING'}:raise ValueError('one attributed channel per experiment')
    if type(limit) is not int or limit<1:raise ValueError('positive budget')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);lock=Path(str(path)+'.lock')
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        history=[r for r in data if r['project']==project and r['issue']==issue]
        effective=min([limit]+[r['limit'] for r in history])
        if len(history)>=effective:raise ValueError('ITERATION_BUDGET_EXHAUSTED')
        row=dict(project=project,issue=issue,cause=cause,evidence=evidence,channels=channels,round=len(history)+1,limit=effective,status='RESERVED')
        data.append(row);tmp=Path(str(path)+'.tmp')
        tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,path)
        return row
    finally:
        os.close(fd);lock.unlink()

def file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify_reuse(media, receipt, expected_scene_fingerprint, expected_frames, expected_fps):
    """Reuse is granted only for the requested revision and exact clip identity."""
    if not Path(media).is_file():return False
    required={'scene_fingerprint':expected_scene_fingerprint,'frames':expected_frames,'fps':expected_fps,'technical':'PASS'}
    return all(receipt.get(k)==v for k,v in required.items()) and receipt.get('media_sha256')==file_sha(media)
