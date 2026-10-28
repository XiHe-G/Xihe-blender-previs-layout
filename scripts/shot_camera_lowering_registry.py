"""Explicit behavior -> camera kernel; plain historical HOLD has no default profile."""
REGISTRY={'HOLD':'CAM_HOLD','REFRAME':'CAM_REFRAME','FOLLOW':'CAM_FOLLOW','LEAD_LAG':'CAM_LEAD_LAG','PUSH_PULL':'CAM_PUSH_PULL','CATCH_UP':'CAM_CATCH_UP'}
AUTHOR_FIELDS={'behavior','profile','subject','screen_anchor','target_screen_region','distance','height_offset','tracking_strength','lag_seconds','lead_distance','screen_bias','transition_seconds','direction','travel_distance','spacing','lens_change','entry_lag_seconds','catchup_fraction','settle_fraction','max_rotation_degrees','max_translation','start','end','previous_shot'}

COMMON={'behavior','subject','height_offset','start','end'}
FIELDS_BY_BEHAVIOR={
'HOLD':COMMON|{'profile','tracking_strength'},
'REFRAME':COMMON|{'target_screen_region','max_rotation_degrees','max_translation'},
'FOLLOW':COMMON|{'screen_anchor','distance','tracking_strength','lag_seconds'},
'LEAD_LAG':COMMON|{'lead_distance','lag_seconds','screen_bias','transition_seconds'},
'PUSH_PULL':COMMON|{'direction','travel_distance','lens_change'},
'CATCH_UP':COMMON|{'entry_lag_seconds','tracking_strength','catchup_fraction','settle_fraction'},
}
