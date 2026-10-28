import unittest,sys,tempfile,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from director_camera.workflow import *

def example():
    shots=[]
    for i in range(3):
        shots.append(dict(id=str(i),start=1+i*8,end=9+i*8,purpose='recognition',first_focus='speaker',start_read='relationship',end_read='decision',cut_reason='response',source='authored test',events=[dict(id='event'+str(i),frame=4+i*8,observable='head turns')],camera=dict(id='camera'+str(i),lens_mm=40,motion=dict(kind='STATIC_HOLD',start=[0,-4,1.5],aim_start=[0,0,1.5]))))
    return dict(schema='DIRECTOR_PLAN/1',fps=24,start=1,end=25,frame_convention='HALF_OPEN',shots=shots)

class DirectorWorkflowTests(unittest.TestCase):
    def test_actual_local_front_not_assumed_positive_y(self):
        from director_camera.review_contracts import facing_relation
        self.assertEqual(facing_relation([0,-1,0],[2,3,0],[2,0,0])['status'],'WITHIN_REQUESTED_CONE')
        self.assertEqual(facing_relation([0,1,0],[2,3,0],[2,0,0])['status'],'OUTSIDE_REQUESTED_CONE')
    def test_facing_does_not_claim_gaze_or_coincident_direction(self):
        from director_camera.review_contracts import facing_relation
        self.assertEqual(facing_relation([1,0,0],[0,0,0],[0,0,0])['status'],'NOT_REVIEWED')
        self.assertEqual(facing_relation([1,0,0],[0,0,0],[1,0,0])['gaze'],'NOT_REVIEWED')
    def test_facing_invalid_vector_refused(self):
        from director_camera.review_contracts import facing_relation
        with self.assertRaises(ValueError):facing_relation([float('nan'),0,0],[0,0,0],[1,0,0])
    def test_static_waypoint_pan_rejected(self):
        p=example();p['shots'][0]['camera']['motion']['aim_waypoints']=[[0,[0,0,1.5]],[.5,[1,0,1.5]],[1,[0,0,1.5]]]
        with self.assertRaises(ValueError):validate_plan(p)
    def test_static_evaluated_rotation_fails(self):
        from director_camera.editing import motion_contract
        self.assertEqual(motion_contract([[0,0,0],[0,0,0]],24,'STATIC_HOLD',[[1,0,0,0],[.70710678,0,0,.70710678]])['status'],'FAIL')
    def test_static_without_orientation_limits_claim(self):
        from director_camera.editing import motion_contract
        r=motion_contract([[0,0,0],[0,0,0]],24,'STATIC_HOLD')
        self.assertEqual(r['orientation_status'],'NOT_REVIEWED');self.assertEqual(r['scope'],'TRANSLATION_ONLY')
    def test_valid_static_dialogue_needs_no_motion(self):self.assertEqual(validate_plan(example())['technical'],'PLAN_VALID')
    def test_missing_story_decision_rejected(self):
        p=example();del p['shots'][0]['purpose']
        with self.assertRaises(ValueError):validate_plan(p)
    def test_gap_rejected(self):
        p=example();p['shots'][1]['start']+=1
        with self.assertRaises(ValueError):validate_plan(p)
    def test_cut_not_camera_flight(self):
        p=example();p['shots'][1]['camera']['id']='camera0'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_bad_fps(self):
        for f in [0,-2,float('nan'),True]:
            p=example();p['fps']=f
            with self.assertRaises(ValueError):validate_plan(p)
    def test_wrong_convention(self):
        p=example();p['frame_convention']='INCLUSIVE'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_integer_required(self):
        p=example();p['shots'][0]['start']=1.0
        with self.assertRaises(ValueError):validate_plan(p)
    def test_event_at_exclusive_end_rejects(self):
        p=example();p['shots'][0]['events'][0]['frame']=9
        with self.assertRaises(ValueError):validate_plan(p)
    def test_static_position_cannot_drift(self):
        p=example();p['shots'][0]['camera']['motion']['end']=[1,-4,1.5]
        with self.assertRaises(ValueError):validate_plan(p)
    def test_complex_move_requires_reason(self):
        p=example();p['shots'][0]['camera']['motion']['kind']='ORBIT'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_encoded_schedule_has_cut_and_event_window(self):
        s=review_schedule(example());self.assertEqual(s['cut_pairs'],[[8,9],[16,17]]);self.assertIn(4,s['shots'][0]['frames']);self.assertEqual(s['playback']['status'],'NOT_REVIEWED')
    def test_halfopen_does_not_invalidate_next(self):self.assertEqual(invalidation(example(),[dict(channel='camera',frames=[1,9])])['render'],['0'])
    def test_persistent_actor_affects_later_shots(self):self.assertEqual(invalidation(example(),[dict(channel='action',frames=[6,8],persistent=True)])['render'],['0','1','2'])
    def test_known_reset_limits_dependency(self):self.assertEqual(invalidation(example(),[dict(channel='prop',frames=[2,3],persistent=True,reset_frame=9)])['render'],['0'])
    def test_missing_dependency_expands(self):self.assertEqual(invalidation(example(),[dict(channel='camera',frames=[10,11],dependency_complete=False)])['render'],['0','1','2'])
    def test_caption_does_not_render(self):self.assertEqual(invalidation(example(),[dict(channel='caption',frames=[1,25])])['render'],[])
    def test_empty_change_rejects(self):
        with self.assertRaises(ValueError):invalidation(example(),[dict(channel='camera',frames=[4,4])])
    def test_persisted_budget_survives_cause_rename_and_limit_increase(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json'
            reserve_attempt(p,'p','issue','framing','encoded f4',['CAMERA'],2)
            reserve_attempt(p,'p','issue','new name','encoded f5',['CAMERA'],20)
            with self.assertRaises(ValueError):reserve_attempt(p,'p','issue','again','encoded f6',['CAMERA'],20)
            self.assertEqual(len(json.loads(p.read_text())),2)
    def test_parallel_writer_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json';Path(str(p)+'.lock').touch()
            with self.assertRaises(FileExistsError):reserve_attempt(p,'p','i','c','f4',['CAMERA'])
    def test_cross_channel_experiment_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):reserve_attempt(Path(d)/'l.json','p','i','c','f4',['CAMERA','ACTION'])
    def test_hash_bound_reuse_and_stale_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'clip.mp4';p.write_bytes(b'fixture')
            r=dict(media_sha256=file_sha(p),scene_fingerprint='version',frames=24,fps=24,technical='PASS')
            self.assertTrue(verify_reuse(p,r,'version',24,24));self.assertFalse(verify_reuse(p,r,'other',24,24));p.write_bytes(b'changed');self.assertFalse(verify_reuse(p,r,'version',24,24))

if __name__=='__main__':unittest.main()
