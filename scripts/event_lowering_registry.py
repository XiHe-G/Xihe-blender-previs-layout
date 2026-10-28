"""Fixed S52 safe subset. No runtime language-model or choreography selection."""
REGISTRY={
 'MOVE':{'family':'MOVEMENT','primitives':['MOVE_PROFILE'],'writes':['ROOT_LOCATION']},
 'ENTER':{'family':'MOVEMENT','primitives':['MOVE_PROFILE'],'writes':['ROOT_LOCATION']},
 'EXIT':{'family':'MOVEMENT','primitives':['MOVE_PROFILE'],'writes':['ROOT_LOCATION']},
 'LOOK':{'family':'ORIENTATION','primitives':['ORIENT_TO'],'writes':['HEAD_ROTATION']},
 'TURN':{'family':'ORIENTATION','primitives':['ORIENT_TO'],'writes':['ROOT_ROTATION']},
 'DODGE':{'family':'OFFSET','primitives':['MOVE_PROFILE','OFFSET_PATH'],'writes':['ROOT_LOCATION']},
 'RELEASE':{'family':'OWNERSHIP','primitives':['ATTACH_DETACH'],'writes':['PROJECTILE_TRANSFORM','ATTACHMENT_STATE']},
 'PROJECTILE_TRAVEL':{'family':'PROJECTILE','primitives':['MOVE_PROFILE'],'writes':['PROJECTILE_TRANSFORM']},
 'RECOVERY':{'family':'RECOVERY','primitives':['RECOVERY_PROFILE'],'writes':['ROOT_LOCATION']},
}
UNSUPPORTED={'TAKEOFF','LAND','ATTACK','BLOCK','CONTACT','NEAR_MISS','FOLLOW_THROUGH','VFX_TRIGGER','ATTENTION_HANDOFF'}
SPACING={'constant':'CONSTANT','accelerate_cruise_decelerate':'ACCEL_CRUISE_DECEL','ease_in':'EASE_IN','ease_out':'EASE_OUT','ease_in_out':'EASE_IN_OUT'}
AUTHOR_FIELDS={'destination','exit_point','entry_point','path','spacing','arrival_velocity','peak_speed','allow_speed_derivation','entry','target_direction','target_point','target_entity','body_level','max_turn_rate_deg_s','turn_mode','lead_delay_s','incoming_threat_direction','dodge_direction','offset_m','return_to_route','base_destination','release_time','release_direction','release_speed','owner_velocity_fraction','release_acceleration_duration','attachment_offset','stability','displacement_limit','retain_direction','orientation_strategy','head_lead_time','body_delay','root_delay','look_lag_time','catchup_window','angular_timing_profile','head_target_fraction'}

# An irrelevant semantic quantity is not silently discarded.
MOVEMENT_FIELDS={'destination','exit_point','entry_point','path','spacing','arrival_velocity','peak_speed','allow_speed_derivation','entry'}
FIELDS_BY_EVENT={k:MOVEMENT_FIELDS for k in ('MOVE','ENTER','EXIT','PROJECTILE_TRAVEL')}
FIELDS_BY_EVENT.update({k:{'target_direction','target_point','target_entity','body_level','max_turn_rate_deg_s','turn_mode','lead_delay_s','entry','orientation_strategy','head_lead_time','body_delay','root_delay','look_lag_time','catchup_window','angular_timing_profile','head_target_fraction'} for k in ('LOOK','TURN')})
FIELDS_BY_EVENT.update(DODGE={'incoming_threat_direction','dodge_direction','offset_m','return_to_route','base_destination','spacing','arrival_velocity','peak_speed','allow_speed_derivation','entry'},RELEASE={'release_time','release_direction','release_speed','owner_velocity_fraction','release_acceleration_duration','attachment_offset','entry'},RECOVERY={'stability','arrival_velocity','displacement_limit','retain_direction','entry'})
