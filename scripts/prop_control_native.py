"""Native control registration. Metadata only; no geometry/transform writes."""
import json
KEY='previs_prop_control_index'
TABLE='previs_prop_control_registry'

def apply_control(obj,state,frame):
    value={k:v for k,v in state.items() if k!='contract'}
    registry=json.loads(obj.get(TABLE,'[]'))
    if value not in registry:registry.append(value);obj[TABLE]=json.dumps(registry,sort_keys=True,separators=(',',':'))
    obj[KEY]=registry.index(value)
    if frame is not None:obj.keyframe_insert(data_path='["'+KEY+'"]',frame=frame)

def native_control(obj):
    if KEY not in obj:return None
    registry=json.loads(obj[TABLE]);index=float(obj[KEY])
    if abs(index-round(index))>1e-7 or not 0<=round(index)<len(registry):raise ValueError('INVALID_NATIVE_CONTROL_INDEX')
    return registry[round(index)]
