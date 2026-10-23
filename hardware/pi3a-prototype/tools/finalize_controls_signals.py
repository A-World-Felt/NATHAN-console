"""Resolve actual DRC conflicts; preserve 0.20 mm clearance requirement."""
import json,math,hashlib
import repair_controls as r
from repair_controls import p,ROOT,FILE,pos,cell,v,segment
def main():
    b=p.LoadBoard(str(FILE));drc=json.loads((ROOT/'validation/native-current/controls-fanout-drc.json').read_text())
    for t in list(b.GetTracks()):
        x,y=pos(t)
        if t.GetNetname() in ['SHOULDER_L1','FACE_R_RIGHT'] or t.GetNetname()=='3V3_PI' and 129.5<x<130.5 and 82.5<y<84.5:b.Delete(t)
    f=next(f for f in b.GetFootprints() if f.GetReference()=='R35');f.SetPosition(v(130,82.5));pad=next(x for x in f.Pads() if x.GetNumber()=='2');n=pad.GetNetCode()
    segment(b,pos(pad),(130,80.8),n,0,.2);via=p.PCB_VIA(b);via.SetPosition(v(130,80.8));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH);via.SetNetCode(n);b.Add(via)
    r.MARGIN=.025;g=r.Grid(b,.2);failed=[]
    for name in ['H2_SCL','H2_SDA','SHOULDER_L1','FACE_R_RIGHT']:
        pads=[pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetname()==name];n=pads[0].GetNetCode();connected=[pads[0]];remaining=pads[1:]
        while remaining:
            _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in connected for c in remaining),key=lambda t:t[0]);qa=r.connected_endpoints(b,a);qc=r.connected_endpoints(b,c)
            if set(qa)&set(qc):path=[next(iter(set(qa)&set(qc)))]
            else:path=g.route(qa,qc,n)
            if path and len(path)>1:g.emit(path,n)
            elif path is None:failed.append({'net':name,'from':pos(a),'to':pos(c)})
            connected.append(c);remaining.remove(c)
        p.SaveBoard(str(FILE),b);print(name+' failed='+str(len(failed)),flush=True)
    byid={x.m_Uuid.AsString():x for f in b.GetFootprints() for x in f.Pads()};byid.update({x.m_Uuid.AsString():x for x in b.GetTracks()})
    for issue in drc['unconnected_items']:
        if '[3V3_PI]' not in issue['items'][0]['description']:continue
        ia,ic=issue['items'];a,c=byid.get(ia['uuid']),byid.get(ic['uuid'])
        if a is None or c is None:continue
        pa=(ia['pos']['x'],ia['pos']['y']);pc=(ic['pos']['x'],ic['pos']['y']);n=a.GetNetCode();qa=r.connected_endpoints(b,a,pa);qc=r.connected_endpoints(b,c,pc);path=g.route(qa,qc,n)
        if path:g.emit(path,n)
        else:failed.append({'net':'3V3_PI','from':pa,'to':pc})
        print('PI_PLANE_GAP',bool(path),flush=True)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    (ROOT/'validation/controls-final-signals-d1.json').write_text(json.dumps({'failures':failed,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'status':'Native DRC required'},indent=2)+'\n')
if __name__=='__main__':main()
