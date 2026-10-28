"""Extract requested director evidence from the actual encoded video.

Requires existing plan and optional native trace receipt. Extraction is not a
visual/director PASS and never infers emotion from brightness or motion amount.
"""
import argparse,json,subprocess
from pathlib import Path
from director_camera.workflow import review_schedule,file_sha
def extract(plan,video,out,ffmpeg='ffmpeg',native=None):
    schedule=review_schedule(plan);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    frames=set(f for s in schedule['shots'] for f in s['frames'])
    frames.update(f for pair in schedule['cut_pairs'] for f in pair);frames=sorted(frames)
    expr='+'.join('eq(n\\,%d)'%(f-plan['start']) for f in frames)
    subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(video),'-vf','select='+expr,'-fps_mode','vfr',str(out/'frame_%05d.png')],check=True)
    produced=sorted(out.glob('frame_*.png'))
    if len(produced)!=len(frames):raise ValueError('encoded video lacks requested evidence frames')
    receipt=dict(video_sha256=file_sha(video),requested=schedule,frames=[dict(source_frame=f,path=p.name,sha256=file_sha(p)) for f,p in zip(frames,produced)],visual='NOT_REVIEWED',director='NOT_REVIEWED',playback='NOT_REVIEWED')
    if native is not None:
        receipt['native_receipt_sha256']=file_sha(native)
        receipt['binding']='Explicit paired receipt; hash alone does not prove video was rendered from this scene'
    (out/'EVIDENCE.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return receipt
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('plan',type=Path);ap.add_argument('video',type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--native',type=Path)
    a=ap.parse_args();extract(json.loads(a.plan.read_text(encoding='utf-8-sig')),a.video,a.output,a.ffmpeg,a.native)
if __name__=='__main__':main()
