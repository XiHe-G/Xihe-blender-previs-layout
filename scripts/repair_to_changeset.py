"""Approval-bound execution re-lowering; the director's Plan is immutable."""
from copy import deepcopy
from s2_common import digest,schema_check,projection

def validate_decision(proposal,decision,csp=None):
    schema_check(proposal,'repair-proposal.schema.json');schema_check(decision,'repair-decision.schema.json')
    if decision['proposal_id']!=proposal['proposal_id'] or decision['proposal_sha256']!=digest(proposal):raise ValueError('STALE_REPAIR_DECISION')
    r=proposal['source_checker_result']['result']
    from repair_proposal_generator import SUPPORTED,CODES
    if r['type'] not in SUPPORTED or r['code']!=CODES[r['type']] or proposal['problem_type']!=r['type'] or proposal['source_author_id']!=r['source_author_id']:raise ValueError('INELIGIBLE_REPAIR_TYPE_OR_SOURCE')
    if digest(r)!=proposal['source_checker_result']['result_sha256'] or r['status']!='FAIL' or r['evidence_sufficiency']['level']!='ENOUGH' or not r.get('evidence'):raise ValueError('INELIGIBLE_REPAIR_RESULT')
    if r['plan'].get('requirement_source')=='INFERRED' or r['plan'].get('confidence')=='LOW':raise ValueError('INELIGIBLE_REPAIR_REQUIREMENT')
    if any(proposal['repair_goal'].get(k)!=r['plan'].get(k) for k in ['expected_state','expected_range','behavior_profile']):raise ValueError('REPAIR_MUST_PRESERVE_PLAN')
    if decision['decision'] not in ('APPROVE','APPROVE_WITH_MODIFICATION'):raise ValueError('HUMAN_APPROVAL_REQUIRED: '+decision['decision'])
    if decision['authority']['kind']!='HUMAN_USER_MESSAGE':raise ValueError('SYNTHETIC_DECISION_CANNOT_EXECUTE')
    candidates=[s for s in proposal['candidate_strategies'] if s['strategy_id']==decision['selected_strategy']]
    if len(candidates)!=1:raise ValueError('INVALID_SELECTED_STRATEGY')
    strategy=candidates[0]
    if not set(strategy['preserve']).issubset(decision['protected_content']):raise ValueError('PROTECTED_CONTENT_REMOVED')
    if not decision['allowed_scope'] or set(decision['allowed_channels'])!={s['channel'] for s in decision['allowed_scope']}:raise ValueError('INVALID_ALLOWED_CHANNELS')
    if csp is not None:
        if digest(csp)!=proposal['csp_sha256']:raise ValueError('STALE_REPAIR_CSP')
        if not set(projection(csp,decision['allowed_scope'])).issubset(projection(csp,strategy['modify'])):raise ValueError('DECISION_SCOPE_EXCEEDS_STRATEGY')
    blocked=[l for l in proposal['protected_overrides'] if l['strategy_id']==strategy['strategy_id']]
    resolution=decision['override_resolution']
    releases={x['override_id'] for x in (resolution or {}).get('resolutions',[]) if x['decision'] in ('RELEASE','REPLACE_LOCK')}
    if any(x['override_id'] not in releases for x in blocked):raise ValueError('BLOCKED_BY_OVERRIDE')
    return strategy

def to_changeset(graph,proposal,decision,csp=None):
    validate_decision(proposal,decision,csp)
    if digest(graph)!=proposal['graph_sha256']:raise ValueError('STALE_REPAIR_GRAPH')
    t=proposal['lowering_target'];table,key=('shot_intents','shot_id') if t['change_type']=='SHOT_INTENT_CHANGE' else ('events','event_id')
    row=next(x for x in graph[table] if x[key]==t['target']);value=deepcopy(row[t['channel']])
    change=dict(change_id='RELOWER_'+proposal['proposal_id'],change_type=t['change_type'],target=t['target'],channel=t['channel'],old_value=value,new_value=deepcopy(value),requested_by=decision['authority']['author'],provenance='Execution-only repair; unchanged author value. Proposal '+proposal['proposal_id']+' / Decision '+decision['decision_id'])
    cs=dict(changeset_version='CHANGESET/1.0',changeset_id='CS_'+decision['decision_id'],base_graph_id=graph['graph_id'],base_graph_sha256=digest(graph),author=decision['authority']['author'],reason=decision['director_note'],changes=[change],execution_repair=dict(mode='RELOWER_UNCHANGED_PLAN',proposal=deepcopy(proposal),decision=deepcopy(decision),proposal_id=proposal['proposal_id'],decision_id=decision['decision_id']))
    schema_check(cs,'changeset.schema.json');return cs

def validate_relower(graph,cs):
    ctx=cs['execution_repair'];expected=to_changeset(graph,ctx['proposal'],ctx['decision'])
    if digest(cs)!=digest(expected):raise ValueError('TAMPERED_REPAIR_CHANGESET')

def validate_execution_authorization(base,patch,graph,updated,cs,binding,registry,resolution):
    ctx=cs['execution_repair'];p=ctx['proposal'];d=ctx['decision'];validate_decision(p,d,base)
    if digest(binding)!=p['execution_binding_sha256'] or digest(registry)!=p['override_registry_sha256']:raise ValueError('STALE_REPAIR_CONTEXT')
    if digest(resolution)!=digest(d['override_resolution']):raise ValueError('UNAPPROVED_OVERRIDE_RESOLUTION')
    compare=deepcopy(updated)
    # Only explicit override workflow status can differ; all director semantic fields stay identical.
    for lock in compare['overrides']:
        original=next(o for o in graph['overrides'] if o['override_id']==lock['override_id'])
        if lock['status']!=original['status']:
            ids={r['override_id'] for r in (resolution or {}).get('resolutions',[]) if r['decision'] in ('RELEASE','REPLACE_LOCK')}
            if lock['override_id'] not in ids:raise ValueError('UNAPPROVED_OVERRIDE_CHANGE')
            lock['status']=original['status']
    if digest(compare)!=digest(graph):raise ValueError('REPAIR_MUST_PRESERVE_PLAN')
    allowed=set(projection(base,d['allowed_scope']))
    if any(op['path'] not in allowed for op in patch['execution_payload']):raise ValueError('PATCH_OUTSIDE_HUMAN_APPROVAL')

def scope_comparison(proposal,decision,scope,csp):
    estimated=set(projection(csp,decision['allowed_scope']));actual=set(scope['allowed_paths'])
    return dict(status='WARNING' if actual-estimated or estimated-actual else 'PASS',estimated_path_count=len(estimated),s2_path_count=len(actual),additional_s2_paths=len(actual-estimated),unavailable_estimated_paths=len(estimated-actual),dependent_events=scope['dependent_events'],policy='Patch must satisfy intersection of S2 scope and human approval; estimates never expand authority')

if __name__=='__main__':
    import argparse
    from s2_common import read,write
    from combat_sequence_package import read_package
    ap=argparse.ArgumentParser()
    for field in ['graph','proposal','decision','csp','output']:ap.add_argument('--'+field,required=True)
    a=ap.parse_args();write(a.output,to_changeset(read(a.graph),read(a.proposal),read(a.decision),read_package(a.csp)));print('APPROVED_RELOWER_CHANGESET; no execution patch generated')
