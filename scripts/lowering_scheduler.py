"""Compilation dependencies, separate from the six author collections."""
import json
MOTION={'MOVE','ENTER','EXIT','DODGE','PROJECTILE_TRAVEL','RECOVERY'}
def schedule(graph):
    events={e['event_id']:e for e in graph['events']};deps={k:set() for k in events};edges=[]
    def edge(a,b,kind):
        if a!=b and b in events:deps[a].add(b);edges.append({'consumer':a,'producer':b,'kind':kind})
    for d in graph['dependencies']:edge(d['event_id'],d['depends_on'],'CAUSAL')
    for e in events.values():
        eid=e['event_id']
        if e.get('source_event'):edge(eid,e['source_event'],'CAUSAL_SOURCE')
        try:v=json.loads(e['world_intent']['value'])
        except (ValueError,TypeError):v={}
        targets=[v.get('target_entity')]
        if e['event_type'] in ('LOOK','TURN'):targets+=e['actor']
        for target in targets:
            candidates=[o for o in events.values() if target in o['actor'] and o['event_type'] in MOTION and o['start']<=e['end']]
            for o in candidates:
                if o['end']>=e['start'] or not any(x['start']<=e['start'] and x['end']>o['end'] for x in candidates):edge(eid,o['event_id'],'EVALUATED_TARGET')
        # Channel states require earlier committed exits, independently of author causality.
        if e['event_type'] in MOTION:
            prior=[o for o in events.values() if o['actor']==e['actor'] and o['event_type'] in MOTION and o['end']<=e['start'] and o['event_id']!=eid]
            if prior:edge(eid,max(prior,key=lambda x:x['end'])['event_id'],'STATE_CHAIN')
        if e['event_type'] in ('LOOK','TURN'):
            level=v.get('body_level','HEAD' if e['event_type']=='LOOK' else 'ROOT')
            for o in events.values():
                if o['actor']!=e['actor'] or o['event_id']==eid or o['event_type'] not in ('LOOK','TURN') or o['end']>e['start']:continue
                try:ov=json.loads(o['world_intent']['value'])
                except (ValueError,TypeError):continue
                if ov.get('body_level','HEAD' if o['event_type']=='LOOK' else 'ROOT')==level:edge(eid,o['event_id'],'ORIENTATION_STATE_CHAIN')
    pending={k:set(v) for k,v in deps.items()};order=[]
    while pending:
        ready=sorted([k for k,v in pending.items() if not v],key=lambda k:(events[k]['start'],k))
        if not ready:raise ValueError('EVALUATION_CYCLE')
        k=ready[0];order.append(k);pending.pop(k)
        for v in pending.values():v.discard(k)
    cameras=[]
    for s in graph['shot_intents']:
        for e in events.values():
            if e['event_type'] in MOTION and set(s['subjects'])&set(e['actor']) and e['start']<=s['time_range'][1]:cameras.append({'consumer':s['shot_id'],'producer':e['event_id'],'kind':'CAMERA_SUBJECT'})
    return {'order':order,'dependencies':{k:sorted(v) for k,v in deps.items()},'edges':edges,'camera_edges':cameras}
