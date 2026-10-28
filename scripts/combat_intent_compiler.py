"""Explicit one-on-one intent composition; only existing motion/control/perception APIs."""
import copy,math
from primitive_sampler import add,sub,mul,norm,unit
from motion_intensity import compile_profile
from momentum_transfer import recovery_segment,write_segment,compile_consequence,position
from prop_control import compile_control
from perception_reaction import resolve,attach_csp
from support_contact import sample_offsets
from combat_intent import attach

def compile_intents(csp,plan):
    p=copy.deepcopy(csp);n=p['timebase']['frames'];fps=p['timebase']['fps'];a=plan['attacker'];b=plan['defender'];ar='CHAR_'+a;br='CHAR_'+b;weapon=plan['weapon'];anchor=plan['owner_anchor'];defense=plan['defense_anchor'];region=plan['target_region'];tip=plan['tip_offset'];offset=plan['weapon_root_offset'];initial_weapon=position(p,weapon,1)
    ledger={weapon:[],br:[]};primitives={weapon:[],br:[]};end={weapon:1,br:1};vel={weapon:[0,0,0],br:[0,0,0]};perceptions=[];consequences=[];intents=[];profiles=[]
    control_events=[dict(event_id=plan['id']+'_OWN_CONTACT',frame=1,kind='CONTACT',actor=a,prop_id=weapon),dict(event_id=plan['id']+'_OWN_ACQUIRE',frame=4,kind='ACQUIRE',actor=a,prop_id=weapon,contact_ref=plan['id']+'_OWN_CONTACT')]
    binding=dict(prop_id=weapon,anchors={a:anchor,b:defense},handle_id=plan['handle'],handle_offset=tip,contact_radius=.05,max_reach=1.8,minimum_contact_frames=2,max_speed=plan['maximum_speed'],position_tolerance=.0001,placement_tolerance=.002,release_continuation='HOLD_WORLD',provenance='AUTHOR_EXPLICIT weapon and control-point dimensions; S003 defaults, not anatomical hands')
    akeys=[[1,0]];bkeys=[[1,0]]
    def record(obj,q,f):
        ledger[obj].append(f);primitives[obj].append(q);end[obj]=f['world_samples'][-1]['frame'];vel[obj]=f['exit_state_actual']['velocity']
    def segment(obj,last,v):
        if last==end[obj]:return
        if last<end[obj]:raise ValueError('COMBAT_EVENT_OVERLAP')
        q,f,_=recovery_segment(p,plan['id']+'_'+obj+'_'+str(len(ledger[obj])),obj,end[obj],last,position(p,obj,end[obj]),vel[obj],v)
        write_segment(p,obj,f,True);record(obj,q,f)
    def bridge(obj,goal,last):
        first=end[obj];mid=(first+last)//2;T=(last-first)/fps;peak=mul(sub(goal,position(p,obj,first)),2/T)
        segment(obj,mid,peak);segment(obj,last,[0,0,0])
    def sync():
        for f in range(1,n+1):
            wp=position(p,weapon,f);bp=position(p,br,f)
            p['object_tracks'][ar][f-1]['state']['location']=sub(wp,offset)
            p['object_tracks'][anchor][f-1]['state']['location']=add(wp,tip)
            p['object_tracks'][defense][f-1]['state']['location']=add(bp,plan['region_offset'])
            p['object_tracks'][region][f-1]['state']['location']=add(bp,plan['region_offset'])
    def controls():
        nonlocal p
        sync();p['action_beats']=[x for x in p['action_beats'] if 'prop_control_transition' not in x]
        p['primitive_assets']=[x for x in p['primitive_assets'] if x['id']!=plan['handle']];p['object_tracks'].pop(plan['handle'],None)
        p=compile_control(p,[binding],control_events,{x:[r['state']['location'] for r in p['object_tracks']['CHAR_'+x]] for x in (a,b)})
    for beat in plan['beats']:
        eid=beat['id'];cue=beat['cue_frame'];notice=cue+beat['perception_delay'];response=notice+beat['reaction_delay'];commit=cue+beat['commit_delay'];contact=commit+sum(beat['attack_phase_frames']);stop=contact+beat['stop_frames'];momentum_end=contact+sum(beat['response_frames']);reset_start=max(stop,momentum_end) if beat['result'] in ('BLOCK','HIT') else stop;ready=reset_start+beat['reset_frames'] if beat.get('reset_weapon',True) else momentum_end
        if ready>=n:raise ValueError('COMBAT_OUTSIDE_TIMELINE')
        pb={'schema_version':'PERCEPTION-REACTION/1.0','binding_id':eid+'_PERCEPTION','actor':b,'target':a,'source_event':{'event_id':eid+'_CUE','frame':cue},'perception_event':eid+'_NOTICE','fps':fps,'window':[cue+1,commit],'trigger':{'mode':'EXPLICIT_AUTHOR_TRIGGER','frame':notice,'author_reason':beat['cue_reason']},'reaction_delay_frames':beat['reaction_delay'],'response_steps':[{'event_id':eid+'_DEFENSE','kind':'DEFENSE_TREND','duration_frames':contact-response}],'execution_end_frame':n,'measurement_onset_allowance_frames':6,'provenance':'DIRECTOR_AUTHORED attack cue; not automatic cognition'}
        evidence=[dict(frame=f,actor=b,target=a,actor_exists=True,target_exists=True) for f in range(cue+1,commit+1)];resolution=resolve(pb,evidence)
        if resolution['status']!='READY':raise ValueError('DEFENSE_BEFORE_ATTACK_CUE')
        response=resolution['response_events'][0]['start_frame'];p=attach_csp(p,pb,resolution);perceptions.append({'binding':pb,'resolution':resolution})
        target=add(position(p,br,response),plan['region_offset']);start=initial_weapon[:];direction=unit(beat['direction']);goal=sub(target,tip)
        if beat['result']=='MISS':goal=add(goal,beat['miss_offset'])
        # This scoped compiler accepts fixed +X strike sweeps. Other routes remain explicit unsupported.
        if direction!=[1.,0.,0.] or abs(goal[1]-start[1])>1e-7:raise ValueError('UNSUPPORTED_THREAT_DIRECTION')
        t1=beat['attack_phase_frames'][0]/fps;t2=(beat['attack_phase_frames'][1]-3)/fps;cruise=3/fps;exitv=beat['contact_speed'];peak=(goal[0]-start[0]-exitv*(t2/2+cruise))/((t1+t2)/2)
        segment(weapon,commit,[0,0,0]);profile={'id':eid+'_ATTACK','actor':weapon,'intensity_class':beat['motion_class'],'trend':'LUNGE','direction':direction,'start_position':position(p,weapon,commit),'knots':[{'frame':commit,'speed':0,'phase':'PREPARE'},{'frame':commit+beat['attack_phase_frames'][0],'speed':peak,'phase':'BURST'},{'frame':contact-3,'speed':exitv,'phase':'DECELERATE'},{'frame':contact,'speed':exitv,'phase':'CRUISE'}],'provenance':'AUTHOR route/time/contact speed; peak DERIVED_FROM_ROUTE_AND_TIMING; S008 relative intensity','facing_yaw':-90}
        compiled=compile_profile(profile,{'fps':fps,'duration':n/fps,'frame_origin':1,'time_unit':'seconds'});profiles.append(compiled)
        for q,f in zip(compiled['primitives'],compiled['bundle']['fragments']):write_segment(p,weapon,f,True);record(weapon,q,f)
        if beat['result']=='EVADE':
            segment(br,response,[0,0,0]);origin=position(p,br,response);bridge(br,add(origin,beat['evade_offset']),response+beat['evade_frames']);segment(br,contact,[0,0,0])
        else:segment(br,contact,[0,0,0]);origin=position(p,br,contact)
        sync()
        if beat['result'] in ('BLOCK','HIT'):
            contact_id=eid+'_CONTACT';control_events.append(dict(event_id=contact_id,frame=contact,kind='CONTACT',actor=b,prop_id=weapon));controls()
            mc=dict(transfer_id=eid+'_CONSEQUENCE',mode='IMPACT_RESPONSE',source=weapon,receiver=br,actor=b,actor_root=br,prop=weapon,contact_ref=contact_id,acquire_ref=None,first_frame=contact,response_end_frame=contact+beat['response_frames'][0],source_stop_frame=stop,recovery_end_frame=momentum_end,response_gain=beat['response_gain'],reason=beat['result']+' director-level contact consequence',provenance='EXPLICIT_COMBAT_INTENT, not impulse/mass solver',limits=plan['momentum_limits'])
            p,bundle=compile_consequence(p,mc)
            resolved=next(x['momentum_transfer'] for x in p['action_beats'] if x['event_id']==mc['transfer_id']);consequences.append(resolved)
            for q,f in zip(bundle['primitives'],bundle['fragments']):record(f['affected_entity'],q,f)
        else:
            contact_id=None;segment(weapon,stop,[0,0,0]);segment(br,stop,[0,0,0])
        if beat.get('reset_weapon',True):
            segment(weapon,reset_start,[0,0,0]);bridge(weapon,initial_weapon,ready)
        else:segment(weapon,ready,[0,0,0])
        if beat['result']=='EVADE':bridge(br,origin,ready)
        elif end[br]<ready:segment(br,ready,[0,0,0])
        sync();controls()
        path=[{'frame':r['frame'],'position':r['position']} for r in compiled['rows']]
        c={'id':eid,'attacker':a,'defender':b,'weapon':weapon,'result':beat['result'],'attack_intensity':beat['attack_intensity'],'cue_frame':cue,'notice_frame':notice,'defense_frame':response,'commit_frame':commit,'contact_frame':contact,'contact_window':[contact-3,contact+3],'source_stop_frame':stop,'recovery_end':ready,'perception_event':pb['perception_event'],'defense_ref':pb['perception_event'],'defense_trend':'DODGE' if beat['result']=='EVADE' else 'BLOCK_ATTEMPT' if beat['result']=='BLOCK' else 'DEFEND_PREPARE','attack_contact_event':contact_id,'response_event':eid+'_CONSEQUENCE' if contact_id else None,'momentum_source':contact_id,'threat_route':{'attacker':a,'target':b,'origin':add(start,tip),'direction':direction,'path':path,'target_point':target,'target_region':region,'speed_intensity':beat['attack_intensity'],'start_frame':commit,'commit_frame':commit,'contact_or_miss_window':[contact-3,contact+3],'terminal_direction':direction,'tracking_authorized':False},'limits':plan['limits'],'initiative_policy':'attacker commits; defender reacts; result resolves to neutral unless explicit later beat changes initiative','provenance':'DIRECTOR_AUTHORED technical combat intent'}
        p=attach(p,c);intents.append(c)
        akeys.extend([[cue,0],[commit,3],[contact,7],[stop,2],[ready,0]])
        bkeys.extend([[response,0],[response+12,-5],[contact,-5],[momentum_end,0],[ready,0]])
        # A guard bar is an action proxy only, never a new rig or owner.
        for f in range(cue,ready+1):
            p['object_tracks'][defense][f-1]['state']['hide_render']=beat['result']!='BLOCK' or f<response or f>momentum_end
    segment(weapon,n,[0,0,0]);segment(br,n,[0,0,0]);sync();controls()
    p['actor_pose_tracks']={actor:[{'frame':f,'state':{'position':position(p,'CHAR_'+actor,f),'yaw':-90 if actor==a else 90,'grounded':True,'body_pitch':sample_offsets(keys,f)[0]}} for f in range(1,n+1)] for actor,keys in [(a,akeys),(b,bkeys)]}
    # The fresh Builder owns actor root placement; canonical planned positions stay in compiler evidence.
    planned={obj:[r['state']['location'] for r in p['object_tracks'][obj]] for obj in (ar,br)}
    p['object_tracks'].pop(ar);p['object_tracks'].pop(br)
    return p,{'plan':plan,'intents':intents,'perceptions':perceptions,'consequences':consequences,'profiles':profiles,'fragments':ledger,'primitives':primitives,'planned_actor_positions':planned,'scope':'Fixed-axis authored attacks; no target chasing, tactics, physics or AG auto-lowering'}


