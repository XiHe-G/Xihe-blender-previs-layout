"""Decode every encoded frame; flags are review requests, never artistic acceptance."""
import subprocess,hashlib
import numpy as np
def review(video,ffmpeg,shots,native,expected_frames,expected_source_sha256,allowed_exits=()):
 if native.get('blend_sha256')!=expected_source_sha256 or len(shots)!=len(native['shots']):raise ValueError('NATIVE_SOURCE_OR_SHOT_COUNT_MISMATCH')
 raw=subprocess.run([ffmpeg,'-v','error','-i',str(video),'-vf','scale=160:90','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
 unit=160*90*3
 if len(raw)%unit:raise ValueError('TRUNCATED_DECODE')
 images=np.frombuffer(raw,np.uint8).reshape((-1,90,160,3))
 if len(images)!=expected_frames:raise ValueError('DECODE_COUNT_MISMATCH')
 reports=[]
 for sh,n in zip(shots,native['shots']):
  if sh['id']!=n['shot']:raise ValueError('SHOT_BINDING_MISMATCH')
  clip=images[sh['start']-1:sh['end']];luma=clip.mean(axis=(1,2,3));change=np.abs(np.diff(clip.astype(np.float32),axis=0)).mean(axis=(1,2,3))
  issues=[];occluded={};edge={}
  for row in n['rows']:
   for actor,a in row['subjects'].items():
    head=a['head_uv'];inside=head[2]>0 and 0<=head[0]<=1 and 0<=head[1]<=1
    if inside and a['head_ray_external_occluder']:occluded.setdefault(actor,[]).append(row['frame'])
    if not inside:edge.setdefault(actor,[]).append(row['frame'])
  if luma.max()<3:issues.append({'code':'DECODED_BLACK','frames':[sh['start'],sh['end']]})
  if sh['id'] not in allowed_exits:
   for a,fs in occluded.items():
    if len(fs)>=3:issues.append({'code':'HEAD_RAY_OCCLUSION_REVIEW','actor':a,'frames':fs,'automatic_failure':False})
  reports.append(dict(shot=sh['id'],all_frames_decoded=len(clip),mean_luma=float(luma.mean()),mean_interframe_change=float(change.mean()) if len(change) else 0,head_outside_samples=edge,head_occlusion_samples=occluded,issues=issues,technical='MEASURED',visual_readability='REVIEW_REQUIRED',director_expression='NOT_REVIEWED',seedance_effect='NOT_TESTED'))
 return {'video_sha256':hashlib.sha256(open(video,'rb').read()).hexdigest(),'decoded_frames':len(images),'shots':reports,'status':'REVIEW_REQUIRED','max_iterations':4,'no_artistic_score':True}
