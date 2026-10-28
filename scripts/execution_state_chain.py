"""State inheritance from explicit facts and S51 actual exits; no motion generation."""
import copy,math
from primitive_sampler import sample_track,unit,yaw_quat,norm,sub,qangle,sha
from lowering_validator import parse_evidence,record,StopLowering,need

class ExecutionStateChain:
    def __init__(self,graph,context):self.graph=graph;self.context=context;self.entries=[];self.links=[]
    def initial(self,actor,p):
        entity=next(e for e in self.graph['entities'] if e['id']==actor);facts,confidence=parse_evidence(entity['persistent_state'])
        if not all(k in facts for k in ('position','velocity','heading_degrees','at_time')):need(p,'entity_initial_state(position,velocity,heading_degrees,at_time)')
        if confidence=='LOW':raise StopLowering('NEEDS_AUTHOR_INPUT','LOW_CONFIDENCE_ENTITY_STATE',['confirmed_initial_state'])
        st=dict(position=facts['position'],velocity=facts['velocity'],movement_direction=unit(facts['velocity']),orientation=yaw_quat(math.radians(facts['heading_degrees'])),angular_velocity=0.,ownership_state=facts.get('ownership','FREE'),support_state=facts.get('support','UNSPECIFIED'))
        return st,facts['at_time'],actor+'.persistent_state'
    def entry(self,actor,event,channel,p,explicit=None,recovery=False):
        t=event['start'];st,at,origin=self.initial(actor,p);source='ENTITY_STATE';method='INITIAL_FACT'
        active=[x for x in self.entries if x['actor']==actor and any(c in x['channels'] for c in ('ROOT_LOCATION','PROJECTILE_TRANSFORM')) and x['start']<=t]
        previous=max(active,key=lambda x:(min(x['end'],t),x['order'])) if active else None
        if recovery and (not previous or abs(previous['end']-t)>1e-8):need(p,'previous_event_exit_state')
        if previous:
            if previous['end']<t-1e-8 and not (self.context.get('contract_policy')=='S53R/1.0' and norm(previous['fragment']['exit_state_actual']['velocity'])<1e-8):need(p,'state_at_event_start_after_gap')
            rows=previous['fragment']['world_samples'];st.update(position=sample_track(rows,t),velocity=sample_track(rows,t,'velocity'))
            st['ownership_state']=previous['fragment']['exit_state_actual']['ownership_state'] if t>=previous['end'] else st['ownership_state']
            origin=previous['event_id']+'.exit_state' if abs(previous['end']-t)<1e-8 else previous['event_id']+'.evaluated_state_at_'+str(t)
            source='PREVIOUS_EXIT_STATE' if abs(previous['end']-t)<1e-8 else 'DEPENDENCY';method='CONTINUITY_INHERITANCE' if source=='PREVIOUS_EXIT_STATE' else 'EXPLICIT_TRACK_SAMPLE'
        elif abs(t-at)>1e-8:need(p,'initial_state_at_event_start')
        orientation_channel=channel if channel in ('ROOT_ROTATION','BODY_ROTATION','HEAD_ROTATION') else 'ROOT_ROTATION'
        rotations=[x for x in self.entries if x['actor']==actor and orientation_channel in x['channels'] and x['end']<=t+1e-8]
        if rotations:
            r=max(rotations,key=lambda x:x['end']);st['orientation']=r['fragment']['exit_state_actual']['orientation'];st['angular_velocity']=r['fragment']['exit_state_actual']['angular_velocity']
        elif channel in ('BODY_ROTATION','HEAD_ROTATION'):st['orientation']=[1.,0.,0.,0.];st['angular_velocity']=0.
        explicit=explicit or {}
        for k,v in explicit.items():
            if k not in st:raise StopLowering('NEEDS_AUTHOR_INPUT','UNKNOWN_ENTRY_FIELD',[k])
            error=qangle(st[k],v) if k=='orientation' else norm(sub(st[k],v)) if isinstance(v,list) else 0 if st[k]==v else 1
            if error>1e-5:raise StopLowering('BLOCKED_BY_CONSTRAINT','STATE_CONFLICT',[k])
        st['movement_direction']=unit(st['velocity']);p['entry_state']=copy.deepcopy(st)
        facts,_=parse_evidence(next(e for e in self.graph['entities'] if e['id']==actor)['persistent_state'])
        for key,value in st.items():
            src,where,how=source,origin,method
            if key in ('orientation','angular_velocity') and rotations:src,where,how='PREVIOUS_EXIT_STATE',rotations[-1]['event_id']+'.exit_state','CHANNEL_STATE_INHERITANCE'
            elif key in ('orientation','angular_velocity') and channel in ('BODY_ROTATION','HEAD_ROTATION'):src,where,how='TECHNICAL_DEFAULT','neutral local '+channel,'EXPLICIT_NEUTRAL_LOCAL_ENTRY'
            elif source=='ENTITY_STATE' and key=='angular_velocity':src,where,how='TECHNICAL_DEFAULT','initial angular velocity','ZERO_UNLESS_PRIOR_ROTATION'
            elif source=='ENTITY_STATE' and key=='ownership_state' and 'ownership' not in facts:src,where,how='TECHNICAL_DEFAULT','initial unattached state','FREE_DEFAULT'
            elif source=='ENTITY_STATE' and key=='support_state' and 'support' not in facts:src,where,how='TECHNICAL_DEFAULT','initial support','UNSPECIFIED_DEFAULT'
            record(p,'entry.'+key,value,src,where,how,'MEDIUM' if src=='TECHNICAL_DEFAULT' else 'HIGH')
        if recovery and norm(st['velocity'])<1e-6:raise StopLowering('NEEDS_AUTHOR_INPUT','RECOVERY_FROM_STATIC_STATE',['nonzero_previous_exit_velocity'])
        if previous:self.links.append({'from':previous['event_id'],'to':event['event_id'],'at_time':t,'actor':actor,'method':method,'source_sha256':sha(previous['fragment']['exit_state_actual'])})
        return st
    def commit(self,event_id,actor,fragments):
        for f in fragments:self.entries.append({'event_id':event_id,'actor':actor,'channels':f['channel_ownership']['WRITES'],'start':f['time_range'][0],'end':f['time_range'][1],'fragment':f,'order':len(self.entries)})
