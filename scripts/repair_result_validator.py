"""Recheck decides repair success, never compilation success."""
from s2_common import digest
RESULTS={'FIXED','PARTIALLY_FIXED','NOT_FIXED','REGRESSION_INTRODUCED','ABORTED'}

def validate_result(before,after,target_ids,unchanged,override_ok=True,aborted=False):
    if aborted:return dict(status='ABORTED',reason='Repair not executed/approved or execution aborted')
    if before['graph_sha256']!=after['graph_sha256']:raise ValueError('REPAIR_PLAN_CHANGED')
    aa={x['observable_id']:x for x in after['results']};bb={x['observable_id']:x for x in before['results']}
    regressions=[];diff=[];warning_review=[]
    for id,old in bb.items():
        new=aa.get(id)
        if new is None:regressions.append(dict(observable_id=id,reason='CHECK_DISAPPEARED'));continue
        if digest(old['plan'])!=digest(new['plan']):raise ValueError('REPAIR_REQUIREMENT_CHANGED: '+id)
        reason=None
        if old['status']=='PASS' and new['status']!='PASS':reason='PREVIOUS_PASS_LOST'
        elif old['status']!='FAIL' and new['status']=='FAIL':reason='NEW_FAIL'
        elif old['status']=='WARNING' and new['status']=='NOT_REVIEWED':reason='WARNING_EVIDENCE_LOST'
        elif old['status']=='WARNING' and new['status']=='WARNING':
            severity={'INFO':0,'MINOR':1,'MAJOR':2,'CRITICAL':3}
            if severity.get(new.get('severity'),0)>severity.get(old.get('severity'),0) or old.get('measurement_status')=='PASS' and new.get('measurement_status')=='FAIL':reason='WARNING_WORSENED'
            elif digest(old.get('actual'))!=digest(new.get('actual')):warning_review.append(id)
        if reason:regressions.append(dict(observable_id=id,reason=reason,shot_id=old['shot_id'],before=old['status'],after=new['status']))
        diff.append(dict(observable_id=id,shot_id=old['shot_id'],type=old['type'],before=old['status'],after=new['status'],before_actual=old['actual'],after_actual=new['actual']))
    if unchanged['status']!='PASS':regressions.append(dict(reason='UNCHANGED_REGION_REGRESSION'))
    if not override_ok:regressions.append(dict(reason='OVERRIDE_REGRESSION'))
    fixed=[id for id in target_ids if id in aa and aa[id]['status']=='PASS' and aa[id].get('evidence_sufficiency',{}).get('level')=='ENOUGH']
    improved=[id for id in target_ids if id in aa and aa[id]['status']=='WARNING']
    status='REGRESSION_INTRODUCED' if regressions else 'FIXED' if len(fixed)==len(target_ids) and target_ids and not warning_review else 'PARTIALLY_FIXED' if fixed or improved else 'NOT_FIXED'
    return dict(status=status,target_results={id:aa.get(id,{}).get('status','MISSING') for id in target_ids},regressions=regressions,warning_measurements_requiring_review=warning_review,diff=diff,unchanged_region=unchanged,overrides_preserved=override_ok,automatic_retry=False)

if __name__=='__main__':
    import argparse
    from s2_common import read,write
    ap=argparse.ArgumentParser()
    for field in ['before','after','unchanged','output']:ap.add_argument('--'+field,required=True)
    ap.add_argument('--target',action='append',required=True);a=ap.parse_args();result=validate_result(read(a.before),read(a.after),a.target,read(a.unchanged));write(a.output,result);print(result['status'])
