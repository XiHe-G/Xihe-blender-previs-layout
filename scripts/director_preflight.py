"""DIRECTOR-PREFLIGHT/1.0: feasibility only, one revision at most."""
import json,copy
from orientation_feasibility import orientation_budget,channel_plan
from dynamic_look_feasibility import dynamic_look_feasibility

def run(graph,context,revision=None):
    checks=[]
    for e in graph['events']:
        try:v=json.loads(e['world_intent']['value'])
        except Exception:v={}
        if e['event_type'] in ('TURN','LOOK') and v.get('target_direction'):
            # current yaw is derived from the graph entity state; +Y is 0°.
            entry=next(x for x in graph['entities'] if x['id']==e['actor'][0]);facts=json.loads(entry['persistent_state']['value']);import math
            a=math.radians(facts.get('heading_degrees',0));d=v['target_direction'];target=math.atan2(d[0],d[1]);from primitive_sampler import yaw_quat
            b=orientation_budget(yaw_quat(a),yaw_quat(target),e['end']-e['start'],v.get('max_turn_rate_deg_s',90))
            b.update(event_id=e['event_id'],event_type=e['event_type']);checks.append({'type':'ORIENTATION_FEASIBILITY','result':b})
        elif e['event_type'] in ('LOOK','TURN') and v.get('target_entity'):
            checks.append({'type':'DYNAMIC_TARGET_TRACKABILITY','event_id':e['event_id'],'status':'DEFERRED_TO_EVALUATED_TRACK','target_entity':v['target_entity']})
    return {'schema_version':'DIRECTOR-PREFLIGHT/1.0','graph_id':graph['graph_id'],'status':'PASS' if all(x.get('result',{}).get('status','PASS') not in ('INFEASIBLE_DURATION','INFEASIBLE_TRACKING') for x in checks) else 'FAIL','checks':checks,'director_revision_allowed':True,'revision_count':1 if revision else 0,'automatic_revision':False}
