"""Portable CSP/1.0 structural validation; visual gates are NEVER auto-passed."""
import argparse,gzip,json,math
from pathlib import Path

GATES=('ACTION_READABILITY','CUT_CONTINUITY','TIMING_SPACING','CAMERA_CHOREOGRAPHY','VFX_LIFECYCLE','RECOVERY','SILENT_REVIEW','FILE_RENDER_QA')
PHASES=('PREPARE','COMPRESS','ACCELERATE','PEAK','CONTACT','FOLLOW_THROUGH','RECOVERY')
LIFECYCLE=('Spawn','Build','Travel','Impact','Expansion','Dissipation')
CAMERA_STATES=('Lead','Lag','Catch-up','Hold','Impact Reaction','Pull-back','Settle')

def read_package(path):
    b=Path(path).read_bytes();return json.loads(gzip.decompress(b) if str(path).endswith('.gz') else b)

def validate(p):
    e=[]
    required=('schema_version','sequence_id','layout_mode','entry_mode','timebase','shot_plan','action_beats','rhythm_map','actors','object_tracks','screen_targets','causal_links','proxy_lifecycles','camera_choreography','continuity_states','review_gates')
    for k in required:
        if k not in p:e.append('Missing '+k)
    if e:return e
    if p['schema_version']!='CSP/1.0' or p['layout_mode'] not in ('COMBAT_DYNAMIC','NARRATIVE'):e.append('Unsupported version/mode')
    if p['entry_mode'] not in ('SOURCE','TEXT'):e.append('entry_mode must be SOURCE or TEXT')
    fps=p['timebase'].get('fps',0);n=p['timebase'].get('frames',0)
    if fps<=0 or n<1:return e+['Invalid timebase']
    if p['layout_mode']=='NARRATIVE' and (not p.get('scene_asset') or p.get('actor_assets') or p.get('actor_pose_tracks')):e.append('Narrative CSP requires a baked scene_asset; fresh Narrative actor lowering unsupported')
    duration=n/fps
    def window(w,label):
        if not isinstance(w,list) or len(w)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in w) or not 0<=w[0]<=w[1]<=duration+1e-5:e.append('Invalid seconds interval '+label)
    cursor=1;shot_ids=set();camera_ids=set()
    for s in p['shot_plan']:
        if s['id'] in shot_ids:e.append('Duplicate shot '+s['id'])
        shot_ids.add(s['id']);camera_ids.add(s['camera_id'])
        if s['first_frame']!=cursor or s['end_frame_exclusive']<=cursor:e.append('Gap/overlap in shot '+s['id'])
        cursor=s['end_frame_exclusive']
    if cursor!=n+1:e.append('Shots do not cover full timeline')
    def tracks_validate(tracks):
        for obj,samples in tracks.items():
            fs=[s['frame'] for s in samples]
            if not fs or fs!=sorted(set(fs)) or fs[0]!=1 or fs[-1]!=n:e.append('Track bounds/order '+obj)
            for s in samples:
                if not 1<=s['frame']<=n:e.append('Track out of range '+obj)
                def finite(v):
                    if isinstance(v,float):return math.isfinite(v)
                    if isinstance(v,dict):return all(finite(x) for x in v.values())
                    if isinstance(v,list):return all(finite(x) for x in v)
                    return True
                if not finite(s['state']):e.append('Non-finite track '+obj)
    tracks_validate(p['object_tracks']);tracks_validate(p.get('actor_pose_tracks',{}))
    event_ids=set();beats={}
    for b in p['action_beats']:
        if b['event_id'] in event_ids:e.append('Duplicate event ID '+b['event_id'])
        event_ids.add(b['event_id']);beats[b['event_id']]=b;window(b['interval_s'],b['event_id'])
        for phase in PHASES:
            q=b.get('phases',{}).get(phase)
            if not q:e.append('Missing phase '+b['event_id']+'/'+phase);continue
            if q.get('status')=='NA':
                if not q.get('reason'):e.append('NA needs reason '+phase)
            elif q.get('status')=='APPLIES':window(q.get('interval_s'),phase)
            else:e.append('Invalid phase status '+phase)
        if not b.get('breakdowns'):e.append('Missing breakdown samples '+b['event_id'])
    for r in p['rhythm_map']:window(r['interval_s'],'rhythm')
    adjacency={x:[] for x in event_ids}
    for c in p['causal_links']:
        if c['cause_event'] not in event_ids or c['reaction_event'] not in event_ids:e.append('Dangling causal event');continue
        adjacency[c['cause_event']].append(c['reaction_event'])
        if c['response_s']<c['trigger_s']-c.get('anticipation_s',0):e.append('Reaction before trigger without anticipation')
        if not c.get('direction_rule') or not c.get('strength_rule'):e.append('Causal force contract missing')
    def visit(k,active,done):
        if k in active:e.append('Causal cycle '+k);return
        if k in done:return
        active.add(k)
        for child in adjacency[k]:visit(child,active,done)
        active.remove(k);done.add(k)
    done=set()
    for k in adjacency:visit(k,set(),done)
    for proxy in p['proxy_lifecycles']:
        if proxy['event_id'] not in event_ids:e.append('Proxy event missing '+proxy['id'])
        for phase in LIFECYCLE:
            q=proxy.get('stages',{}).get(phase)
            if not q:e.append('Lifecycle missing '+proxy['id']+'/'+phase)
            elif q.get('status')=='NA':
                if not q.get('reason'):e.append('Lifecycle NA needs reason')
            elif q.get('status')=='APPLIES':window(q.get('interval_s'),'proxy '+phase)
            else:e.append('Invalid lifecycle status')
        if not proxy.get('end_state'):e.append('Proxy end state missing')
    targetshots={s['shot_id'] for s in p['screen_targets']}
    if targetshots!=shot_ids:e.append('Screen target coverage mismatch')
    for c in p['camera_choreography']:
        if c['shot_id'] not in shot_ids:e.append('Unknown camera shot')
        for q in c['states']:
            if q['state'] not in CAMERA_STATES:e.append('Unknown camera state')
            window(q['interval_s'],'camera')
            if not all(k in q for k in ('trigger','delay_s','entry_speed','exit_speed','framing_goal')):e.append('Incomplete camera dynamics')
    cuts={s['first_frame'] for s in p['shot_plan'][1:]}
    if {c['cut_frame'] for c in p['continuity_states']}!=cuts:e.append('Continuity cut coverage mismatch')
    for c in p['continuity_states']:
        if not set(c['active_event_ids']).issubset(event_ids):e.append('Unknown continuity event')
        if not all(k in c for k in ('before_frame','after_frame','state_evidence','phase_state','ownership')):e.append('Incomplete continuity state')
    for g in GATES:
        r=p['review_gates'].get(g)
        if not r or r.get('status') not in ('PASS','FAIL','NOT_REVIEWED','NA'):e.append('Missing/invalid gate '+g)
        elif r['status'] in ('PASS','FAIL','NA') and not r.get('evidence'):e.append('Gate needs evidence '+g)
    if any(any('prop_control' in r['state'] for r in rows) for rows in p['object_tracks'].values()):
        from prop_control import validate_control
        e.extend(validate_control(p))
    if any(any('support_contact' in r['state'] for r in rows) for rows in p['object_tracks'].values()):
        from support_contact import structural_errors
        e.extend(structural_errors(p))
    for beat in p.get('action_beats', []):
        if 'contact_readability' in beat:
            from contact_readability import structural_errors
            e.extend(structural_errors(p, beat['contact_readability']))
        if 'momentum_transfer' in beat:
            from momentum_transfer import structural_errors
            e.extend(structural_errors(p, beat['momentum_transfer']))
    return e

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('package');args=a.parse_args();errors=validate(read_package(args.package))
    print(json.dumps({'status':'FAIL' if errors else 'STRUCTURAL_PASS','errors':errors},ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
