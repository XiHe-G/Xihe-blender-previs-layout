"""Lowering protocol, evidence, pre-runtime protection, and explicit constraint checks."""
import json,copy
from pathlib import Path
from primitive_sampler import sha,unit,norm,sub,project,frame_to_time
from primitive_channel_registry import channels
from plan_actual_checker import REGIONS
STATUSES=('READY','NEEDS_AUTHOR_INPUT','AMBIGUOUS','UNSUPPORTED','BLOCKED_BY_CONSTRAINT','BLOCKED_BY_OVERRIDE','BLOCKED_BY_UPSTREAM')
ROOT=Path(__file__).resolve().parents[1]
class StopLowering(Exception):
    def __init__(self,status,code,missing=None,choices=None):self.status=status;self.code=code;self.missing=missing or [];self.choices=choices or [];super().__init__(code)
def parse_evidence(evidence):
    if evidence.get('status')=='UNKNOWN' or evidence.get('value') is None:return {},'LOW'
    try:data=json.loads(evidence['value'])
    except (ValueError,TypeError):return {},'LOW'
    if not isinstance(data,dict):return {},'LOW'
    if any(k.startswith('primitive') or k in ('world_samples','camera_samples','keyframes') for k in data):raise StopLowering('UNSUPPORTED','EXECUTION_DATA_IS_NOT_AUTHOR_INTENT')
    return data,'LOW' if evidence['status']=='INFERRED' else 'HIGH'
def plan(graph,id,typ,provenance):
    return dict(lowering_version='EVENT-LOWERING-PLAN/1.0',plan_id='LP_'+id,graph_id=graph['graph_id'],event_id=id,event_type=typ,lowering_status='NEEDS_AUTHOR_INPUT',input_evidence=copy.deepcopy(provenance),required_inputs=[],resolved_inputs={},derived_inputs={},primitive_sequence=[],channel_plan=[],entry_state=None,exit_requirements={},continuity_contract={'C0_REQUIRED':True,'C1_REQUIREMENT':'REQUIRED','C2_POLICY':'RECORD'},dependencies=[],constraints=[],confidence='HIGH',provenance={'graph_sha256':sha(graph),'registry_version':'S52/1.0'},warnings=[],validation_status='NOT_RUN')
def record(p,key,value,source,origin,method='DIRECT_VALUE',confidence='HIGH'):
    if confidence=='MEDIUM' and p['confidence']=='HIGH':p['confidence']='MEDIUM'
    d={'value':copy.deepcopy(value),'source':source,'derived_from':origin,'method':method,'confidence':confidence};p['resolved_inputs'][key]=d
    if source in ('DERIVED','PREVIOUS_EXIT_STATE','DEPENDENCY','TECHNICAL_DEFAULT'):p['derived_inputs'][key]=copy.deepcopy(d)
    return value
def need(p,key):
    p['required_inputs'].append(key);raise StopLowering('NEEDS_AUTHOR_INPUT','MISSING_'+key.upper(),[key])
def request(p,stop):
    p['lowering_status']=stop.status;p['validation_status']='FAIL' if stop.code in ('STATE_CONFLICT','LOWERING_VALIDATION_FAIL') else 'NOT_RUN';p['warnings'].append(stop.code)
    return {'request_version':'AUTHOR-INPUT-REQUEST/1.0','plan_id':p['plan_id'],'graph_id':p['graph_id'],'event_id':p['event_id'],'status':stop.status,'missing':stop.missing,'known':copy.deepcopy(p['resolved_inputs']),'valid_unresolved_choices':stop.choices,'question':'请明确 '+', '.join(stop.missing or [stop.code])+'；未批准前不执行。','automatic_dialogue':False,'automatic_execution':False,'provenance':copy.deepcopy(p['provenance'])}
def constraints_for(graph,event_id,actor,window,shot_id=None):
    ids={event_id,actor,shot_id}
    return [c for c in graph['constraints'] if c['scope']=='SEQUENCE' or ids&set(c['targets']) or c['scope']=='SHOT' and any(s['shot_id'] in c['targets'] and max(s['time_range'][0],window[0])<min(s['time_range'][1],window[1]) for s in graph['shot_intents'])]
def constraint_inputs(cs,values,p):
    out=dict(values)
    for c in cs:
        if c['provenance']['status'] in ('UNKNOWN','INFERRED'):raise StopLowering('NEEDS_AUTHOR_INPUT','UNCONFIRMED_CONSTRAINT',[c['constraint_id']])
        try:rules=json.loads(c['requirement'])
        except ValueError:raise StopLowering('NEEDS_AUTHOR_INPUT','UNPARSED_CONSTRAINT',[c['constraint_id']])
        if not isinstance(rules,dict) or set(rules)-{'inputs','allowed_dodge_directions','world_bounds','max_speed','screen_region','subject','prohibit_channels'}:raise StopLowering('NEEDS_AUTHOR_INPUT','UNSUPPORTED_CONSTRAINT',[c['constraint_id']])
        for k,v in rules.get('inputs',{}).items():
            if k in out and out[k]!=v:raise StopLowering('BLOCKED_BY_CONSTRAINT','CONSTRAINT_INPUT_CONFLICT',[k])
            out[k]=v;record(p,k,v,'CONSTRAINT',c['constraint_id'])
    return out
