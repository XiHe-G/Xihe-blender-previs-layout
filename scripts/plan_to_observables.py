"""Compile explicit measurable declarations, preserving unsupported intent as unreviewed.

OBSERVABLE/1.0 JSON is a narrow constraint.requirement grammar, NOT a new AG
collection and NOT a natural language interpretation engine.
"""
import argparse,json
from pathlib import Path
from s2_common import digest,read,write,schema_check
from author_graph_validator import require_valid

TYPES=['SHOT_SIZE','SCREEN_POSITION','SCREEN_DIRECTION','CONTACT','NEAR_MISS','PROJECTILE_CONTINUITY','ACTION_PHASE','CAMERA_STATE','RECOVERY']
PREFIX='OBSERVABLE/1.0 '
SIZE_BANDS={'XS':[0,.10],'SMALL':[.10,.25],'MEDIUM':[.25,.45],'LARGE':[.45,.70],'EXTREME':[.70,1.50]}

def compile_plan(graph,binding):
    require_valid(graph)
    if binding['graph_sha256']!=digest(graph):raise ValueError('STALE_MEASUREMENT_BINDING')
    ids={e['id'] for e in graph['entities']};shots={s['shot_id']:s for s in graph['shot_intents']}
    for v in binding['views'].values():
        if v['entity_id'] not in ids:raise ValueError('UNKNOWN_VIEW_ENTITY')
    obs=[];unreviewed=[]
    for c in graph['constraints']:
        if not c['requirement'].startswith(PREFIX):
            unreviewed.append(dict(source_author_id=c['constraint_id'],reason='UNSUPPORTED_NATURAL_LANGUAGE',plan=c['requirement']));continue
        if c['provenance']['status'] not in ('AUTHORED','SOURCE'):
            unreviewed.append(dict(source_author_id=c['constraint_id'],reason='UNKNOWN_OR_INFERRED',plan=c['requirement']));continue
        o=json.loads(c['requirement'][len(PREFIX):]);o.update(source_author_id=c['constraint_id'],provenance=c['provenance'])
        o.setdefault('observable_id','OBS_'+c['constraint_id']);o.setdefault('expected_range',None);o.setdefault('expected_state',None)
        o.setdefault('tolerance',0.);o.setdefault('severity','MAJOR')
        if not set(o['subjects']).issubset(binding['views']):raise ValueError('UNKNOWN_MEASUREMENT_VIEW')
        subject_entities={binding['views'][v]['entity_id'] for v in o['subjects']}
        if not subject_entities.issubset(set(c['targets'])):raise ValueError('OBSERVABLE_SUBJECT_NOT_IN_SOURCE')
        if o['shot_id'] is not None and (o['shot_id'] not in shots or o['shot_id'] not in c['targets']):raise ValueError('OBSERVABLE_SHOT_NOT_IN_SOURCE')
        lo,hi=o['time_window']
        if not 0<=lo<hi<=graph['timebase']['duration']:raise ValueError('INVALID_OBSERVABLE_WINDOW')
        if o['shot_id']:
            a,b=shots[o['shot_id']]['time_range']
            if lo<a-1e-8 or hi>b+1e-8:raise ValueError('OBSERVABLE_OUTSIDE_SHOT')
        if o['type']=='SHOT_SIZE' and o['expected_range'] is None:
            band=(o['expected_state'] or {}).get('band');o['expected_range']=SIZE_BANDS.get(band)
        if 'requirement_source' in o:
            if not all(k in o for k in ('confidence','tolerance_profile','behavior_profile')):raise ValueError('INCOMPLETE_TOLERANCE_PROVENANCE')
            if o['behavior_profile']!='DECLARED_BEHAVIOR' and (o['type']!='CAMERA_STATE' or (o['expected_state'] or {}).get('mode')!='HOLD'):raise ValueError('PROFILE_BEHAVIOR_MISMATCH')
        obs.append(o)
    # Exact controlled tokens in SHOT_INTENT are also usable; no prose guessing.
    for s in graph['shot_intents']:
        for field,typ,allowed in [('shot_size_intent','SHOT_SIZE',SIZE_BANDS),('screen_direction_intent','SCREEN_POSITION',dict.fromkeys(['LEFT','RIGHT','CENTER','UPPER','LOWER'])),('camera_behavior_intent','CAMERA_STATE',{'HOLD':None})]:
            intent=s[field];value=intent['value']
            views=[k for k,v in binding['views'].items() if v.get('default') and v['entity_id'] in s['subjects']]
            if intent['status'] in ('AUTHORED','SOURCE') and isinstance(value,str) and value in allowed and views:
                state={'band':value} if typ=='SHOT_SIZE' else {'region':value} if typ=='SCREEN_POSITION' else {'mode':'HOLD','max_translation':.01,'max_rotation_deg':.1,'max_lens_delta':.01}
                obs.append(dict(observable_id='OBS_'+s['shot_id']+'_'+typ,source_author_id=s['shot_id'],shot_id=s['shot_id'],time_window=s['time_range'],type=typ,subjects=views[:1],expected_range=SIZE_BANDS[value] if typ=='SHOT_SIZE' else None,expected_state=state,tolerance=0.,severity='MAJOR',provenance=intent))
            else:unreviewed.append(dict(source_author_id=s['shot_id'],reason='UNKNOWN_OR_UNSUPPORTED_INTENT',plan={field:intent}))
    if len({o['observable_id'] for o in obs})!=len(obs):raise ValueError('DUPLICATE_OBSERVABLE_ID')
    result=dict(schema_version='EXPECTED-OBSERVABLES/1.0',graph_id=graph['graph_id'],graph_sha256=digest(graph),measurement_binding_sha256=digest(binding),observables=obs,not_reviewed=unreviewed)
    schema_check(result,'expected-observable.schema.json');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graph',required=True);p.add_argument('--binding',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    write(a.output,compile_plan(read(a.graph),read(a.binding)))
