"""Attention sequencing diagnostic; no new AG Event type."""
def build_attention_trace(graph,trace,links):
    frames=trace.get('frames',[]);events={e['event_id']:e for e in graph['events']};out=[]
    for link in links:
        source=events.get(link['source_event']);target=events.get(link['target_event'])
        if not source or not target:continue
        out.append({'attention_id':link['attention_id'],'target_entity':link['target_entity'],'notice_event':link['target_event'],'notice_time':target['start'],'head_response_event':link.get('head_response_event'),'body_response_event':link.get('body_response_event'),'ordering_assertion':link['ordering_assertion'],'status':'TRACE_ONLY','source':'DIRECTOR_PLAN / PREFLIGHT','event_type':'DIAGNOSTIC_NOT_AUTHOR_GRAPH_TYPE'})
    return {'schema_version':'ATTENTION-SEQUENCE-TRACE/1.0','events':out,'automatic_lowering':False}
