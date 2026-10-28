"""Opt-in production contract utilities. Never changes Blender/AG/CSP or grants approval.

The compilers below package explicit author data, not natural-language direction or
animation. Schema validation is not native or artistic validation.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/production-v2.schema.json').read_text(encoding='utf-8'))
VALIDATOR = Draft202012Validator(SCHEMA)
BINDING = ('project','scene','sequence','shot_range','source_blend','layout_version',
           'lighting_version','visibility_version','resolution','frame_range','camera_version','revision_ids')
PROTECTED = {'CAMERA','BLOCKING','SCREEN_DIRECTION','CUT','BEAT_RESULT'}
FREEDOMS = {'LIMB_DETAIL','EXPRESSION','CLOTH','HAIR','ACTION_DETAIL','FINAL_VFX','FINAL_MATERIAL'}

class ContractError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ContractError(message)

def _finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'Non-finite number')
    elif isinstance(value, dict):
        for v in value.values(): _finite(v)
    elif isinstance(value, list):
        for v in value: _finite(v)

def _vector(v, positive=False):
    require(len(v) == 3 and all(isinstance(x,(float,int)) and not isinstance(x,bool) for x in v), 'Expected numeric 3-vector')
    if positive: require(all(x > 0 for x in v), 'Expected positive dimensions')

def _unique(items, label):
    require(len(items) == len(set(items)), 'Duplicate ' + label)

def _authorization(auth):
    require(auth['mode'] in ('NONE','PLAN_APPROVAL','DIRECT_REFERENCE'), 'Unknown authorization mode')
    if auth['mode'] != 'NONE':
        require(bool(auth['source_message'].strip()) and bool(auth['scope'].strip()), 'Authorization needs actual source message and scope')
    # This records an author assertion; caller must match it to trusted user history.

def validate(document):
    _finite(document)
    errors = sorted(VALIDATOR.iter_errors(document), key=lambda e: str(e.path))
    if errors:
        leaf = errors[0]
        if leaf.context:
            relevant = [e for e in leaf.context if not e.path or e.path[0] != 'contract']
            leaf = relevant[0] if relevant else leaf
        raise ContractError('Schema: ' + leaf.message)
    k = document['contract']; d = document
    if k == 'task':
        require(d['primary_owner'] in d['requested_routes'], 'Primary owner must be a requested route')
        require(not (d['storyboard_confirmed'] and 'DESIGN_FROM_STORY' in d['requested_routes'] and not d['design_permission']), 'Confirmed storyboard needs explicit redesign permission')
        require('LIGHTING_PREVIS' not in d['requested_routes'] or d['lighting_required'], 'Lighting route must declare required lighting')
        _authorization(d['lighting_authorization'])
    elif k == 'scene-state':
        ids = [x['id'] for x in d['landmarks']]; _unique(ids, 'landmark IDs')
        require(all(x and all(c.isupper() or c.isdigit() or c=='_' for c in x) for x in ids), 'Use stable uppercase landmark IDs')
        for x in d['landmarks']: _vector(x['position'])
        refs=d['entrances']+d['exits']+d['key_occluders']+sum(d['depth_regions'].values(),[])
        for f in ('walkable_regions','support_surfaces','light_zones'):
            _unique([x['id'] for x in d[f]],f)
            refs += sum([x['landmark_ids'] for x in d[f]],[])
        require(set(refs) <= set(ids), 'Dangling landmark reference')
        shots=[x['shot_id'] for x in d['boundaries']];_unique(shots,'boundary shot IDs')
        require(shots, 'Scene must have a shot boundary')
        cast = {x['identity'] for x in d['boundaries'][0]['characters']}
        require(cast, 'Scene cast is empty')
        support={x['id'] for x in d['support_surfaces']}|{'AIRBORNE','NONE'}
        zones={x['id'] for x in d['light_zones']}|{'NONE','UNKNOWN'}
        for b in d['boundaries']:
            _unique([x['identity'] for x in b['characters']],'characters')
            require({x['identity'] for x in b['characters']}==cast,'Offscreen cast must persist at every boundary')
            for x in b['characters']:
                for f in ('world_position','facing','body_orientation'): _vector(x[f])
                require(x['support'] in support and x['lighting_zone'] in zones,'Unknown support/light zone')
                require(set(x['prop_control']) <= set(d['persistent_props']),'Unknown persistent prop')
                require(x['visible'] or bool(x['action_state']), 'Offscreen action state required')
                require(x['next_entrance_dependency'] in shots or x['next_entrance_dependency'] in ('','NONE'), 'Unknown next entrance dependency')
        require(all(x['minimum'] <= x['maximum'] for x in d['height_bands']), 'Inverted height band')
    elif k == 'revision-record':
        require(bool(d['source_message'].strip()) and bool(d['source_version'].strip()), 'Revision provenance required')
        require(d['target_shots'], 'Revision target required')
        require(not set(d['allowed_channels']) & set(d['protected_channels']), 'Allowed/protected channel conflict')
        require(d['allowed_channels'], 'Revision must allow a channel')
    elif k == 'camera-semantic':
        _camera(d)
    elif k == 'identity-proxy':
        _vector(d['color']);require(all(0<=x<=1 for x in d['color']),'Color range')
        require(d['head_silhouette'].strip() and d['anchors'], 'Non-color identity anchors required')
        _unique([a['id'] for a in d['anchors']], 'identity anchors')
        for a in d['anchors']: _vector(a['scale'],True)
        _unique([h['side'] for h in d['simple_hands']], 'hand sides')
        for h in d['simple_hands']:
            require(h['side'] in ('LEFT','RIGHT') and h['geometry'] in ('SPHERE','BOX'),'Simple hand shape/side')
            require(h['relation'] in ('GRIP','CONTACT','POINT') and h['target_ref'].strip(),'Hand target relation required')
            _vector(h['anchor'])
    elif k == 'physical-profile':
        require(d['mobility_class'] in ('LIMITED','NORMAL','AGILE','EXTREME'), 'Unknown mobility class')
        require(d['evidence_source'] in ('AUTHOR_DEFINED_RELATIVE','REFERENCE_PROPORTIONS','USER_SPECIFIED'), 'Do not infer kilograms from images')
        require(d['surface'].strip() and d['current_load'].strip(), 'Surface/load required')
        require(d['story_intent'] != 'FLY' or d['aerial_capability'] in ('FLY','FLOAT'), 'FLY requires aerial capability')
        if d['locomotion_type'] != 'HUMAN': require(d['motion_binding']=='NOT_IMPLEMENTED_RUNTIME','New locomotion cannot claim runtime')
    elif k == 'locomotion-profile':
        for f in ('acceleration_envelope','cruise_range'):
            require(len(d[f])==2 and 0<=d[f][0]<=d[f][1], 'Invalid '+f)
        require(d['turn_radius']>=0 and d['stopping_distance']>=0,'Negative motion bound')
        if d['locomotion_type']!='HUMAN': require(d['runtime_binding']=='NOT_IMPLEMENTED_RUNTIME','Non-HUMAN runtime unavailable')
    elif k == 'prop-interaction':
        _vector(d['size'],True);_vector(d['com_offset'])
        _unique([p['id'] for p in d['contact_points']], 'contact points')
        roles={p['role'] for p in d['contact_points']}
        for p in d['contact_points']: _vector(p['position'])
        require(d['attachment_point'].strip() and d['orientation_constraint'].strip(), 'Attachment/orientation required')
        if d['carry_mode']=='PALM_SUPPORTED': require('PALM' in roles and d['orientation_constraint']=='UPRIGHT','Palm support needs upright palm contact')
        if d['carry_mode']=='GROUND_SUPPORTING': require({'GRIP','SUPPORT'}<=roles and bool(d['support_ref']),'Ground support needs grip and support binding')
        if d['carry_mode']=='WEAPON': require('GRIP' in roles and d['reach']>0 and 'WEAPON_AXIS' in d['interaction_rules'], 'Weapon needs grip, reach and axis')
        if d['carry_mode']=='BACK_MOUNTED': require('BACK' in roles,'Back mounting needs back contact')
        if d['carry_mode']=='TWO_HAND_HELD': require({'LEFT_GRIP','RIGHT_GRIP'}<=roles,'Two hand grips required')
    elif k == 'impact-response':
        _vector(d['relative_velocity']);_vector(d['contact_direction'])
        allowed={'NO_EFFECT','LIGHT_REACTION','BODY_SHIFT','STEP_BACK','SLIDE','ROTATE','KNOCKBACK','FALL_CANDIDATE'}
        require(d['response_candidates'] and set(d['response_candidates'])<=allowed,'Unknown response')
        require(d['selection_authority']=='DIRECTOR_REQUIRED','Response candidates are not physics solutions')
        require(all(d[f].strip() for f in ('momentum_ref','support_ref','contact_intent_ref')),'Reuse Sprint005/004/010 bindings')
    elif k == 'vfx-previs':
        _vector(d['origin']);_vector(d['direction'])
        light=d['light_contribution']
        require(not light['enabled'] or bool(light['lighting_event_ref']), 'Visible FX is not a lighting event')
        require(light['validation'] in ('NOT_REVIEWED','PASS','FAIL'),'Unknown light validation')
    elif k == 'lighting-context':
        _vector(d['key_direction']);_authorization(d['authorization'])
        require({'camera','blocking','motion'}<=set(d['protected_channels']),'Lighting cannot rewrite layout')
    elif k == 'delivery-manifest':
        _delivery(d)
    elif k == 'ai-video-handoff':
        overrides={x['field'] for x in d['authorized_overrides']}
        require(overrides<=PROTECTED,'Unknown protected override')
        require(all(x['source_message'].strip() and x['scope'].strip() for x in d['authorized_overrides']), 'Overrides need actual scoped user source')
        require(PROTECTED-overrides<=set(d['protected_fields']),'Missing downstream locks')
        require(set(d['downstream_freedoms'])<=FREEDOMS|overrides,'Unsupported downstream freedom')
        _unique([x['identity'] for x in d['identity_mapping']], 'identity mapping')
        _unique([x['shot_id'] for x in d['shots']], 'handoff shots')
        require(d['cut_points']==sorted(set(d['cut_points'])),'Cuts must be strictly ordered')
        actors={x['identity'] for x in d['identity_mapping']}
        for s in d['shots']:
            require({x['identity'] for x in s['world_positions']}<=actors,'Unmapped actor')
            require(s['lens']>0,'Lens must be positive')
            for x in s['world_positions']: _vector(x['position'])
    return {'status':'PASS','scope':'CONTRACT_ONLY','native_validation':'NOT_REVIEWED','director_approval':'NOT_REVIEWED','downstream_validation':'NOT_REVIEWED'}

def _camera(d):
    p=d['position_path']; r=d['recipe']
    require(d['rotation_behavior'] not in d['forbidden_transforms'], 'Forbidden rotation behavior')
    require(d['composition']['lens']>0,'Positive lens required')
    for f in ('subject_occupancy','headroom','lead_room'): require(0<=d['composition'][f]<=1,'Invalid screen proportion')
    require(not (set(d['allowed_compensation']) & set(d['forbidden_transforms'])),'Camera compensation conflict')
    if not d['allow_pan']: require(d['rotation_behavior']!='PAN' and 'PAN' not in d['allowed_compensation'], 'Pan not authorized')
    if r=='LATERAL_REVEAL_FROM_SHOULDER':
        require(d['start_anchor']=='HEAD_SHOULDER','Reveal starts at head/shoulder')
        require(d['height_behavior']=='FIXED' and max(x[2] for x in p)-min(x[2] for x in p)<1e-8,'Reveal must preserve height')
        require(max(x[1] for x in p)-min(x[1] for x in p)<1e-8 and abs(p[-1][0]-p[0][0])>1e-8,'Path must be lateral in declared camera-start local coordinates')
        require({'ORBIT','HEIGHT_CHANGE','WAIST_RISE'}<=set(d['forbidden_transforms']),'Missing reveal prohibitions')
    if r=='DIAGONAL_PULLBACK':
        delta=[p[-1][i]-p[0][i] for i in range(3)];norm=sum(x*x for x in delta)
        require(norm>0 and sum(abs(x)>1e-8 for x in delta)>=2 and delta[1]<0,'Diagonal pullback must move backward on a diagonal')
        previous=-1e-8
        for point in p:
            t=sum((point[i]-p[0][i])*delta[i] for i in range(3))/norm
            require(previous<=t<=1+1e-8 and all(abs(point[i]-p[0][i]-t*delta[i])<1e-8 for i in range(3)),'Pullback must be one monotonic straight segment')
            previous=t
        require('ORBIT' in d['forbidden_transforms'],'Pullback forbids orbit')
    if r=='STATIC_REACTION': require(all(x==p[0] for x in p) and d['rotation_behavior']=='FIXED' and d['lens_behavior']=='FIXED','Static reaction transform/lens must stay fixed')
    if r=='AXIS_CROSS_AUTHORIZED': require(d['axis_cross_authorization'].strip(),'Axis cross needs scoped source authorization')
    require(d['composition_evidence'] in ('NOT_REVIEWED','PASS','FAIL'),'Unknown composition evidence')

def _delivery(d):
    require(d['shot_range'] and d['requested_outputs'],'Delivery needs selected shots/outputs')
    _unique(d['shot_range'],'shot range');_unique(d['revision_ids'],'revision IDs')
    require(len(d['resolution'])==2 and all(x>0 for x in d['resolution']),'Positive resolution required')
    require(len(d['frame_range'])==2 and d['frame_range'][0]<=d['frame_range'][1],'Invalid frame range')
    pairs=[(x['view'],x['style']) for x in d['requested_outputs']];_unique(pairs,'output combinations')
    rendered=[]
    for a in d['artifacts']:
        require(all(a['binding'][f]==d[f] for f in BINDING),'Artifact version binding differs from manifest')
        require(len(a['sha256'])==64 and all(c in '0123456789abcdef' for c in a['sha256']),'Artifact SHA required')
        require(a['kind']=='VIDEO','Manifest artifact currently supports VIDEO only')
        rendered.append((a['view'],a['style']))
    require(sorted(rendered)==sorted(pairs),'Artifacts must exactly cover requested combinations')
    require([x['shot_id'] for x in d['shot_ranges']]==d['shot_range'],'Shot order/range mismatch')
    require([x['shot_id'] for x in d['cameras']]==d['shot_range'],'Camera list/order mismatch')
    require(all(x['version']==d['camera_version'] for x in d['cameras']),'Camera version mismatch')
    last=d['frame_range'][0]-1
    for x in d['shot_ranges']:
        f=x['frames'];require(len(f)==2 and f[0]==last+1 and f[1]>=f[0],'Non-contiguous shot range');last=f[1]
    require(last==d['frame_range'][1],'Shot frames do not cover delivery')
    require({x['revision_id'] for x in d['changes']}==set(d['revision_ids']),'Changelog revision mismatch')

def route(task=None):
    if task is None:
        return {'primary_owner':'LEGACY','routes':[],'action':'UNCHANGED_LEGACY_ENTRY','additional_confirmation':False}
    validate(task)
    require(task['contract']=='task','Expected task')
    auth=task['lighting_authorization']
    return {'primary_owner':task['primary_owner'],'routes':task['requested_routes'],
            'full_director_design':'DESIGN_FROM_STORY' in task['requested_routes'],
            'storyboard_edit_allowed':task['design_permission'],
            'lighting_plan_confirmation':task['lighting_required'] and auth['mode']=='NONE',
            'authorization_verification':'MATCH_SOURCE_MESSAGE_AND_SCOPE' if auth['mode']!='NONE' else 'NONE',
            'requested_outputs':task['requested_outputs'],'scope':'ROUTING_ONLY'}

def locomotion_route(profile):
    validate(profile)
    require(profile['contract'] in ('locomotion-profile','physical-profile'),'Expected locomotion/physical profile')
    human=profile['locomotion_type']=='HUMAN'
    return {'adapter':'Sprint008/MOTION-INTENSITY' if human else None,
            'runtime':'EXISTING_EXPLICIT_PARAMETERS_ONLY' if human else 'NOT_IMPLEMENTED_RUNTIME',
            'automatic_physical_mapping':'NOT_IMPLEMENTED_RUNTIME'}

def revision_query(record, shot_order):
    validate(record);require(record['contract']=='revision-record','Expected revision record')
    _unique(shot_order,'shot order');known=set(shot_order);direct=set(record['target_shots'])
    require(direct<=known and set(record['dependent_shots'])<=known,'Unknown revision shot')
    edges=record['continuity_dependencies']+record['lighting_dependencies']
    graph={s:[] for s in shot_order}
    for e in edges:
        require(e['from_shot'] in known and e['to_shot'] in known,'Dangling dependency')
        graph[e['from_shot']].append(e['to_shot'])
    visiting=set();done=set()
    def visit(s):
        require(s not in visiting,'Cyclic boundary inheritance; use event references on existing timeline')
        if s in done:return
        visiting.add(s)
        for t in graph[s]:visit(t)
        visiting.remove(s);done.add(s)
    for s in shot_order:visit(s)
    affected=set(direct);stack=list(direct)
    while stack:
        for t in graph[stack.pop()]:
            if t not in affected:affected.add(t);stack.append(t)
    dependencies=affected-direct
    require(dependencies<=set(record['dependent_shots']),'Record omits derived dependent shots')
    # Explicit dependencies may cover non-graph relationships; inspect them conservatively.
    dependencies |= set(record['dependent_shots'])-direct
    affected |= dependencies
    ordered=lambda s:[x for x in shot_order if x in s]
    return {'scope_status':'PLANNED_NOT_EXECUTED',
            'DIRECTLY_MODIFIED':ordered(direct),'DEPENDENCY_CHECKED':ordered(dependencies),
            'UNCHANGED_PROTECTED':ordered(known-affected),
            'category_semantics':'Requested modification / required dependency audit / protected scope; names are not completion evidence',
            'validation_status':'NOT_REVIEWED','protected_channels':record['protected_channels']}

def compile_camera(contract):
    validate(contract);require(contract['contract']=='camera-semantic','Expected camera contract')
    checks={
      'OTS_RELATION':['head/shoulder foreground','relationship and depth'],
      'LATERAL_REVEAL_FROM_SHOULDER':['fixed height','lateral path','head/shoulder start','reveal target','no orbit'],
      'DIAGONAL_PULLBACK':['single diagonal straight path','no orbit','end composition'],
      'FOLLOW_THEN_STOP':['follow window','stop event','camera terminal velocity'],
      'STATIC_REACTION':['fixed transform and lens','reaction visibility'],
      'PUSH_IN_FOR_REALIZATION':['motivated trigger','approach target','end occupancy'],
      'COMPOSITION_PRESERVE_REFRAME':['all composition fields','world transform may change'],
      'SCREEN_DIRECTION_TRACK':['screen direction across frames and cuts'],
      'FOREGROUND_WIPE':['occluder crossing and reveal interval'],
      'AXIS_CROSS_AUTHORIZED':['source authorization','axis transition and orientation cues']}
    return {'contract':copy.deepcopy(contract),'required_native_checks':checks[contract['recipe']],
            'compiler_scope':'EXPLICIT_CONSTRAINT_PACKET','natural_language_solver':'NOT_IMPLEMENTED_RUNTIME',
            'blender_lowering':'NOT_IMPLEMENTED_RUNTIME','composition_validation':'NOT_REVIEWED'}

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def _bound_file(base, relative):
    p=Path(relative);require(not p.is_absolute(),'Use package-relative paths')
    root=Path(base).resolve();p=(root/p).resolve()
    require(p.is_relative_to(root),'Path escapes package')
    require(p.is_file(),'Missing bound file: '+relative)
    return p

def compile_delivery(manifest, base):
    validate(manifest);require(manifest['contract']=='delivery-manifest','Expected delivery manifest')
    source=_bound_file(base,manifest['source_blend'])
    require(file_sha(source)==manifest['source_sha256'],'Source Blend SHA mismatch')
    for a in manifest['artifacts']:
        require(file_sha(_bound_file(base,a['path']))==a['sha256'],'Output SHA mismatch')
    return {'DELIVERY_MANIFEST':copy.deepcopy(manifest),'CHANGELOG':manifest['changes'],
            'CAMERA_LIST':manifest['cameras'],'SHOT_RANGE':manifest['shot_ranges'],
            'EVIDENCE':{'status':'PASS','scope':'FILE_HASH_AND_DECLARED_BINDING_ONLY',
                        'native_render_provenance':'NOT_REVIEWED','visual_review':'NOT_REVIEWED',
                        'required_existing_check':'scripts/verify_delivery.py + native/render receipts'}}

def compile_handoff(handoff, manifest):
    validate(handoff);validate(manifest)
    require(handoff['contract']=='ai-video-handoff' and manifest['contract']=='delivery-manifest','Expected handoff and delivery')
    require(handoff['layout_version']==manifest['layout_version'],'Handoff layout version mismatch')
    require([s['shot_id'] for s in handoff['shots']]==manifest['shot_range'],'Handoff shot order mismatch')
    require(handoff['cut_points']==[s['frames'][0] for s in manifest['shot_ranges'][1:]],'Handoff cut mismatch')
    return {'AI_VIDEO_HANDOFF':copy.deepcopy(handoff),'manifest_fingerprint':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
            'status':'CONTRACT_PACKAGED','render_freshness':'NOT_REVIEWED','downstream_validated':False,'seedance_invoked':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['validate','route','locomotion','revision','camera','delivery','handoff'])
    p.add_argument('input',type=Path);p.add_argument('--shots',nargs='+');p.add_argument('--base',type=Path);p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();load=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
    try:
        d=load(a.input)
        if a.operation=='validate':result=validate(d)
        elif a.operation=='route':result=route(d)
        elif a.operation=='locomotion':result=locomotion_route(d)
        elif a.operation=='revision':require(bool(a.shots),'--shots required');result=revision_query(d,a.shots)
        elif a.operation=='camera':result=compile_camera(d)
        elif a.operation=='delivery':require(a.base is not None,'--base required');result=compile_delivery(d,a.base)
        else:require(a.manifest is not None,'--manifest required');result=compile_handoff(d,load(a.manifest))
        if a.output:
            a.output.parent.mkdir(parents=True,exist_ok=True)
            with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        else:print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ContractError,OSError,ValueError) as e:
        p.exit(2,str(e)+'\n')

if __name__=='__main__':main()
