import copy
import math
import unittest
from action_expression import compile_travel, compile_impact, full_track, patch_csp, contact_evidence
from action_readability import measure_readability

TB={'fps':30,'frames':121}


def travel():
    return dict(id='DASH',actor='A',body_height=2,meters_per_unit=1,boundary_policy='AUTHORED_SPEED_ENVELOPE',
                points=[[0,0,0],[12,0,0]],provenance='authored test',
                speed_knots=[dict(frame=f,weight=w,phase=p) for f,w,p in
                             [(11,0,'PREPARE'),(15,0,'PREPARE'),(21,1,'BURST'),(39,1,'CRUISE'),(51,0,'DECELERATE')]],
                pose_channels={'body_pitch':[dict(frame=f,value=v) for f,v in [(11,0),(15,15),(21,32),(39,32),(51,0)]]})


def impact():
    return dict(id='HIT',actor='B',body_height=2,meters_per_unit=1,provenance='authored hit',boundary_policy='AUTHORED_SPEED_ENVELOPE',
                contact=dict(event_id='CONTACT',frame=31,source_actor='A',target_actor='B'),
                start_position=[1,0,0],direction=[1,0,0],response_kind='SLIDE',response_speed_hps=3,
                phase_frames=[31,34,40,64],facing={'mode':'FIXED','yaw_deg':90},
                pose_channels={'body_pitch':[dict(frame=f,value=v) for f,v in [(31,0),(34,-30),(44,-18),(54,6),(64,0)]]})


def source():return [dict(frame=30,position=[0,0,1],actor='A'),dict(frame=31,position=[.2,0,1],actor='A')]


