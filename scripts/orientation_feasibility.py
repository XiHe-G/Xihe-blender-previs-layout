"""Preflight-only orientation budget; does not write execution data."""
import math
from primitive_sampler import qangle,qnorm

def shortest_angle(current,target): return qangle(qnorm(current),qnorm(target))
def orientation_budget(current_orientation,target_orientation,available_duration,max_angular_speed,max_angular_acceleration=None,entry_angular_velocity=0.,exit_angular_velocity=0.):
    if available_duration<=0 or max_angular_speed<=0:return {'status':'NEEDS_AUTHOR_INPUT','failure_code':'INVALID_ORIENTATION_BUDGET'}
    delta=shortest_angle(current_orientation,target_orientation);required=delta/available_duration
    # quintic ease peak velocity is 1.875 * delta / T; this is the same profile used by ORIENT_TO.
    eased_peak=1.875*delta/available_duration
    if eased_peak<=math.radians(max_angular_speed)+1e-9 and (max_angular_acceleration is None or 5.7735*delta/(available_duration**2)<=max_angular_acceleration+1e-9):
        return {'status':'FEASIBLE','angular_delta_rad':delta,'angular_delta_deg':math.degrees(delta),'available_duration':available_duration,'required_average_angular_speed':required,'required_peak_angular_speed':eased_peak,'allowed_angular_speed':math.radians(max_angular_speed),'entry_angular_velocity':entry_angular_velocity,'exit_angular_velocity':exit_angular_velocity,'profile':'EASE_IN_OUT_ROTATION','source':'DIRECTOR_PREFLIGHT/1.0'}
    return {'status':'INFEASIBLE_DURATION','angular_delta_rad':delta,'angular_delta_deg':math.degrees(delta),'available_duration':available_duration,'required_average_angular_speed':required,'required_peak_angular_speed':eased_peak,'allowed_angular_speed':math.radians(max_angular_speed),'entry_angular_velocity':entry_angular_velocity,'exit_angular_velocity':exit_angular_velocity,'failure_code':'ANGULAR_SPEED_OR_ACCELERATION_LIMIT','source':'DIRECTOR_PREFLIGHT/1.0'}

def channel_plan(strategy,head_lead_time=0.,body_delay=0.,root_delay=0.):
    if strategy not in ('HEAD_ONLY','HEAD_LEAD_BODY_FOLLOW','BODY_ROOT_TURN'):raise ValueError('UNKNOWN_ORIENTATION_STRATEGY')
    return {'schema_version':'ORIENTATION-CHANNEL-PLAN/1.0','strategy':strategy,'phases':{'HEAD':{'lead_time':head_lead_time,'delay':0.},'BODY':{'delay':body_delay},'ROOT':{'delay':root_delay}},'primitive':'ORIENT_TO','source':'DIRECTOR_PREFLIGHT/1.0'}
