"""Join the last disconnected 3V3_PI island using native DRC endpoints."""
import json,hashlib
import repair_controls as r
from repair_controls import p,ROOT,FILE

b=p.LoadBoard(str(FILE));d=json.loads((ROOT/'validation/native-current/controls-clean-drc.json').read_text())
g=r.Grid(b,.2);items={t.m_Uuid.AsString():t for t in b.GetTracks()};result=[]
for violation in d['unconnected_items']:
    a,c=violation['items'];aa=items[a['uuid']];cc=items[c['uuid']]
    qa=r.connected_endpoints(b,aa,(a['pos']['x'],a['pos']['y']));qc=r.connected_endpoints(b,cc,(c['pos']['x'],c['pos']['y']))
    path=g.route(qa,qc,aa.GetNetCode())
    if path:g.emit(path,aa.GetNetCode())
    result.append({'net':aa.GetNetname(),'routed':bool(path)})
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
(ROOT/'validation/controls-last-gap.json').write_text(json.dumps({'result':result,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(result),flush=True)
