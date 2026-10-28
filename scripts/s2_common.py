"""S2 compiler utilities. Canonical hashes and bounded scalar execution regions."""
from copy import deepcopy
import hashlib,json,math
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
TRACK_SECTIONS={'world_tracks':'object_tracks','camera_tracks':'object_tracks',
 'weapon_tracks':'object_tracks','projectile_tracks':'object_tracks','visibility':'object_tracks','pose_tracks':'actor_pose_tracks'}
CHANNELS={'location':['location'],'rotation':['rotation','rotation_mode'],'scale':['scale'],
 'camera_transform':['location','rotation','rotation_mode','scale'],'lens':['lens'],
 'visibility':['hide_render','hide_viewport'],'pose':None}
RECORD_SECTIONS={'event_execution':('action_beats','event_id'),'shot_execution':('shot_plan','id'),
 'proxy_lifecycles':('proxy_lifecycles','id'),'camera_choreography':('camera_choreography','shot_id'),
 'continuity':('continuity_states','cut_frame'),'screen_targets':('screen_targets','shot_id'),'causal_links':('causal_links','reaction_event')}

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def schema_check(value,name):
    errors=list(Draft202012Validator(read(ROOT/'authoring'/name)).iter_errors(value))
    if errors: raise ValueError('SCHEMA_ERROR: '+str(errors[0].message))
    digest(value) # Reject non-finite JSON values, including inside arbitrary old/new values.

def token(x): return str(x).replace('~','~0').replace('/','~1')
def pointer(*parts): return '/'+ '/'.join(token(x) for x in parts)
def parts(path):
    if not path.startswith('/'): raise ValueError('Invalid JSON pointer')
    return [p.replace('~1','/').replace('~0','~') for p in path[1:].split('/')]
def get(value,path):
    for p in parts(path): value=value[int(p)] if isinstance(value,list) else value[p]
    return value
def put(value,path,replacement):
    p=parts(path);parent=value
    for k in p[:-1]: parent=parent[int(k)] if isinstance(parent,list) else parent[k]
    key=int(p[-1]) if isinstance(parent,list) else p[-1]
    if isinstance(parent[key],(dict,list)) or isinstance(replacement,(dict,list)):
        raise ValueError('PATCH_MUST_REPLACE_SCALAR_LEAVES')
    if type(parent[key]) is bool and type(replacement) is not bool: raise ValueError('Scalar type mismatch')
    if isinstance(parent[key],(int,float)) and not isinstance(parent[key],bool):
        if isinstance(replacement,bool) or not isinstance(replacement,(int,float)) or not math.isfinite(replacement): raise ValueError('Scalar type mismatch')
    elif type(parent[key]) is not type(replacement): raise ValueError('Scalar type mismatch')
    parent[key]=deepcopy(replacement)
def leaves(value,path=''):
    if isinstance(value,dict):
        for k,v in value.items(): yield from leaves(v,path+'/'+token(k))
    elif isinstance(value,list):
        for i,v in enumerate(value): yield from leaves(v,path+'/'+str(i))
    else: yield path,value
def differences(a,b):
    left=dict(leaves(a));right=dict(leaves(b))
    if left.keys()!=right.keys(): raise ValueError('STALE: structural execution changes require full lowering')
    return [p for p in left if digest(left[p])!=digest(right[p])]

def selector_paths(csp,region):
    """Resolve approved ownership selectors to existing scalar leaves only."""
    section=region['section'];target=region['target'];channel=region['channel'];result=[]
    if section in TRACK_SECTIONS:
        table=TRACK_SECTIONS[section]
        samples=csp.get(table,{}).get(target)
        if samples is None: raise ValueError('STALE: unknown execution track '+target)
        if channel not in CHANNELS: raise ValueError('Unsupported track channel '+channel)
        if section=='visibility' and channel!='visibility': raise ValueError('Invalid visibility selector')
        if section=='pose_tracks' and channel!='pose': raise ValueError('Invalid pose selector')
        if section!='pose_tracks' and channel=='pose': raise ValueError('Pose selector on object track')
        start,end=region['frame_range']
        if not (isinstance(start,int) and not isinstance(start,bool) and isinstance(end,int) and 1<=start<=end<=csp['timebase']['frames']):
            raise ValueError('Invalid execution region frame range')
        for i,sample in enumerate(samples):
            if start<=sample['frame']<=end:
                fields=CHANNELS[channel] or list(sample['state'])
                for k in fields:
                    if k in sample['state']:
                        result.extend(p for p,v in leaves(sample['state'][k],pointer(table,target,i,'state',k)))
    elif section in RECORD_SECTIONS:
        table,idfield=RECORD_SECTIONS[section]
        matches=[(i,r) for i,r in enumerate(csp[table]) if (r['cause_event']+'>'+r['reaction_event'] if section=='causal_links' else str(r[idfield]))==str(target)]
        if len(matches)!=1: raise ValueError('STALE: record target missing/ambiguous '+str(target))
        i,record=matches[0];base=pointer(table,i)
        for path,value in leaves(record,base):
            relative=parts(path)[2:]
            first=relative[0]
            allow=False
            if section=='event_execution': allow=first in ('interval_s','phases','breakdowns','outcome','notes') and (first!='phases' or 'interval_s' in relative)
            elif section=='shot_execution': allow=first in ('first_frame','end_frame_exclusive','interval_s','summary')
            elif section=='proxy_lifecycles': allow=first in ('visible_intervals_s','end_state') or first=='stages' and 'interval_s' in relative
            elif section=='camera_choreography': allow=first=='states' and ('interval_s' in relative or relative[-1] in ('trigger','delay_s','entry_speed','exit_speed','framing_goal'))
            elif section=='continuity': allow=first in ('phase_state','state_evidence','active_event_ids')
            elif section=='screen_targets': allow=first not in ('shot_id','authority')
            elif section=='causal_links':allow=first in ('trigger_s','response_s','anticipation_s','direction_rule','strength_rule')
            if allow:result.append(path)
    else: raise ValueError('Unsupported patch section '+section)
    if not result: raise ValueError('STALE: empty execution selector '+region.get('region_id',str(target)))
    return sorted(result)

def projection(csp,selectors):
    paths={p for r in selectors for p in selector_paths(csp,r)}
    return {p:get(csp,p) for p in sorted(paths)}

def unchanged_report(base,result,allowed):
    changes=differences(base,result);outside=[p for p in changes if p not in set(allowed)]
    a=dict(leaves(base));unchanged={p:v for p,v in a.items() if p not in set(allowed)}
    return dict(status='PASS' if not outside else 'FAIL',numeric_tolerance=0,
      compared_scalar_leaves=len(unchanged),unchanged_sha256=digest(unchanged),
      unexpected_changes=outside,changed_leaf_count=len(changes),
      coverage=['shot timing','entity identity','world/pose tracks','camera','weapon/projectile','visibility','lifecycle','continuity','all other CSP leaves'])
