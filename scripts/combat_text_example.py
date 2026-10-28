"""Generate a TEXT-entry interface example, NOT a fixed fight choreography.
python this.py --output sequence.csp.json
Then use the SAME combat_sequence_builder.py as reference packages.
"""
import argparse,json,math
from pathlib import Path
from combat_sequence_package import PHASES,LIFECYCLE,GATES,validate

def make():
    fps=30;n=60
    def state(loc=(0,0,0),rot=(0,0,0),scale=(1,1,1),visible=True,lens=None):
        r=dict(location=list(loc),rotation_mode='XYZ',rotation=list(rot),scale=list(scale),hide_render=not visible,hide_viewport=not visible)
        if lens:r['lens']=lens
        return r
    def stage(w,reason='This launch has no impact target'):return dict(status='APPLIES',interval_s=w) if w else dict(status='NA',reason=reason)
    def smooth(a,b,t):
        x=max(0,min(1,(t-a)/(b-a)));return x*x*(3-2*x)
    def camera(x,y,z):
        dx,dy,dz=-x,-y,1-z
        return state((x,y,z),(math.atan2(math.hypot(dx,dy),-dz),0,-math.atan2(dx,dy)),lens=45)
    p={'schema_version':'CSP/1.0','sequence_id':'TEXT_INTERFACE_EXAMPLE','layout_mode':'COMBAT_DYNAMIC','entry_mode':'TEXT',
        'provenance':{'authority':'DESIGN','scope':'Executable interface demonstration only; replace with approved project beats and trajectories'},
        'timebase':{'fps':fps,'frames':n,'frame_origin':1,'unit':'meter','up_axis':'+Z','forward_axis':'+Y'},'render':{'width':960,'height':540},
        'shot_plan':[dict(id='S1',first_frame=1,end_frame_exclusive=31,camera_id='CAM_1',summary='Compress, launch, recoil'),dict(id='S2',first_frame=31,end_frame_exclusive=61,camera_id='CAM_2',summary='Same projectile exits while body recovers')],
        'actor_assets':[{'id':'A','spec':{'id':'A','height':1.8,'color':[.15,.62,.72],'width_ratio':.26}}],
        'actors':[{'id':'A','root':'CHAR_A','style':'COMBAT_BOX_4','meshes':['A__HEAD','A__NOSE','A__UPPER','A__LOWER'],'pose_channels':['A__LOWER_CTRL','A__BODY_CTRL','A__HEAD_CTRL']}],
        'primitive_assets':[{'id':'FLOOR','type':'CUBE','color':[.5,.53,.58],'state':state((0,1,-.1),scale=(9,10,.2))},{'id':'SCALE_POST','type':'CUBE','color':[.32,.34,.4],'state':state((2,3,1),scale=(.2,.2,2))},{'id':'BALL','type':'SPHERE','color':[.8,.3,.12]},{'id':'CAM_1','type':'CAMERA'},{'id':'CAM_2','type':'CAMERA'}],
        'object_tracks':{'BALL':[],'CAM_1':[],'CAM_2':[]},'actor_pose_tracks':{'A':[]},
        'action_beats':[dict(event_id='LAUNCH_01',owner='A',target='open space',interval_s=[0,2],outcome='Forward launch and recoil; no invented contact',breakdowns=[0,.3,.5,.67,.8,1,1.3,1.7,2],phases={k:stage(w) for k,w in zip(PHASES,[[0,.3],[.3,.5],[.5,.67],[.67,.8],None,[.8,1.3],[1.3,2]])})],
        'rhythm_map':[dict(interval_s=[0,.5],label='coil'),dict(interval_s=[.5,.8],label='burst'),dict(interval_s=[.8,2],label='follow and recover')],
        'causal_links':[],
        'screen_targets':[{'shot_id':s,'authority':'DESIGN','key_states':[{'time_s':t,'A':{'center_uv':[.5,.5],'size_uv':[.2,.6]}}],'major_occlusion':'none; floor and side post provide scale','screen_direction':'projectile moves toward upper-depth; A remains visible'} for s,t in [('S1',0),('S2',1)]],
        'camera_choreography':[{'shot_id':s,'states':[dict(state='Hold',interval_s=w,trigger='Observe launch/recovery',delay_s=0,entry_speed=0,exit_speed=0,framing_goal='Keep body and projectile release corridor visible')]} for s,w in [('S1',[0,1]),('S2',[1,2])]],
        'proxy_lifecycles':[dict(id='BALL',event_id='LAUNCH_01',role='VFX_MOTION_PROXY',owner='A',target='open space',visible_intervals_s=[[.3,1.8]],stages={k:stage(w,'Near miss / no separate impact or expansion') for k,w in zip(LIFECYCLE,[[.3,.4],[.4,.67],[.67,1.7],None,None,[1.7,1.8]])},end_state='HIDDEN_AFTER_EXIT')],
        'continuity_states':[dict(cut_frame=31,before_frame=30,after_frame=31,active_event_ids=['LAUNCH_01'],state_evidence='Same actor_pose_tracks and BALL object track through both cameras',phase_state={'LAUNCH_01':['FOLLOW_THROUGH']},ownership={'BALL':'A'})],
        'review_gates':{g:{'status':'NOT_REVIEWED','evidence':'Interface example requires project-specific visual review'} for g in GATES}}
    for f in range(1,n+1):
        t=(f-1)/fps;coil=smooth(.1,.5,t);burst=smooth(.5,.7,t);recover=smooth(.85,1.9,t)
        p['actor_pose_tracks']['A'].append({'frame':f,'state':{'position':[0,-.18*burst+.18*recover,0],'grounded':True,'body_pitch':24*coil-40*burst+16*recover,'lower_pitch':8*coil-8*recover,'head_pitch':-6*coil+6*recover,'compression':1-.22*coil+.17*burst+.05*recover}})
        y=.65+max(0,t-.67)**1.25*6;r=(.06+.14*smooth(.3,.67,t))*(1-smooth(1.7,1.8,t))
        p['object_tracks']['BALL'].append({'frame':f,'state':state((0,y,1.25),scale=(max(.001,r),)*3,visible=.3<=t<1.8)})
        for name,xyz in [('CAM_1',(3,-7,3)),('CAM_2',(4,-6,2.5))]:p['object_tracks'][name].append({'frame':f,'state':camera(*xyz)})
    errors=validate(p);assert not errors,errors
    return p

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();Path(args.output).write_text(json.dumps(make(),ensure_ascii=False,indent=2),encoding='utf-8')
