"""Read-only, bounded repair suggestions. Never chooses or executes a strategy."""
import argparse,copy
from s2_common import digest,read,write,schema_check,selector_paths,projection

SUPPORTED={'SHOT_SIZE','SCREEN_POSITION','CAMERA_STATE','CONTACT','NEAR_MISS','RECOVERY'}
CODES={'SHOT_SIZE':'SHOT_SIZE_MISMATCH','SCREEN_POSITION':'SCREEN_POSITION_MISMATCH','CAMERA_STATE':'CAMERA_STATE_MISMATCH','CONTACT':'CONTACT_MISMATCH','NEAR_MISS':'NEAR_MISS_MISMATCH','RECOVERY':'RECOVERY_MISSING'}

def generate(report,result_id,graph,csp,binding,registry,context):
    r=next(x for x in report['results'] if x['observable_id']==result_id)
    if report['graph_sha256']!=digest(graph):raise ValueError('STALE_CHECKER_GRAPH')
    if binding['graph_sha256']!=digest(graph) or binding['csp_sha256']!=digest(csp):raise ValueError('STALE_REPAIR_BINDING')
    if r['status']!='FAIL' or r.get('evidence_sufficiency',{}).get('level')!='ENOUGH':return None
    if r['type'] not in SUPPORTED or r['plan'].get('requirement_source')=='INFERRED' or r['plan'].get('confidence')=='LOW':return None
    if r['code']!=CODES[r['type']]:return None
    if not r['evidence']:return None
    typ=r['type'];specs=[]
    def add(id,label,key,risk,boundary):
        if context.get(key):specs.append(dict(strategy_id=id,label=label,modify=copy.deepcopy(context[key]),preserve=copy.deepcopy(context['preserve']),side_effect_risk=risk,implementation_boundary=boundary))
    if typ=='SHOT_SIZE':
        add('CAMERA_DOLLY','静态Camera距离修正','camera_transform','可能改变屏幕位置、遮挡与Near Miss投影关系','LOCKED_HOLD内使用一个静态Anchor；不增加持续运镜')
        add('LENS_CHANGE','静态Lens修正','lens','会同时放大主体偏离画心的距离及其他对象','仅改变该镜既有Lens采样；不得修改主体Scale或世界路线')
        add('CAMERA_LENS_COMBINED','Camera与Lens共同静态修正','camera_and_lens','可能影响背景透视及危险关系','仅静态Camera/Lens，不做候选搜索或自动选优')
    elif typ=='SCREEN_POSITION':
        add('CAMERA_REFRAME','优先Camera静态重构图','camera_transform','可能影响景别与其他主体的屏幕位置','保持角色Root和Projectile轨迹；只修改目标Shot Camera')
        add('CAMERA_LATERAL_OFFSET','Camera静态横向偏移','camera_transform','可能改变视差、遮挡与Near Miss','不改变角色世界位置')
        if not context.get('world_position_locked',True):add('LIMITED_ROOT_CORRECTION','备选有限Root修正','root','会影响接触距离/路线，优先级低于Camera','仅已有局部采样；必须另获明确通道授权')
    elif typ=='CAMERA_STATE':
        mode=r['plan'].get('behavior_profile')
        add('RESTORE_CAMERA_ANCHOR','恢复批准Camera Anchor','camera_transform','Anchor可能不满足其他主体构图，需要复查','对LOCKED_HOLD压平既有错误Camera采样；不新增动作')
        if mode=='SOFT_HOLD':add('COMPRESS_CAMERA_MOTION','压缩已有Camera运动幅度','camera_transform','可能失去必要跟随','仅既有采样，不重新导演')
    elif typ in ('CONTACT','NEAR_MISS'):
        add('PROJECTILE_LOCAL_OFFSET' if typ=='NEAR_MISS' else 'ATTACK_ENDPOINT_ADJUSTMENT','局部攻击端/Projectile终段修正','attack','局部轨迹可能出现速度突变或新Contact','保持身份、攻击方向、Cut、事件顺序；不得隐藏或删除Projectile')
        add('RECEIVER_ENDPOINT_ADJUSTMENT','接收方局部终点修正','receiver','可能改变接收者路线或构图','仅明确窗口内既有采样，不重写整场动作')
    elif typ=='RECOVERY':
        add('RECOVERY_SPEED_SAMPLES','调整既有恢复区间Root速度采样','root','可能改变恢复终点/接续速度','只修改现有执行采样，不发明动作、不变更事件窗口')
        add('RECOVERY_POSTURE_SAMPLES','调整已有姿态回稳采样','pose','不能代替必要位移减速','仅已有姿态通道；不增加Rig')
    if not specs:return None
    protected=[];blocked=set()
    for strategy in specs:
        paths=set(projection(csp,strategy['modify']))
        for lock in registry['overrides']:
            if lock['status']=='LOCKED' and paths & set(projection(csp,lock['protections'])):
                protected.append(dict(override_id=lock['override_id'],strategy_id=strategy['strategy_id'],target=lock['target'],channel=lock['channel'],status='BLOCKED_BY_OVERRIDE'));blocked.add(strategy['strategy_id'])
    p=dict(schema_version='REPAIR-PROPOSAL/1.0',proposal_id=context['proposal_id'],status='BLOCKED_BY_OVERRIDE' if len(blocked)==len(specs) else 'PENDING_HUMAN_APPROVAL',
      source_checker_result=dict(report_sha256=digest(report),result_sha256=digest(r),observable_id=result_id,result=copy.deepcopy(r)),source_author_id=r['source_author_id'],problem_type=typ,severity=r['severity'],evidence=copy.deepcopy(r['evidence']),affected_subjects=r['subjects'],time_range=r['time_window'],
      likely_channels=sorted({s['channel'] for st in specs for s in st['modify']}),repair_goal=dict(rule='Make Actual satisfy unchanged Plan',expected_range=r['plan'].get('expected_range'),expected_state=r['plan'].get('expected_state'),behavior_profile=r['plan'].get('behavior_profile')),candidate_strategies=specs,
      estimated_affected_scope=dict(target=context['lowering_target']['target'],selectors=[s for st in specs for s in st['modify']],basis='Direct estimate only; S2 explicit dependency closure is authoritative'),protected_overrides=protected,risk='No guarantee of success. Any new failure or lost prior PASS blocks FIXED; no automatic retry.',confidence=r['plan'].get('confidence','MEDIUM'),requires_human_approval=True,lowering_target=context['lowering_target'],
      graph_sha256=digest(graph),csp_sha256=digest(csp),execution_binding_sha256=digest(binding),override_registry_sha256=digest(registry))
    schema_check(p,'repair-proposal.schema.json');return p

