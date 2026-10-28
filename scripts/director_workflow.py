"""Plan, schedule encoded-video review, and compute render scope. No Blender reset."""
import argparse,json
from pathlib import Path
from director_camera.workflow import validate_plan,review_schedule,invalidation
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('plan',type=Path);ap.add_argument('--changes',type=Path);ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args();plan=json.loads(args.plan.read_text(encoding='utf-8-sig'))
    result={'validation':validate_plan(plan),'review':review_schedule(plan)}
    if args.changes:result['render_scope']=invalidation(plan,json.loads(args.changes.read_text(encoding='utf-8-sig')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.resolve()==args.plan.resolve() or args.changes and args.output.resolve()==args.changes.resolve():raise ValueError('output must not overwrite input')
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result['validation'])
if __name__=='__main__':main()
