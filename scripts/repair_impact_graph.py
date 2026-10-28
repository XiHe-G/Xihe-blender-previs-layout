"""Finite, auditable coupling table. Describes effects, never ranks candidates."""
from copy import deepcopy
from s2_common import digest

COUPLINGS={
 'LENS_CHANGE':dict(primary_effect=['SHOT_SIZE'],secondary_effects=['SCREEN_POSITION','VISIBILITY','CLIPPING','OCCLUSION','SCREEN_DIRECTION','CONTACT','NEAR_MISS','CAMERA_STATE'],protected_channels=['world_motion','pose','camera_transform','cut_timing','identity'],common_failure_modes=['Off-axis subject magnified outside frame','Other subjects cropped','Zoom violates Hold'],note='Changes field of view, not geometric depth ordering; apparent depth/framing may change'),
 'CAMERA_DOLLY':dict(primary_effect=['SHOT_SIZE'],secondary_effects=['SCREEN_POSITION','VISIBILITY','CLIPPING','OCCLUSION','SCREEN_DIRECTION','CONTACT','NEAR_MISS','CAMERA_STATE','PERSPECTIVE'],protected_channels=['world_motion','pose','lens','cut_timing','identity'],common_failure_modes=['Parallax / occlusion change','Near-plane clipping','Moving camera violates Hold']),
 'CAMERA_REFRAME':dict(primary_effect=['SCREEN_POSITION'],secondary_effects=['SHOT_SIZE','VISIBILITY','CLIPPING','OCCLUSION','SCREEN_DIRECTION','CONTACT','NEAR_MISS','CAMERA_STATE'],protected_channels=['world_motion','pose','lens','cut_timing','identity'],common_failure_modes=['Other subject leaves frame','Temporal pan violates Hold']),
 'RESTORE_CAMERA_ANCHOR':dict(primary_effect=['CAMERA_STATE'],secondary_effects=['SHOT_SIZE','SCREEN_POSITION','VISIBILITY','CLIPPING','OCCLUSION','SCREEN_DIRECTION','CONTACT','NEAR_MISS'],protected_channels=['world_motion','pose','lens','cut_timing','identity'],common_failure_modes=['Anchor incompatible with moved subjects']),
 'PROJECTILE_LOCAL_OFFSET':dict(primary_effect=['CONTACT','NEAR_MISS'],secondary_effects=['PROJECTILE_CONTINUITY','SCREEN_DIRECTION','VISIBILITY','OCCLUSION','MOTION_BOUNDARY'],protected_channels=['camera_transform','lens','character_world_motion','pose','cut_timing','identity','visibility_keys'],common_failure_modes=['Velocity / acceleration break at patch edges','New contact or teleport']),
 'RECOVERY_SPEED_SAMPLES':dict(primary_effect=['RECOVERY'],secondary_effects=['ACTION_PHASE','CONTACT','NEAR_MISS','SCREEN_POSITION','VISIBILITY','MOTION_BOUNDARY'],protected_channels=['camera_transform','lens','pose','weapon','projectile','cut_timing','identity'],common_failure_modes=['Abrupt stop or acceleration at entry','Recovery endpoint drift']),
}

def impact_graph(proposal,expected,strategy_id):
    strategy=next((s for s in proposal['candidate_strategies'] if s['strategy_id']==strategy_id),None)
    if not strategy:raise ValueError('CANDIDATE_NOT_IN_PROPOSAL')
    atoms=['CAMERA_DOLLY','LENS_CHANGE'] if strategy_id=='CAMERA_LENS_COMBINED' else [strategy_id]
    if any(a not in COUPLINGS for a in atoms):raise ValueError('COUPLING_NOT_IMPLEMENTED')
    effects={v for a in atoms for key in ['primary_effect','secondary_effects'] for v in COUPLINGS[a][key]}
    shot=proposal['source_checker_result']['result']['shot_id'];target=proposal['source_checker_result']['observable_id']
    affected=[o['observable_id'] for o in expected['observables'] if o['type'] in effects and (o['shot_id'] in (shot,None))]
    modified={s['channel'] for s in strategy['modify']}
    protected=sorted({c for a in atoms for c in COUPLINGS[a]['protected_channels']}-modified)
    return dict(schema_version='REPAIR-IMPACT-GRAPH/1.0',preview_only=True,proposal_id=proposal['proposal_id'],strategy_id=strategy_id,target_observable=target,directly_modified_channels=deepcopy(strategy['modify']),potentially_affected_observables=affected,protected_observables=[o['observable_id'] for o in expected['observables'] if o['observable_id']!=target],effective_protected_channels=protected,known_couplings={a:deepcopy(COUPLINGS[a]) for a in atoms},preserve=deepcopy(strategy['preserve']),table_sha256=digest(COUPLINGS),selection=None)
