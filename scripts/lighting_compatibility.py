"""Read-only compatibility comparison, not lighting design or mutation permission."""
import copy

def evaluate(before,after,context=None):
    ctx=context or {};result={'capability':'LIGHTING_COMPATIBILITY_GUARD','automatic_mutation':False,'new_confirmation_gate':False,'source':'NATIVE_SAMPLED_STATE','issues':[],'affected':[]}
    if before is None or after is None or 'lights_present' not in before or 'lights_present' not in after:
        result.update(status='NOT_REVIEWED',reason='MISSING_NATIVE_EVIDENCE');return result
    if not before.get('lights_present') and not after.get('lights_present') and not ctx.get('lighting_required'):
        result.update(status='NOT_APPLICABLE',reason='NO_LIGHTING_PREVIS_REQUIRED_OR_PRESENT');return result
    if not before.get('frames') or not after.get('frames') or before.get('frames')!=after.get('frames'):
        result.update(status='NOT_REVIEWED',reason='MISSING_OR_MISMATCHED_GLOBAL_FRAMES');return result
    if not before.get('lights_present') or not after.get('lights_present'):
        result.update(status='NOT_REVIEWED',reason='LIGHTING_REQUEST_OR_LIGHT_SET_UNRESOLVED');return result
    for field in ('lights','color_management','world','materials','camera','geometry','motion'):
        if field not in before or field not in after:
            result['issues'].append('MISSING_'+field.upper());continue
        if any(str(f) not in before[field] or str(f) not in after[field] for f in before['frames']):
            result['issues'].append('MISSING_'+field.upper()+'_SAMPLES');continue
        changes=[f for f in before['frames'] if before[field].get(str(f))!=after[field].get(str(f))]
        if changes:
            result['affected'].append({'field':field,'time_window_frames':[min(changes),max(changes)],'frames':changes,'subjects':ctx.get('subjects',[]),'lights':ctx.get('lights',[]),'regions':ctx.get('regions',[])})
    if result['issues']:
        result.update(status='NOT_REVIEWED',reason='INCOMPLETE_EVIDENCE');return result
    motion=any(x['field'] in ('motion','geometry') for x in result['affected'])
    locked=any(x['field'] in ('lights','color_management','world','materials','camera') for x in result['affected'])
    if locked:result['issues'].append('PROTECTED_LIGHTING_OR_CAMERA_CHANGED')
    # Dynamic cue/facing/occlusion equality must be measured, not inferred from a new timestamp.
    if motion:result['issues'].append('DYNAMIC_LIGHTING_TIMING_OR_SPATIAL_RELATION_CHANGED')
    result['status']='LIGHTING_REVIEW_INVALIDATED' if result['affected'] else 'PASS'
    result['plan_status']='NOT_REVIEWED' if not ctx.get('plan_approval_ref') else 'REVIEW_REQUIRED' if locked or ctx.get('intent_violation_evidence') else 'VALID_SCOPE_UNCHANGED'
    result['test_approval_status']='REVIEW_REQUIRED' if result['affected'] else 'UNCHANGED_NO_NEW_APPROVAL'
    result['approval_source']=ctx.get('plan_approval_ref')
    result['scope']='State compatibility only; no lighting design, perceptual quality or universal implementation claim'
    return result
