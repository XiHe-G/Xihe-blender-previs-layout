"""Eight bounded semantic measurement families; diagnostics only, no repair API."""
import argparse,html,json,math
from collections import Counter
from pathlib import Path
from s2_common import digest,read,write,schema_check
from combat_sequence_package import read_package
from plan_to_observables import compile_plan
from motion_analysis import distance,norm,mean,direction_summary,recovery_summary,quaternion_angle

REGIONS={'LEFT':[0,0,.45,1],'RIGHT':[.55,0,1,1],'CENTER':[.35,.25,.65,.75],'UPPER':[0,.55,1,1],'LOWER':[0,0,1,.45]}

from checker_calibration import camera_hold,qualify,evidence_gap

def measured(o,rows):
    """Return (status, code, actual, evidence rows). Unknown data never passes."""
    typ=o['type'];state=o['expected_state'] or {};tol=o['tolerance'];subjects=o['subjects'];subject=subjects[0]
    samples=[r['entities'].get(subject) for r in rows]
    if not rows or any(s is None for s in samples):return 'NOT_REVIEWED','SUBJECT_TRACE_UNAVAILABLE',{},[]
    if any(not s or not s['exists'] for s in samples):return 'FAIL','SUBJECT_MISSING',{},[r for r,s in zip(rows,samples) if not s or not s['exists']]
    if state.get('applicable') is False:return 'NA','EXPLICIT_NOT_APPLICABLE',{},[]
    if typ in ('SHOT_SIZE','SCREEN_POSITION','SCREEN_DIRECTION'):
        unavailable=[r for r,s in zip(rows,samples) if s['screen_center'] is None or s['screen_bounds']['clipped_bounds'] is None or not s['proxy_state']['render_enabled']]
        if unavailable:return ('NOT_REVIEWED' if typ=='SCREEN_DIRECTION' else 'FAIL'),'SUBJECT_NOT_ON_SCREEN',{},unavailable
        hidden=[r for r,s in zip(rows,samples) if s['occlusion_ratio']==1.]
        if hidden and typ not in ('SHOT_SIZE','SCREEN_DIRECTION'):return 'FAIL','SUBJECT_FULLY_OCCLUDED_ESTIMATE',{},hidden
        uncertain=[r for r,s in zip(rows,samples) if s['occlusion_ratio'] is None]
        if uncertain and typ not in ('SHOT_SIZE','SCREEN_DIRECTION'):return 'NOT_REVIEWED','OCCLUSION_SAMPLES_UNAVAILABLE',{},uncertain
        visibility_fail=[r for r,s in zip(rows,samples) if s['screen_bounds']['visible_fraction_estimate']<state.get('min_visible_fraction',0) or state.get('max_occlusion') is not None and (s['occlusion_ratio'] is None or s['occlusion_ratio']>state['max_occlusion'])]
        if visibility_fail:return 'FAIL','VISIBILITY_OR_OCCLUSION_ESTIMATE_MISMATCH',dict(basis='ESTIMATED'),visibility_fail
    if typ=='SHOT_SIZE':
        bounds=o['expected_range'];axis=state.get('axis','height');key='screen_height_ratio' if axis=='height' else 'screen_width_ratio'
        if bounds is None:return 'NOT_REVIEWED','NO_NUMERIC_SIZE_REQUIREMENT',{},[]
        values=[s[key] for s in samples];bad=[r for r,v in zip(rows,values) if not bounds[0]-tol<=v<=bounds[1]+tol]
        if not bad and hidden:return 'FAIL','SUBJECT_FULLY_OCCLUDED_ESTIMATE',{},hidden
        if not bad and uncertain:return 'NOT_REVIEWED','OCCLUSION_SAMPLES_UNAVAILABLE',{},uncertain
        return ('FAIL' if bad else 'PASS'),'SHOT_SIZE_MISMATCH' if bad else 'SHOT_SIZE_MATCH',dict(min=min(values),max=max(values),delta=[min(values)-bounds[0],max(values)-bounds[1]],axis=axis,basis='PROJECTED_RECT_NOT_VISIBLE_PIXELS'),bad or rows[:1]
    if typ=='SCREEN_POSITION':
        region=o['expected_range'] or REGIONS.get(state.get('region'))
        if not region:return 'NOT_REVIEWED','UNSUPPORTED_SCREEN_REGION',{},[]
        coords=[s['screen_center'] for s in samples];bad=[r for r,(x,y) in zip(rows,coords) if not region[0]-tol<=x<=region[2]+tol or not region[1]-tol<=y<=region[3]+tol]
        return ('FAIL' if bad else 'PASS'),'SCREEN_POSITION_MISMATCH' if bad else 'SCREEN_POSITION_MATCH',dict(x_range=[min(x[0] for x in coords),max(x[0] for x in coords)],y_range=[min(x[1] for x in coords),max(x[1] for x in coords)]),bad or rows[:1]
    if typ=='SCREEN_DIRECTION':
        if len({r['shot_id'] for r in rows})>1:return 'NOT_REVIEWED','SCREEN_DIRECTION_CROSSES_CUT',{},[]
        d=direction_summary([s['screen_center'] for s in samples]);d['DIRECTION_BASIS']='PROJECTED_CENTER';x,y=d['delta'];minimum=state.get('min_displacement',.02)
        d['projection_evidence']='PARTIAL' if any(not (0<=s['screen_center'][0]<=1 and 0<=s['screen_center'][1]<=1) for s in samples) else 'ENOUGH'
        d['min_visible_fraction_estimate']=min(s['screen_bounds']['visible_fraction_estimate'] for s in samples)
        wanted=state.get('direction');region=state.get('region_range') or o.get('expected_range');tests={'LEFT_TO_RIGHT':x>=minimum and abs(y)<=abs(x)*state.get('cross_axis_ratio',1),'RIGHT_TO_LEFT':x<=-minimum and abs(y)<=abs(x)*state.get('cross_axis_ratio',1),'UP':y>=minimum and abs(x)<=abs(y)*state.get('cross_axis_ratio',1),'DOWN':y<=-minimum and abs(x)<=abs(y)*state.get('cross_axis_ratio',1),'DIAGONAL':abs(x)>=minimum and abs(y)>=minimum,'HOLD_REGION':bool(region) and all(region[0]-tol<=u[0]<=region[2]+tol and region[1]-tol<=u[1]<=region[3]+tol for u in [s['screen_center'] for s in samples])}
        if wanted not in tests:return 'NOT_REVIEWED','UNSUPPORTED_DIRECTION',d,[]
        ok=tests[wanted] if wanted=='HOLD_REGION' else tests[wanted] and d['coherence']>=state.get('min_coherence',.5)
        return ('PASS' if ok else 'FAIL'),'SCREEN_DIRECTION_MATCH' if ok else 'SCREEN_DIRECTION_MISMATCH',d,[rows[0],rows[-1]]
    if typ in ('CONTACT','NEAR_MISS'):
        if len(subjects)!=2:return 'NOT_REVIEWED','PAIR_REQUIRED',{},[]
        key='|'.join(subjects);pairs=[r['pairwise_distance'].get(key) or r['pairwise_distance'].get('|'.join(reversed(subjects))) for r in rows]
        if any(p is None or p.get('contact') is None or p.get('geometry_clearance') is None for p in pairs):return 'NOT_REVIEWED','GEOMETRY_UNAVAILABLE',{},[]
        active=[(r,p) for r,p in zip(rows,pairs) if p['both_render_enabled']]
        if not active:return 'FAIL','PAIR_NOT_ACTIVE',{},rows[:1]
        r,p=min(active,key=lambda rp:rp[1]['geometry_clearance']);contacts=[row for row,q in active if q['contact'] or q['geometry_clearance']<=state.get('contact_epsilon',.001)]
        if typ=='CONTACT':ok=bool(contacts) or p['geometry_clearance']<=state.get('max_contact_distance',.01)+tol;category='CONTACT' if ok else 'SAFE_PASS'
        else:
            geometry_ok=not contacts and state.get('min_clearance',0)<p['geometry_clearance']<=state['near_miss_max']+tol
            screen_distance=p.get('screen_bounds_gap_estimate') if state.get('screen_metric')=='bounds_gap' else p['screen_center_distance']
            screen_ok=screen_distance is not None and screen_distance<=state['max_screen_distance']+tol
            visible=all(r['entities'][s]['screen_bounds']['clipped_bounds'] is not None and r['entities'][s]['occlusion_ratio'] is not None and r['entities'][s]['occlusion_ratio']<=state.get('max_occlusion',1.) for s in subjects)
            ok=geometry_ok and screen_ok and visible;category='CONTACT' if contacts else 'NEAR_MISS' if ok else 'SAFE_PASS'
        actual=dict(closest_time=r['time'],closest_frame=r['frame'],closest_distance=p['geometry_clearance'],screen_center_distance=p['screen_center_distance'],screen_bounds_gap_estimate=p.get('screen_bounds_gap_estimate'),classification=category,geometry_method=p['method'])
        return ('PASS' if ok else 'FAIL'),typ+'_MATCH' if ok else typ+'_MISMATCH',actual,contacts or [r]
    if typ=='PROJECTILE_CONTINUITY':
        positions=[s['entity_world_state']['position'] for s in samples];tokens=[s['identity_token'] for s in samples];violations=[];unknown_owner=False
        unknown_identity=bool(state.get('expected_entity_id')) and any(s.get('identity_evidence')!='NATIVE_OBJECT_PROPERTY' for s in samples)
        for i in range(1,len(rows)):
            step=distance(positions[i],positions[i-1]);dt=rows[i]['time']-rows[i-1]['time']
            if tokens[i]!=tokens[0]:violations.append((rows[i],'IDENTITY_RECREATED'))
            if step>state['max_step']+tol or step/dt>state.get('max_speed',1e12):violations.append((rows[i],'PROJECTILE_TELEPORT'))
        for r,s in zip(rows,samples):
            if state.get('expected_entity_id') and s.get('identity_evidence')=='NATIVE_OBJECT_PROPERTY' and s['entity_id']!=state['expected_entity_id']:violations.append((r,'ENTITY_ID_MISMATCH'))
            expected_visible=any(a<=r['time']<b for a,b in state.get('visibility_intervals',[]))
            if expected_visible and not s['proxy_state']['render_enabled']:violations.append((r,'UNEXPLAINED_DISAPPEARANCE'))
            if state.get('expected_owner') is not None:
                own=s['ownership_state'];owner=own['native_owner']
                if owner is None:unknown_owner=True
                elif owner!=state['expected_owner']:violations.append((r,'OWNER_MISMATCH'))
        release=state.get('release_time');relative=[(r,s['ownership_state']['owner_relative']) for r,s in zip(rows,samples) if release is not None and r['time']>=release and s['ownership_state']['owner_relative'] is not None]
        detached=None
        if release is not None:
            if len(relative)<2:
                if not violations:return 'NOT_REVIEWED','RELEASE_RELATIVE_TRACE_UNAVAILABLE',{},[]
            else:
                detached=max(distance(relative[0][1],x[1]) for x in relative)
                if detached<state.get('min_owner_relative_travel',.05):violations.append((relative[-1][0],'PROJECTILE_STILL_ATTACHED'))
        # Native owner-local motion catches rigid following even when the owner rotates.
        if state.get('detachment_window'):
            a,b=state['detachment_window'];rel=[(r,s['ownership_state'].get('owner_local_position')) for r,s in zip(rows,samples) if a<=r['time']<b]
            complete=len(rel)>=2 and all(v is not None for r,v in rel)
            if complete:
                detached=max(distance(rel[0][1],v) for r,v in rel)
                if detached<state.get('min_owner_relative_travel',.05):violations.append((rel[-1][0],'PROJECTILE_RELEASE_DETACHMENT'))
            elif not violations:return 'NOT_REVIEWED','DETACHMENT_EVIDENCE_UNAVAILABLE',{},[]
        if state.get('terminal_state')=='VISIBLE' and not samples[-1]['proxy_state']['render_enabled']:violations.append((rows[-1],'TERMINAL_STATE_MISMATCH'))
        if state.get('terminal_state')=='HIDDEN' and samples[-1]['proxy_state']['render_enabled']:violations.append((rows[-1],'TERMINAL_STATE_MISMATCH'))
        actual=dict(release_time=release,release_time_basis='PLAN_REGISTERED_WITH_ACTUAL_RELATIVE_MOTION_CHECK',owner_relative_travel=detached,
            max_step=max([distance(a,b) for a,b in zip(positions,positions[1:])] or [0]),native_identity_tokens=tokens[0],
            visibility_intervals_observed=visible_intervals(rows,samples),terminal_state='VISIBLE' if samples[-1]['proxy_state']['render_enabled'] else 'HIDDEN',violations=list(dict.fromkeys(v for r,v in violations)),violation_counts=dict(Counter(v for r,v in violations)),owner_evidence=sorted({s['ownership_state']['authority'] for s in samples}),
            trajectory_status='FAIL' if any(v=='PROJECTILE_TELEPORT' for r,v in violations) else 'PASS',ownership_status='NOT_REVIEWED' if unknown_owner else 'FAIL' if any(v=='OWNER_MISMATCH' for r,v in violations) else 'PASS' if state.get('expected_owner') else 'NA')
        actual['identity_evidence']=sorted({s.get('identity_evidence','UNKNOWN') for s in samples})
        return ('FAIL' if violations else 'NOT_REVIEWED' if unknown_owner or unknown_identity else 'PASS'),'PROJECTILE_CONTINUITY_MISMATCH' if violations else 'OWNER_ACTUAL_NOT_REVIEWED' if unknown_owner else 'ENTITY_ACTUAL_NOT_REVIEWED' if unknown_identity else 'PROJECTILE_CONTINUITY_MATCH',actual,[r for r,v in violations] or rows[-1:]
    if typ=='CAMERA_STATE':
        if o.get('behavior_profile') in ('LOCKED_HOLD','COMPOSITION_HOLD','SOFT_HOLD'):return camera_hold(o,rows)
        if len({r['camera_transform']['object'] for r in rows})>1:return 'NOT_REVIEWED','CAMERA_STATE_CROSSES_CUT',{},[]
        cams=[r['camera_transform'] for r in rows];p=[c['position'] for c in cams];travel=sum(distance(a,b) for a,b in zip(p,p[1:]));angle=max(quaternion_angle(cams[0]['quaternion'],c['quaternion']) for c in cams)
        lens=max(r['camera_lens'] for r in rows)-min(r['camera_lens'] for r in rows);dist=[distance(c['position'],s['entity_world_state']['position']) for c,s in zip(cams,samples)];mode=state.get('mode')
        actual=dict(path_translation=travel,max_rotation_deg=angle,max_rotation_frame=rows[max(range(len(cams)),key=lambda i:quaternion_angle(cams[0]['quaternion'],cams[i]['quaternion']))]['frame'],lens_range=lens,subject_distance_start=dist[0],subject_distance_end=dist[-1])
        if mode=='HOLD':ok=travel<=state['max_translation']+tol and angle<=state['max_rotation_deg']+tol and lens<=state.get('max_lens_delta',.01)+tol
        elif mode in ('PUSH','PULL'):
            sign=-1 if mode=='PUSH' else 1;frac=mean([1 if (b-a)*sign>=-tol else 0 for a,b in zip(dist,dist[1:])]);actual['monotonic_fraction']=frac
            ok=travel>=state.get('min_translation',.01) and (dist[-1]-dist[0])*sign>=state.get('min_distance_change',.05) and frac>=state.get('min_monotonic_fraction',.7)
        elif mode=='FOLLOW':
            centers=[s['screen_center'] for s in samples]
            if any(c is None for c in centers):return 'NOT_REVIEWED','FOLLOW_PROJECTION_UNAVAILABLE',actual,[]
            drift=max(distance(c,centers[0]) for c in centers);actual['screen_drift']=drift
            ok=travel>=state.get('min_translation',.01) and drift<=state['max_screen_drift']+tol and max(dist)-min(dist)<=state['max_distance_variation']+tol
        elif mode in ('PAN','REFRAME'):ok=angle>=state['min_rotation_deg']-tol and travel<=state.get('max_translation',1e12)+tol
        elif mode in ('LAG','CATCH_UP'):
            centers=[s['screen_center'] for s in samples]
            if any(c is None for c in centers):return 'NOT_REVIEWED','CAMERA_TREND_UNAVAILABLE',actual,[]
            errors=[distance(c,state['target_screen']) for c in centers];actual['screen_error_start_end']=[errors[0],errors[-1]]
            change=errors[-1]-errors[0];ok=(change if mode=='LAG' else -change)>=state['min_error_change']-tol and travel>=state.get('min_translation',.01)
        else:return 'NOT_REVIEWED','UNSUPPORTED_CAMERA_STATE',actual,[]
        evidence=[rows[0],rows[-1]]
        if mode=='HOLD' and not ok:
            evidence=[];accumulated=0;seen_lens=[]
            for i,r in enumerate(rows):
                if i:accumulated+=distance(p[i],p[i-1])
                seen_lens.append(r['camera_lens'])
                if accumulated>state['max_translation']+tol or quaternion_angle(cams[0]['quaternion'],cams[i]['quaternion'])>state['max_rotation_deg']+tol or max(seen_lens)-min(seen_lens)>state.get('max_lens_delta',.01)+tol:evidence.append(r)
        return ('PASS' if ok else 'FAIL'),'CAMERA_STATE_MATCH' if ok else 'CAMERA_STATE_MISMATCH',actual,evidence
    if typ in ('ACTION_PHASE','RECOVERY'):
        available=[(r,s) for r,s in zip(rows,samples) if s['speed_world'] is not None]
        if len(available)<3:return 'NOT_REVIEWED','INSUFFICIENT_MOTION_SAMPLES',{},[]
        rr,ss=zip(*available);speeds=[s['speed_world'] for s in ss];phase=state.get('phase');k=max(1,len(speeds)//3)
        actual=dict(initial_speed=mean(speeds[:k]),final_speed=mean(speeds[-k:]),peak_speed=max(speeds));peak=rr[speeds.index(max(speeds))];actual.update(peak_time=peak['time'],peak_frame=peak['frame'])
        positions=[s['entity_world_state']['position'] for s in ss]
        vectors=[[b[i]-a[i] for i in range(3)] for a,b in zip(positions,positions[1:])];moving=[v for v in vectors if norm(v)>1e-8]
        actual['direction_change_deg']=math.degrees(math.acos(max(-1,min(1,sum(a*b for a,b in zip(moving[0],moving[-1]))/(norm(moving[0])*norm(moving[-1])))))) if len(moving)>1 else None
        actual['max_speed_change']=max(abs(b-a) for a,b in zip(speeds,speeds[1:]))
        if typ=='RECOVERY':
            actual.update(recovery_summary([s['entity_world_state']['position'] for s in ss],speeds,[s['entity_world_state']['tilt_deg'] for s in ss]))
            ok=actual['initial_speed']>=state.get('min_initial_speed',.01) and actual['final_speed']<=actual['initial_speed']*state['max_final_speed_ratio']+tol and actual['max_step']<=state['max_step']+tol and actual['final_displacement']<=state['max_final_displacement']+tol
            if state.get('require_upright_trend'):ok=ok and actual['final_tilt']<=actual['initial_tilt']+state.get('tilt_tolerance_deg',2)
            if 'max_speed_change' in state:ok=ok and actual['max_speed_change']<=state['max_speed_change']+tol
            return ('PASS' if ok else 'FAIL'),'RECOVERY_MATCH' if ok else 'RECOVERY_MISSING',actual,[rr[0],peak,rr[-1]]
        if phase=='PEAK':
            if max(speeds)-min(speeds)<state.get('min_peak_prominence',.01):return 'NOT_REVIEWED','NO_DISTINCT_SPEED_PEAK',actual,[peak]
            ok=any(state['peak_window'][0]-tol<=r['time']<state['peak_window'][1]+tol for r,v in zip(rr,speeds) if abs(v-max(speeds))<1e-8) and max(speeds)>=state.get('min_speed',.01)
        elif phase in ('ANTICIPATION','ACCELERATION'):ok=actual['final_speed']>=actual['initial_speed']+state.get('min_speed_increase',.05)-tol
        elif phase=='FOLLOW_THROUGH':
            ok=actual['final_speed']<=actual['initial_speed']+state.get('max_speed_increase',0)+tol and distance(ss[0]['entity_world_state']['position'],ss[-1]['entity_world_state']['position'])>=state.get('min_travel',.01)
            if 'min_direction_change_deg' in state:ok=ok and actual['direction_change_deg'] is not None and actual['direction_change_deg']>=state['min_direction_change_deg']-tol
        elif phase in ('CONTACT','NEAR_MISS'):
            oo=dict(o,type=phase);return measured(oo,rows)
        else:return 'NOT_REVIEWED','UNSUPPORTED_ACTION_PHASE',actual,[]
        return ('PASS' if ok else 'FAIL'),'ACTION_PHASE_MATCH' if ok else 'ACTION_PHASE_MISMATCH',actual,[peak]
    return 'NOT_REVIEWED','UNSUPPORTED_OBSERVABLE',{},[]

def visible_intervals(rows,samples):
    result=[];start=None;dt=rows[1]['time']-rows[0]['time'] if len(rows)>1 else 0
    for r,s in zip(rows,samples):
        if s['proxy_state']['render_enabled'] and start is None:start=r['time']
        if not s['proxy_state']['render_enabled'] and start is not None:result.append([start,r['time']]);start=None
    if start is not None:result.append([start,rows[-1]['time']+dt])
    return result

def check(graph,expected,trace,binding):
    from jsonschema import Draft202012Validator
    errors=list(Draft202012Validator(read(Path(__file__).resolve().parents[1]/'runtime/actual-trace.schema.json')).iter_errors(trace))
    if errors:raise ValueError('ACTUAL_TRACE_SCHEMA_ERROR: '+errors[0].message)
    canonical=compile_plan(graph,binding)
    if digest(expected)!=digest(canonical):raise ValueError('STALE_OR_FORGED_EXPECTED_OBSERVABLES')
    if trace['schema_version']!='ACTUAL-TRACE/1.0' or trace['graph_id']!=graph['graph_id'] or trace['measurement_binding_sha256']!=digest(binding):raise ValueError('STALE_ACTUAL_TRACE_BINDING')
    if trace['timebase']!=graph['timebase']:raise ValueError('TRACE_TIMEBASE_MISMATCH')
    results=[];fps=graph['timebase']['fps'];constraints={c['constraint_id']:c for c in graph['constraints']}
    for o in expected['observables']:
        lo,hi=o['time_window'];rows=[r for r in trace['frames'] if lo-1e-8<=r['time']<hi-1e-8 and (o['shot_id'] is None or o['shot_id']==r['shot_id'])]
        wanted=[f for f in range(1,math.ceil(graph['timebase']['duration']*fps)+1) if lo-1e-8<=(f-1)/fps<hi-1e-8]
        if [r['frame'] for r in rows]!=wanted or any(abs(r['time']-(r['frame']-1)/fps)>1e-7 for r in rows):status,code,actual,evidence='NOT_REVIEWED','TRACE_COVERAGE_GAP',{},[]
        elif len(rows)<2:status,code,actual,evidence='NOT_REVIEWED','INSUFFICIENT_SAMPLES',{},[]
        else:
            try:
                gap=evidence_gap(o,rows)
                status,code,actual,evidence=('NOT_REVIEWED',gap,{},[]) if gap else measured(o,rows)
            except (KeyError,TypeError,IndexError) as error:status,code,actual,evidence='NOT_REVIEWED','MISSING_REQUIRED_MEASUREMENT_OR_THRESHOLD',{'reason':str(error)},[]
        measurement_status=status
        status,sufficiency=qualify(o,status,code,actual,evidence)
        if status=='FAIL' and o['severity'] in ('MINOR','INFO'):status='WARNING'
        results.append(dict(observable_id=o['observable_id'],source_author_id=o['source_author_id'],related_events=[x for x in constraints.get(o['source_author_id'],{}).get('targets',[]) if x.startswith('EVT_')],shot_id=o['shot_id'],type=o['type'],subjects=o['subjects'],severity=o['severity'],status=status,code=code,
            measurement_status=measurement_status,evidence_sufficiency=sufficiency,plan=o,actual=actual,time_window=o['time_window'],evidence=[dict(frame=r['frame'],time=r['time'],shot_id=r['shot_id'],trace_pointer='/frames/'+str(trace['frames'].index(r))) for r in evidence],diagnostic_only=True))
    for i,u in enumerate(expected['not_reviewed']):results.append(dict(observable_id='UNREVIEWED_'+str(i),source_author_id=u['source_author_id'],shot_id=None,type='UNSUPPORTED_INTENT',evidence_sufficiency=dict(level='INSUFFICIENT',strong_evidence=False,reasons=[u['reason']]),subjects=[],severity='INFO',status='NOT_REVIEWED',code=u['reason'],plan=u['plan'],actual=None,time_window=None,evidence=[],diagnostic_only=True))
    counts=dict(Counter(r['status'] for r in results));overall='FAIL' if counts.get('FAIL') else 'WARNING' if counts.get('WARNING') else 'NOT_REVIEWED' if counts.get('NOT_REVIEWED') else 'PASS' if counts.get('PASS') else 'NA'
    return dict(schema_version='PLAN-ACTUAL-REPORT/1.0',graph_id=graph['graph_id'],status=overall,counts=counts,graph_sha256=digest(graph),expected_sha256=digest(expected),trace_sha256=digest(trace),source_blend=trace['source_blend'],results=results,automatic_repair=False,artistic_review='NOT_REVIEWED')

def deliver(report,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);write(out/'PLAN-ACTUAL-REPORT.json',report)
    suggestions=[dict(problem=r['code'],source_author_id=r['source_author_id'],affected_object=r['subjects'],time_range=r['time_window'],likely_channel={'CAMERA_STATE':'camera_transform','SHOT_SIZE':'camera_framing','SCREEN_POSITION':'world_or_camera_transform'}.get(r['type'],'motion_or_proxy_execution'),suggested_scope=dict(shot_id=r['shot_id'],evidence=r['evidence']),action='HUMAN_DIAGNOSIS_ONLY; no Changeset or Execution Patch generated') for r in report['results'] if r['status'] in ('FAIL','WARNING')]
    write(out/'REPAIR-SUGGESTION.json',dict(schema_version='REPAIR-SUGGESTION/1.0',automatic_execution=False,suggestions=suggestions))
    cards=[]
    for r in report['results']:
        attrs=html.escape(' '.join(str(r[k]) for k in ['shot_id','source_author_id','severity','status','type'])+' '+' '.join(r.get('related_events',[])))
        detail=html.escape(json.dumps({k:r[k] for k in ['plan','actual','time_window','subjects','evidence','evidence_sufficiency']},ensure_ascii=False,indent=2))
        cards.append(f'<article data-filter="{attrs}"><h3 class="{r["status"]}">{html.escape(r["status"]+" · "+r["code"])}</h3><p>{attrs}</p><p>{html.escape(str(r.get('evidence_sufficiency',{})))}</p><details><summary>PLAN / ACTUAL / TIME / OBJECTS / EVIDENCE</summary><pre>{detail}</pre></details></article>')
    page='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>Plan → Actual</title><style>*{box-sizing:border-box}body{overflow-wrap:anywhere;font:16px system-ui;max-width:1120px;margin:40px auto;background:#101820;color:#e8edf1;padding:16px}h1{font-size:32px}.meta{color:#b7c9d3}article{padding:16px;background:#1d2a35;margin:12px 0;border-radius:8px}.FAIL{color:#ff9c9c}.PASS{color:#94e2b1}.WARNING{color:#ffd68a}.NOT_REVIEWED{color:#b5c9df}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px monospace}input{padding:12px;width:90%;font:inherit}summary{cursor:pointer}h3{margin:0 0 8px}</style><h1>PLAN → ACTUAL · S3.5</h1>'''
    page+=f'<p>{html.escape(report["graph_id"])} · {html.escape(report["status"])} · {html.escape(str(report["counts"]))}</p><p class="meta">只读诊断 · 遮挡/投影为估计 · 不替代正常速度人工审片 · 无自动修复</p><p class="meta">Source SHA-256: {report["source_blend"]["sha256"]}</p><input id="filter" placeholder="筛选 SHOT / EVT / CST / severity / result">'+''.join(cards)
    page+="<script>document.getElementById('filter').addEventListener('input',e=>{const q=e.target.value.toUpperCase();document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.filter.toUpperCase().includes(q))})</script></html>"
    (out/'PLAN-ACTUAL-REPORT.html').write_text(page,encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['graph','expected','trace','binding','output']:p.add_argument('--'+name,required=True)
    a=p.parse_args();r=check(read(a.graph),read(a.expected),read_package(a.trace),read(a.binding));deliver(r,a.output);print(r['status'],r['counts'])
