"""Open the last DRV SDA escape while retaining native clearance checks."""
import json,math,hashlib
import repair_controls as r
from repair_controls import p,ROOT,FILE,pos,v,segment
def main():
    b=p.LoadBoard(str(FILE));names=['CTRL_RESET_N','CENTRAL_2'];remove={'0a166484-0fca-4d7f-96b2-36ece1d7656b','79166290-3c9a-471c-a29c-4740ae2af743'}
    for t in list(b.GetTracks()):
        if t.GetNetname() in names or t.m_Uuid.AsString() in remove:b.Delete(t)
    f=next(f for f in b.GetFootprints() if f.GetReference()=='U2');pads={p.GetNumber():p for p in f.Pads()}
    for pin,x,y in [('4',107.4,107.5),('3',103.2,107.4)]:
        pad=pads[pin];n=pad.GetNetCode();segment(b,pos(pad),(x,y),n,0,.2)
        via=p.PCB_VIA(b);via.SetPosition(v(x,y));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(n);b.Add(via)
    # Reset mux fanout is recreated because that net was ripped up.
    f=next(f for f in b.GetFootprints() if f.GetReference()=='U8');pad=next(p for p in f.Pads() if p.GetNumber()=='3');n=pad.GetNetCode();x,y=115.4,pos(pad)[1];segment(b,pos(pad),(x,y),n,0,.2)
    via=p.PCB_VIA(b);via.SetPosition(v(x,y));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(n);b.Add(via)
    r.MARGIN=.025;g=r.Grid(b,.2);fail=[]
    for name in ['H2_SDA']+names:
        pads=[pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetname()==name];n=pads[0].GetNetCode();remaining=pads[1:];done=[pads[0]]
        while remaining:
            _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in done for c in remaining),key=lambda t:t[0]);qa=r.connected_endpoints(b,a);qc=r.connected_endpoints(b,c)
            if set(qa)&set(qc):path=[next(iter(set(qa)&set(qc)))]
            else:path=g.route(qa,qc,n)
            if path and len(path)>1:g.emit(path,n)
            elif path is None:fail.append({'net':name,'from':pos(a),'to':pos(c)})
            done.append(c);remaining.remove(c)
        print(name+' failures='+str(len(fail)),flush=True);p.SaveBoard(str(FILE),b)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    (ROOT/'validation/controls-haptic-escape-d1.json').write_text(json.dumps({'failures':fail,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()},indent=2)+'\n')
if __name__=='__main__':main()