class ExpressionTests(unittest.TestCase):
    def test_exact_route_end_and_duration(self):
        c=compile_travel(travel(),TB)
        self.assertEqual(c['rows'][0]['state']['position'],[0,0,0])
        self.assertEqual(c['rows'][-1]['state']['position'],[12,0,0])
        self.assertAlmostEqual(c['metrics']['duration_s'],40/30)
        self.assertGreater(c['metrics']['peak_speed_body_heights_s'],5)
    def test_shorter_time_has_meaningful_gain(self):
        fast=travel();slow=copy.deepcopy(fast)
        for k in slow['speed_knots']:k['frame']=11+(k['frame']-11)*2
        for k in slow['pose_channels']['body_pitch']:k['frame']=11+(k['frame']-11)*2
        a=compile_travel(fast,TB);b=compile_travel(slow,TB)
        self.assertAlmostEqual(a['metrics']['peak_speed_units_s']/b['metrics']['peak_speed_units_s'],2)
    def test_units_and_actor_scale(self):
        a=travel();b=copy.deepcopy(a);b['body_height']*=100;b['meters_per_unit']=.01
        b['points']=[[x*100 for x in p] for p in b['points']]
        x=compile_travel(a,TB)['metrics'];y=compile_travel(b,TB)['metrics']
        self.assertAlmostEqual(x['peak_speed_m_s'],y['peak_speed_m_s'])
        self.assertAlmostEqual(x['peak_speed_body_heights_s'],y['peak_speed_body_heights_s'])
    def test_fps_conversion(self):
        a=travel();b=copy.deepcopy(a)
        for keys in [b['speed_knots'],*b['pose_channels'].values()]:
            for k in keys:k['frame']=1+(k['frame']-1)*2
        self.assertAlmostEqual(compile_travel(a,TB)['metrics']['peak_speed_units_s'],compile_travel(b,dict(fps=60,frames=241))['metrics']['peak_speed_units_s'])
    def test_cinematic_range_conflict_rejected(self):
        s=travel();s['peak_speed_range_hps']=[20,30]
        with self.assertRaisesRegex(ValueError,'CONFLICT'):compile_travel(s,TB)
    def test_arbitrary_direction(self):
        s=travel();s['points']=[[0,0,0],[0,12,0]]
        c=compile_travel(s,TB);self.assertAlmostEqual(c['rows'][10]['state']['yaw'],0)
    def test_curved_route_turns_without_teleport(self):
        s=travel();s.update(path_type='BEZIER_SIMPLE',points=[[0,0,0],[5,0,0],[8,3,0],[8,8,0]])
        c=compile_travel(s,TB)
        self.assertAlmostEqual(c['rows'][0]['state']['yaw'],-90,delta=.2)
        self.assertAlmostEqual(c['rows'][-1]['state']['yaw'],0,delta=.2)
        self.assertTrue(all(math.dist(a['state']['position'],b['state']['position'])<1 for a,b in zip(c['rows'],c['rows'][1:])))
    def test_input_preserved_and_old_scalar_kernel_used(self):
        s=travel();before=copy.deepcopy(s);c=compile_travel(s,TB)
        self.assertEqual(s,before)
        self.assertTrue(all(f['metadata']['primitive_type']=='RECOVERY_PROFILE' for f in c['kernel_evidence']['fragments']))
    def test_fast_profile_does_not_hide_legacy_diagnostic(self):
        s=travel();c=compile_travel(s,TB)
        self.assertTrue(any(f['continuity_report']['dimensions']['C1']=='FAIL' for f in c['kernel_evidence']['fragments']))
        self.assertEqual(c['analytic_scalar_c0_c1'],'PASS')
        s['boundary_policy']='LEGACY_STRICT'
        with self.assertRaisesRegex(ValueError,'LEGACY_C1'):compile_travel(s,TB)
    def test_nonfinite_and_negative_inputs(self):
        for value in [float('nan'),-1]:
            s=travel();s['speed_knots'][2]['weight']=value
            with self.assertRaises(ValueError):compile_travel(s,TB)
    def test_flight_not_silently_grounded(self):
        s=travel();s['points'][-1][2]=5
        with self.assertRaisesRegex(ValueError,'PLANAR'):compile_travel(s,TB)
    def test_pose_lag_independent(self):
        s=travel();s['pose_channels']['head_pitch']=[dict(frame=f,value=v) for f,v in [(11,0),(23,0),(27,-10),(51,0)]]
        c=compile_travel(s,TB);r=next(r for r in c['rows'] if r['frame']==21)['state']
        self.assertEqual(r['body_pitch'],32);self.assertEqual(r['head_pitch'],0)
    def test_recoil_displacement_and_recovery(self):
        c=compile_impact(impact(),TB,source())
        self.assertGreater(c['rows'][-1]['state']['position'][0]-1,3)
        self.assertEqual(c['exit_speed'],0)
        self.assertEqual(c['rows'][-1]['state']['body_pitch'],0)
        self.assertTrue(c['planned_contact_only'])
    def test_reaction_strength_is_visible_in_displacement(self):
        s=impact();strong=compile_impact(s,TB,source());s['response_speed_hps']=.5
        weak=compile_impact(s,TB,source())
        self.assertAlmostEqual(strong['metrics']['route_length']/weak['metrics']['route_length'],6)
    def test_arbitrary_impact_axis(self):
        s=impact();s['direction']=[0,1,0];s['redirect_reason']='authored deflection'
        c=compile_impact(s,TB,source());self.assertGreater(c['rows'][-1]['state']['position'][1],3)
    def test_contact_missing_wrong_actor_and_idle_source(self):
        for rows in [[],[dict(r,actor='C') for r in source()],[dict(r,position=[0,0,1]) for r in source()]]:
            with self.assertRaises(ValueError):compile_impact(impact(),TB,rows)
    def test_reaction_does_not_precede_contact(self):
        c=compile_impact(impact(),TB,source());rows=full_track(c,121)
        self.assertTrue(all(r['state']['position']==[1,0,0] for r in rows[:31]))
    def test_moving_endpoint_cannot_be_frozen(self):
        s=travel();s['speed_knots'][-1]['weight']=1;c=compile_travel(s,TB)
        with self.assertRaisesRegex(ValueError,'CONTINUATION'):full_track(c,121)
    def test_contact_requires_native_witness(self):
        self.assertEqual(contact_evidence([],31,.1)['status'],'NOT_REVIEWED')
        self.assertEqual(contact_evidence([dict(frame=31,source_point=[0,0,0],target_point=[1,0,0])],31,.1)['status'],'FAIL')
    def test_scope_and_camera_preservation(self):
        c=compile_travel(travel(),TB);track=full_track(c,121)
        p=dict(layout_mode='COMBAT_DYNAMIC',timebase=TB,actor_pose_tracks={'A':track,'B':copy.deepcopy(track)},object_tracks={'CAM':[1,2,3]},review_gates={'RECOVERY':{'status':'PASS'}})
        out=patch_csp(p,c,allowed_actors=['A'])
        self.assertEqual(out['object_tracks'],p['object_tracks']);self.assertEqual(out['actor_pose_tracks']['B'],p['actor_pose_tracks']['B'])
        self.assertEqual(out['review_gates']['RECOVERY']['status'],'NOT_REVIEWED');self.assertEqual(p['review_gates']['RECOVERY']['status'],'PASS')
        with self.assertRaisesRegex(ValueError,'LOCK'):patch_csp(p,c,allowed_actors=['A'],locked_channels={'A':['position']})
    def test_cannot_silently_move_existing_endpoint(self):
        c=compile_travel(travel(),TB);p=dict(layout_mode='COMBAT_DYNAMIC',timebase=TB,actor_pose_tracks={'A':full_track(c,121)})
        broken=copy.deepcopy(c);broken['rows'][-1]['state']['position'][0]+=1
        with self.assertRaisesRegex(ValueError,'BOUNDARY'):patch_csp(p,broken,allowed_actors=['A'])
    def test_tracking_camera_context_not_false_failure(self):
        rows=[dict(frame=i+1,shot_id='S',position=[i,0,0],visible=True,center_uv=[.5,.5],height_uv=.3,landmark_uv={'P':[.7-i*.01,.5]}) for i in range(6)]
        m=measure_readability(rows,30,2)
        self.assertEqual(m['actor_screen_uv_s']['peak'],0);self.assertGreater(m['landmark_screen_uv_s']['peak'],.2)
        self.assertEqual(m['visual_review'],'NOT_REVIEWED')
    def test_cut_not_counted_as_speed(self):
        rows=[dict(frame=1,shot_id='A',position=[0,0,0],visible=True),dict(frame=2,shot_id='B',position=[100,0,0],visible=True)]
        m=measure_readability(rows,30,2);self.assertEqual(m['cut_pairs_excluded'],1);self.assertIsNone(m['world_speed_units_s'])
    def test_out_of_frame_cannot_pass_visual_review(self):
        rows=[dict(frame=i+1,position=[i,0,0],visible=False,center_uv=[2,.5]) for i in range(4)]
        m=measure_readability(rows,30,2);self.assertEqual(m['visible_pair_fraction'],0);self.assertIsNone(m['actor_screen_uv_s'])


if __name__=='__main__':unittest.main()
