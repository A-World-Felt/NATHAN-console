"""Remove only vias explicitly reported dangling by the last native DRC."""
import json,hashlib
import pcbnew as p
from repair_controls import ROOT,FILE
b=p.LoadBoard(str(FILE));d=json.loads((ROOT/'validation/native-current/controls-closed-drc.json').read_text())
ids={i['uuid'] for v in d['violations'] if v['type']=='via_dangling' for i in v['items']}
removed=[]
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in ids:
        if not isinstance(t,p.PCB_VIA):raise ValueError('Reported object is not a via')
        removed.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname()});b.Delete(t)
if len(removed)!=len(ids):raise ValueError('Stale DRC UUIDs')
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
(ROOT/'validation/controls-unused-vias-removed.json').write_text(json.dumps({'removed':removed,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'status':'Must run fresh native DRC after removal'},indent=2)+'\n')
print(json.dumps(removed),flush=True)