def review_html(report,proposals,out,decisions=()):
    from plan_actual_checker import deliver
    from pathlib import Path
    import html,json
    deliver(report,out);path=Path(out)/'PLAN-ACTUAL-REPORT.html';page=path.read_text(encoding='utf-8')
    cards=[];dd={d['proposal_id']:d for d in decisions}
    for p in proposals:
        payload=dict(Problem=p['problem_type'],Evidence=p['evidence'],Candidate_Strategies=p['candidate_strategies'],Affected_Scope_Estimate=p['estimated_affected_scope'],Risk=p['risk'],Protected_Overrides=p['protected_overrides'],Decision_Status=dd.get(p['proposal_id'],{}).get('decision',p['status']))
        attrs=html.escape('REPAIR '+p['proposal_id']+' '+p['problem_type']+' '+p['source_author_id']+' '+payload['Decision_Status'])
        cards.append('<article data-filter="'+attrs+'"><h3>'+html.escape(p['proposal_id'])+'</h3><pre>'+html.escape(json.dumps(payload,ensure_ascii=False,indent=2))+'</pre></article>')
    page=page.replace('</body>','') # S3 document uses implicit body.
    page=page.replace('</html>','<section><h2>Repair Proposals · Human approval required</h2>'+''.join(cards)+'</section></html>');path.write_text(page,encoding='utf-8')

if __name__=='__main__':
    from combat_sequence_package import read_package
    ap=argparse.ArgumentParser()
    for field in ['report','result-id','graph','csp','binding','registry','context','output']:ap.add_argument('--'+field,required=True)
    a=ap.parse_args();p=generate(read(a.report),a.result_id,read(a.graph),read_package(a.csp),read(a.binding),read(a.registry),read(a.context));write(a.output,p if p else dict(status='DIAGNOSTIC_ONLY',requires_human_approval=True));print('PROPOSAL_READY' if p else 'DIAGNOSTIC_ONLY')
