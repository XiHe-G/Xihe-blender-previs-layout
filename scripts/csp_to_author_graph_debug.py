"""Read-only CSP inspection adapter. Output is DEBUG, never author approval.

Only explicit CSP fields are SOURCE. Name-based classifications are INFERRED;
missing intent remains UNKNOWN. No emotion or causal edges are invented.
"""
import argparse
import json
import re
from pathlib import Path
from combat_sequence_package import read_package
from timebase import frame_to_time


def intent(value=None, status='UNKNOWN', source='Not recoverable from execution data'):
    return {'value': value, 'status': status, 'source': source}


def stable(prefix, name):
    # Include UTF-8 bytes for non-ASCII tokens to avoid silent slug collisions.
    token = ''.join(c if c.isascii() and (c.isalnum() or c == '_') else '_%x_' % ord(c) for c in name)
    return prefix + (token or 'EMPTY')


def debug_graph(p):
    fps = p['timebase']['fps']
    g = dict(schema_version='AG/1.0', graph_id=p['sequence_id'], origin='DEBUG',
             module=p['layout_mode'], entry_mode=p['entry_mode'],
             timebase=dict(time_unit='seconds', fps=fps, duration=p['timebase']['frames']/fps, frame_origin=1),
             execution=None, entities=[], shot_intents=[], events=[], constraints=[], dependencies=[], overrides=[])
    aliases = {}
    for a in p['actors']:
        sid = stable('CHAR_', a['id']); aliases[a['id']] = sid
        g['entities'].append(dict(id=sid, type='character', module=g['module'], owner=None,
                                 role=intent(), persistent_state=intent()))
    for proxy in p['proxy_lifecycles']:
        name = proxy['id']; role = proxy['role']
        kind = 'weapon' if role == 'WEAPON_PROXY' else 'prop'
        if re.search(r'PROJECTILE|^ORB|^BALL|^WOOD_\d+', name): kind = 'projectile'
        sid = stable({'weapon':'WPN_', 'projectile':'PROJ_', 'prop':'PROP_'}[kind], name)
        if name in aliases: continue
        aliases[name] = sid
        g['entities'].append(dict(id=sid, type=kind, module=g['module'], owner=None,
                                 role=intent(role, 'INFERRED' if kind == 'projectile' else 'SOURCE', 'CSP proxy_lifecycles.role; projectile classification is INFERRED from identifier'),
                                 persistent_state=intent(proxy['end_state'], 'SOURCE', 'CSP proxy_lifecycles.end_state')))
    by_id = {e['id']:e for e in g['entities']}
    for proxy in p['proxy_lifecycles']:
        owner = proxy.get('owner_id', proxy.get('owner'))
        by_id[aliases[proxy['id']]]['owner'] = aliases.get(owner)
    def resolve(text):
        if text in aliases: return [aliases[text]]
        # Only resolve explicit exact names; unresolved prose is not an object.
        return list(dict.fromkeys(aliases[v.strip()] for v in text.split('/') if v.strip() in aliases))
    for i, s in enumerate(p['shot_plan']):
        g['shot_intents'].append(dict(shot_id=f'SHOT_{i+1:03d}',
            time_range=[frame_to_time(s['first_frame'],fps),frame_to_time(s['end_frame_exclusive'],fps)],
            primary_information=intent(s['summary'],'SOURCE','CSP shot_plan.summary') if s.get('summary') else intent(),
            subjects=[], shot_size_intent=intent(), screen_direction_intent=intent(),
            camera_behavior_intent=intent(), required_visibility=[], handoff_to_next=None))
    for b in p['action_beats']:
        peak = b.get('phases',{}).get('PEAK',{}).get('interval_s',[b['interval_s'][0]])[0]
        g['events'].append(dict(event_id=stable('EVT_',b['event_id']),event_type='UNKNOWN',
            actor=resolve(b.get('owner','')), targets=resolve(b.get('target','')),
            start=b['interval_s'][0],peak=peak,end=b['interval_s'][1],
            world_intent=intent(),screen_intent=intent(),
            result=intent(b['outcome'],'SOURCE','CSP action_beats.outcome') if b.get('outcome') else intent(),source_event=None))
    for c in p['causal_links']:
        g['dependencies'].append(dict(event_id=stable('EVT_',c['reaction_event']),depends_on=stable('EVT_',c['cause_event']),
            condition=intent(c['direction_rule']+'; '+c['strength_rule'],'SOURCE','Explicit CSP causal_links; not inferred from motion')))
    return g


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('csp');ap.add_argument('--output',required=True);args=ap.parse_args()
    g=debug_graph(read_package(args.csp));path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DEBUG / UNKNOWN intent retained; production compilation requires explicit curation')
