"""Behavioral checks for CSP failures and regression sensitivity. No bpy needed."""
import copy,unittest
from combat_text_example import make
from combat_sequence_package import validate
from combat_regression_check import compare

class PackageTests(unittest.TestCase):
    def setUp(self):self.p=make()
    def test_text_entry_valid(self):self.assertEqual(validate(self.p),[])
    def test_source_uses_same_contract(self):
        self.p['entry_mode']='SOURCE';self.assertEqual(validate(self.p),[])
    def test_cut_gap_rejected(self):
        self.p['shot_plan'][1]['first_frame']+=1;self.assertTrue(any('Gap' in x for x in validate(self.p)))
    def test_missing_recovery_not_silently_hold(self):
        del self.p['action_beats'][0]['phases']['RECOVERY'];self.assertTrue(any('RECOVERY' in x for x in validate(self.p)))
    def test_nonfinite_path_rejected(self):
        self.p['object_tracks']['BALL'][15]['state']['location'][0]=float('nan');self.assertTrue(any('Non-finite' in x for x in validate(self.p)))
    def test_cut_event_reset_rejected(self):
        self.p['continuity_states'][0]['active_event_ids']=['NEW_BALL_AT_CUT'];self.assertTrue(any('continuity event' in x for x in validate(self.p)))
    def test_unknown_camera_state_rejected(self):
        self.p['camera_choreography'][0]['states'][0]['state']='MAGIC_FOLLOW';self.assertTrue(any('camera state' in x for x in validate(self.p)))
    def test_missing_lifecycle_rejected(self):
        del self.p['proxy_lifecycles'][0]['stages']['Spawn'];self.assertTrue(any('Lifecycle missing' in x for x in validate(self.p)))
    def test_na_requires_explanation(self):
        self.p['action_beats'][0]['phases']['CONTACT']={'status':'NA'};self.assertTrue(any('NA needs reason' in x for x in validate(self.p)))
    def test_causal_cycle_rejected(self):
        self.p['causal_links']=[dict(cause_event='LAUNCH_01',reaction_event='LAUNCH_01',trigger_s=.5,response_s=.6,direction_rule='forward',strength_rule='recoil')]
        self.assertTrue(any('cycle' in x for x in validate(self.p)))
    def test_reaction_before_release_rejected(self):
        b=copy.deepcopy(self.p['action_beats'][0]);b['event_id']='REACTION';self.p['action_beats'].append(b)
        self.p['causal_links']=[dict(cause_event='LAUNCH_01',reaction_event='REACTION',trigger_s=.7,response_s=.4,direction_rule='forward',strength_rule='recoil')]
        self.assertTrue(any('before trigger' in x for x in validate(self.p)))
    def test_review_cannot_pass_without_evidence(self):
        self.p['review_gates']['SILENT_REVIEW']={'status':'PASS'};self.assertTrue(any('Gate needs evidence' in x for x in validate(self.p)))
    def test_regression_detects_geometry_camera_visibility_and_cut(self):
        baseline={'hidden_ball_world':[0.,1.,2.],'camera_lens':45.,'visible':True,'event':'E1'}
        for field,new in [('hidden_ball_world',[0.,1.3,2.]),('camera_lens',44.),('visible',False),('event','E2')]:
            changed=copy.deepcopy(baseline);changed[field]=new;self.assertEqual(compare(baseline,changed)['status'],'FAIL')
        self.assertEqual(compare(baseline,copy.deepcopy(baseline))['status'],'PASS')

if __name__=='__main__':unittest.main()
