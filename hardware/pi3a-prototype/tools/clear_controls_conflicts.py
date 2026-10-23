import json,math,hashlib
import repair_controls as r
from repair_controls import p,ROOT,FILE,pos,segment
def main():
    b=p.LoadBoard(str(FILE));d=json.loads((ROOT/'validation/native-current/controls-complete-drc.json').read_text())
    for t in list(b.GetTracks()):
        if t.GetNetname()=='FACE_L_LEFT' or t.m_Uuid.AsString()=='4f674ede-e778-4281-8b20-ca029c7f2681':b.Delete(t)
    pad=next(x for f in b.GetFootprints() if f.GetReference()=='U2' for x in f.Pads() if x.GetNumber()=='3');n=pad.GetNetCode()
    segment(b,pos(pad),(103.5,107),n,0,.2);segment(b,(103.5,107),(103.2,107.4),n,0,.2)
    r.MARGIN=.025;g=r.Grid(b,.2);pads=[x for f in b.GetFootprints() for x in f.Pads() if x.GetNetname()=='FACE_L_LEFT'];n=pads[0].GetNetCode();done=[pads[0]];todo=pads[1:];failed=[]
    while todo:
        _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in done for c in todo),key=lambda t:t[0]);qa=r.connected_endpoints(b,a);qc=r.connected_endpoints(b,c);path=g.route(qa,qc,n)
        if path:g.emit(path,n)
        else:failed.append([pos(a),pos(c)])
        done.append(c);todo.remove(c)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    (ROOT/'validation/controls-clearance-repair-d1.json').write_text(json.dumps({'failed':failed,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()},indent=2)+'\n');print(json.dumps({'failed':failed}),flush=True)
if __name__=='__main__':main()