def check_locks(graph,p,primitives,actor,window,extra_overrides=None):
    writes={w for a in primitives for w in channels(a)['WRITES']};p['channel_plan']=[{'primitive_id':a['primitive_id'],**channels(a)} for a in primitives]
    aliases={'world_location':{'ROOT_LOCATION','PROJECTILE_TRANSFORM'},'world_transform':{'ROOT_LOCATION','ROOT_ROTATION','PROJECTILE_TRANSFORM'},'camera_transform':{'CAMERA_LOCATION','CAMERA_ROTATION'},'camera_lens':{'CAMERA_LENS'},'head_rotation':{'HEAD_ROTATION'},'body_rotation':{'BODY_ROTATION'},'location':{'ROOT_LOCATION','PROJECTILE_TRANSFORM','CAMERA_LOCATION'}}
    for o in graph['overrides']+(extra_overrides or []):
        if o['status']!='LOCKED':continue
        relevant=o['target'] in (actor,p['event_id']) or o['scope']=='CONSTRAINT' and o['target'] in [c['constraint_id'] for c in p['constraints']]
        if o['scope']=='SHOT':relevant=any(s['shot_id']==o['target'] and max(s['time_range'][0],window[0])<min(s['time_range'][1],window[1]) for s in graph['shot_intents'])
        if relevant and o['channel'] not in aliases and o['channel'] not in {'*','ROOT_LOCATION','ROOT_ROTATION','BODY_ROTATION','HEAD_ROTATION','WEAPON_TRANSFORM','PROJECTILE_TRANSFORM','ATTACHMENT_STATE','CAMERA_LOCATION','CAMERA_ROTATION','CAMERA_LENS'}:raise StopLowering('BLOCKED_BY_OVERRIDE','UNRESOLVED_LOCK_CHANNEL',[o['override_id']])
        if relevant and (o['channel']=='*' or writes&aliases.get(o['channel'],{o['channel']})):
            p['provenance']['blocking_override']=copy.deepcopy(o);raise StopLowering('BLOCKED_BY_OVERRIDE','OVERRIDE_CONFLICT',[o['override_id']])
    for c in p['constraints']:
        rules=json.loads(c['requirement'])
        if writes&set(rules.get('prohibit_channels',[])):raise StopLowering('BLOCKED_BY_CONSTRAINT','PROHIBITED_CHANNEL',[c['constraint_id']])
def post_constraints(p,fragments,context):
    evidence=[]
    for c in p['constraints']:
        rule=json.loads(c['requirement']);rows=fragments[-1]['world_samples']
        if rule.get('subject') and rule['subject'] not in (p['provenance'].get('affected_entity'),fragments[-1]['affected_entity']):raise StopLowering('NEEDS_AUTHOR_INPUT','CONSTRAINT_SUBJECT_EVALUATION_REQUIRED',[rule['subject']])
        if 'max_speed' in rule and max(norm(r['velocity']) for r in rows)>rule['max_speed']+1e-8:raise StopLowering('BLOCKED_BY_CONSTRAINT','MAX_SPEED_CONSTRAINT',[c['constraint_id']])
        if 'world_bounds' in rule:
            lo,hi=rule['world_bounds']
            if any(not all(lo[i]<=r['position'][i]<=hi[i] for i in range(3)) for r in rows):raise StopLowering('BLOCKED_BY_CONSTRAINT','WORLD_BOUNDS_CONSTRAINT',[c['constraint_id']])
        if 'screen_region' in rule:
            cam=context.get('camera_state')
            if not cam:raise StopLowering('NEEDS_AUTHOR_INPUT','CONSTRAINT_CAMERA_EVIDENCE_MISSING',['camera_state'])
            if context.get('dynamic_camera_constraints') or context.get('lower_cameras'):raise StopLowering('NEEDS_AUTHOR_INPUT','DYNAMIC_CAMERA_CONSTRAINT_PREVIEW_REQUIRED',['evaluated_camera_track'])
            region=REGIONS.get(rule['screen_region']) if isinstance(rule['screen_region'],str) else rule['screen_region']
            points=[project(cam['position'],cam['orientation'],cam['lens'],r['position']) for r in rows]
            bad=[r['frame'] for r,uv in zip(rows,points) if uv is None or not region[0]<=uv[0]<=region[2] or not region[1]<=uv[1]<=region[3]]
            evidence.append({'constraint':c['constraint_id'],'basis':'PROJECTED_CENTER_GEOMETRIC_PREVIEW; occlusion NOT_REVIEWED','violating_frames':bad})
            if bad:raise StopLowering('BLOCKED_BY_CONSTRAINT','SCREEN_POSITION_CONSTRAINT',[c['constraint_id']])
    p['provenance']['constraint_preview']=evidence
def validate_protocol(value,name):
    import jsonschema
    jsonschema.validate(value,json.loads((ROOT/'authoring'/name).read_text(encoding='utf8')))
